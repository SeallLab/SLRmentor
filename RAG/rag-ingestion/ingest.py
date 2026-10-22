import hashlib
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from pypdf import PdfReader
from pymongo import MongoClient, ReplaceOne


# ============================================================
# Configuration
# ============================================================

# Chunking is word-based so we do not need to load any
# tokenizer or embedding model in the backend.
MAX_CHUNK_WORDS = 200
OVERLAP_WORDS = 20

load_dotenv()

MONGODB_URI = os.environ["MONGO_URI"]

MONGODB_DATABASE = os.environ.get(
    "MONGO_DB_NAME",
    "rag_db_test",
)

MONGODB_COLLECTION = os.environ.get(
    "MONGO_DB_RAG_COLLECTION_NAME",
    "test_paper_chunks",
)


# ============================================================
# Helpers
# ============================================================

def generate_paper_id(pdf_path: Path) -> str:
    """
    Generate a stable SHA-256 ID from the PDF contents.

    If the exact same PDF is ingested again,
    it receives the same paper_id.
    """

    sha256 = hashlib.sha256()

    with pdf_path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            sha256.update(chunk)

    return sha256.hexdigest()


def clean_text(text: str) -> str:
    """
    Clean common PDF extraction artifacts without heavily
    modifying the source text.
    """

    # Remove null bytes.
    text = text.replace("\x00", "")

    # Join words broken across lines:
    #
    #   transfor-
    #   mation
    #
    # becomes:
    #
    #   transformation
    text = re.sub(
        r"(?<=\w)-\s*\n\s*(?=\w)",
        "",
        text,
    )

    # Normalize line breaks inside paragraphs.
    text = re.sub(
        r"(?<!\n)\n(?!\n)",
        " ",
        text,
    )

    # Collapse repeated spaces/tabs.
    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    # Normalize paragraph spacing.
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


def extract_pages(pdf_path: Path) -> list[dict]:
    """
    Extract text from each PDF page independently so page
    metadata can be retained in MongoDB.
    """

    reader = PdfReader(pdf_path)

    pages = []

    for page_number, page in enumerate(
        reader.pages,
        start=1,
    ):
        raw_text = page.extract_text()

        if not raw_text:
            continue

        text = clean_text(raw_text)

        if not text:
            continue

        pages.append(
            {
                "page": page_number,
                "text": text,
            }
        )

    return pages


# ============================================================
# Chunking
# ============================================================

def split_into_sentences(text: str) -> list[str]:
    """
    Basic sentence-aware splitter.

    Keeping sentence boundaries generally produces more useful
    RAG chunks than blindly splitting every N words.
    """

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text,
    )

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def word_count(text: str) -> int:
    """
    Approximate chunk size without requiring a tokenizer.

    Atlas/Voyage performs its own tokenization when generating
    the actual embeddings.
    """

    return len(text.split())


def split_long_sentence(
    sentence: str,
) -> list[str]:
    """
    Split an unusually long sentence into smaller pieces.
    """

    words = sentence.split()

    pieces = []

    start = 0

    while start < len(words):

        end = min(
            start + MAX_CHUNK_WORDS,
            len(words),
        )

        piece = " ".join(
            words[start:end]
        ).strip()

        if piece:
            pieces.append(piece)

        if end >= len(words):
            break

        start = end - OVERLAP_WORDS

    return pieces


def get_overlap_sentences(
    sentences: list[str],
) -> list[str]:
    """
    Preserve approximately OVERLAP_WORDS words from the end
    of the previous chunk.

    This provides some context between adjacent chunks while
    keeping duplicated embedding input relatively small.
    """

    overlap = []
    total_words = 0

    for sentence in reversed(sentences):

        sentence_words = word_count(
            sentence
        )

        if (
            total_words + sentence_words
            > OVERLAP_WORDS
        ):
            break

        overlap.insert(
            0,
            sentence,
        )

        total_words += sentence_words

    return overlap


def create_chunks(
    text: str,
) -> list[str]:
    """
    Create sentence-aware chunks using an approximate word
    limit.

    No embedding model or tokenizer is required locally.
    """

    sentences = split_into_sentences(text)

    chunks = []

    current_sentences = []
    current_words = 0

    for sentence in sentences:

        sentence_words = word_count(
            sentence
        )

        # ----------------------------------------------------
        # Handle an unusually long individual sentence
        # ----------------------------------------------------

        if sentence_words > MAX_CHUNK_WORDS:

            if current_sentences:
                chunks.append(
                    " ".join(
                        current_sentences
                    )
                )

                current_sentences = []
                current_words = 0

            chunks.extend(
                split_long_sentence(
                    sentence
                )
            )

            continue

        # ----------------------------------------------------
        # Sentence fits in current chunk
        # ----------------------------------------------------

        if (
            current_words + sentence_words
            <= MAX_CHUNK_WORDS
        ):
            current_sentences.append(
                sentence
            )

            current_words += sentence_words

            continue

        # ----------------------------------------------------
        # Finish current chunk
        # ----------------------------------------------------

        if current_sentences:
            chunks.append(
                " ".join(
                    current_sentences
                )
            )

        # ----------------------------------------------------
        # Add limited overlap
        # ----------------------------------------------------

        overlap = get_overlap_sentences(
            current_sentences
        )

        # Make sure overlap + new sentence does not exceed
        # the maximum chunk size.
        while (
            overlap
            and (
                sum(
                    word_count(item)
                    for item in overlap
                )
                + sentence_words
                > MAX_CHUNK_WORDS
            )
        ):
            overlap.pop(0)

        current_sentences = (
            overlap + [sentence]
        )

        current_words = sum(
            word_count(item)
            for item in current_sentences
        )

    # Final chunk.
    if current_sentences:
        chunks.append(
            " ".join(
                current_sentences
            )
        )

    return chunks


# ============================================================
# Main ingestion
# ============================================================

def ingest_pdf(
    pdf_path: Path,
) -> None:

    # --------------------------------------------------------
    # Validate file
    # --------------------------------------------------------

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(
            f"Expected a PDF file, got: {pdf_path}"
        )

    print(f"PDF: {pdf_path}")

    # --------------------------------------------------------
    # Extract PDF
    # --------------------------------------------------------

    print("Extracting PDF text...")

    pages = extract_pages(
        pdf_path
    )

    if not pages:
        raise RuntimeError(
            "No text could be extracted from the PDF."
        )

    print(
        f"Extracted text from "
        f"{len(pages)} pages."
    )

    # --------------------------------------------------------
    # Create stable paper ID
    # --------------------------------------------------------

    paper_id = generate_paper_id(
        pdf_path
    )

    print(
        f"Paper ID: "
        f"{paper_id[:16]}..."
    )

    # --------------------------------------------------------
    # Create chunks
    # --------------------------------------------------------

    print("Creating chunks...")

    documents = []

    chunk_index = 0

    for page in pages:

        chunks = create_chunks(
            page["text"]
        )

        for chunk in chunks:

            documents.append(
                {
                    "paper_id": paper_id,
                    "source": pdf_path.name,
                    "page": page["page"],
                    "chunk_index": chunk_index,

                    # This is the field indexed by the
                    # Atlas autoEmbed Vector Search index.
                    "content": chunk,
                }
            )

            chunk_index += 1

    if not documents:
        raise RuntimeError(
            "No chunks were generated."
        )

    print(
        f"Created {len(documents)} chunks."
    )

    # --------------------------------------------------------
    # Connect to MongoDB
    # --------------------------------------------------------

    print("Connecting to MongoDB...")

    client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=10000,
    )

    try:
        # Verify connection.
        client.admin.command(
            "ping"
        )

        database = client[
            MONGODB_DATABASE
        ]

        collection = database[
            MONGODB_COLLECTION
        ]

        print(
            "MongoDB connection successful."
        )

        # ----------------------------------------------------
        # Regular MongoDB index
        # ----------------------------------------------------

        collection.create_index(
            [
                ("paper_id", 1),
                ("chunk_index", 1),
            ],
            unique=True,
        )

        # ----------------------------------------------------
        # Upsert chunks
        # ----------------------------------------------------

        print("Uploading chunks...")

        operations = []

        for document in documents:

            operations.append(
                ReplaceOne(
                    {
                        "paper_id":
                            document["paper_id"],
                        "chunk_index":
                            document["chunk_index"],
                    },
                    document,
                    upsert=True,
                )
            )

        result = collection.bulk_write(
            operations,
            ordered=False,
        )

        # ----------------------------------------------------
        # Remove obsolete chunks
        # ----------------------------------------------------
        #
        # Useful if the same PDF was previously ingested with
        # different chunk settings.

        delete_result = collection.delete_many(
            {
                "paper_id": paper_id,
                "chunk_index": {
                    "$gte": len(documents)
                },
            }
        )

        # ----------------------------------------------------
        # Summary
        # ----------------------------------------------------

        print()
        print("=" * 70)
        print("INGESTION COMPLETE")
        print("=" * 70)

        print(
            f"PDF:       {pdf_path.name}"
        )

        print(
            f"Pages:     {len(pages)}"
        )

        print(
            f"Chunks:    {len(documents)}"
        )

        print(
            f"Inserted:  "
            f"{result.upserted_count}"
        )

        print(
            f"Updated:   "
            f"{result.modified_count}"
        )

        print(
            f"Deleted:   "
            f"{delete_result.deleted_count}"
        )

        print()
        print(
            "Embeddings are handled automatically "
            "by the MongoDB Vector Search index."
        )

    finally:
        client.close()


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":

    if len(sys.argv) != 2:

        print(
            "Usage:\n"
            "  uv run ingest.py "
            "data/paper.pdf"
        )

        sys.exit(1)

    path = Path(
        sys.argv[1]
    )

    ingest_pdf(
        path
    )