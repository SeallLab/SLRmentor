import hashlib
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from pypdf import PdfReader
from pymongo import MongoClient, ReplaceOne
from sentence_transformers import SentenceTransformer


# ============================================================
# Configuration
# ============================================================

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# MiniLM supports up to ~256 tokens.
# Keep some margin below that limit.
MAX_CHUNK_TOKENS = 200
OVERLAP_TOKENS = 30

EMBEDDING_DIMENSIONS = 384
EMBEDDING_BATCH_SIZE = 32

load_dotenv()

MONGODB_URI = os.environ["MONGO_URI"]
MONGODB_DATABASE = os.environ.get("MONGO_DB_NAME", "rag_db_test")
MONGODB_COLLECTION = os.environ.get(
    "MONGO_DB_COLLECTION_NAME",
    "test_paper_chunks",
)


# ============================================================
# Helpers
# ============================================================

def generate_paper_id(pdf_path: Path) -> str:
    """
    Generate a stable ID based on the PDF contents.

    If the exact same PDF is ingested again, it receives
    the same paper_id.
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

    # Remove null bytes
    text = text.replace("\x00", "")

    # Join words broken across lines:
    #
    #   "transfor-\nmation"
    # becomes
    #   "transformation"
    text = re.sub(
        r"(?<=\w)-\s*\n\s*(?=\w)",
        "",
        text,
    )

    # Normalize line breaks inside paragraphs
    text = re.sub(
        r"(?<!\n)\n(?!\n)",
        " ",
        text,
    )

    # Collapse repeated spaces/tabs
    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    # Normalize paragraph spacing
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


def extract_pages(pdf_path: Path) -> list[dict]:
    """
    Extract text from each PDF page independently so that
    page metadata can be retained in MongoDB.
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
    Basic sentence splitter.

    This keeps chunks more natural than blindly splitting
    every N tokens.
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


def token_count(
    text: str,
    tokenizer,
) -> int:
    return len(
        tokenizer.encode(
            text,
            add_special_tokens=False,
        )
    )


def split_long_sentence(
    sentence: str,
    tokenizer,
) -> list[str]:
    """
    Fallback for a sentence that by itself exceeds the
    maximum chunk size.
    """

    token_ids = tokenizer.encode(
        sentence,
        add_special_tokens=False,
    )

    pieces = []

    start = 0

    while start < len(token_ids):
        end = min(
            start + MAX_CHUNK_TOKENS,
            len(token_ids),
        )

        piece = tokenizer.decode(
            token_ids[start:end],
            skip_special_tokens=True,
        ).strip()

        if piece:
            pieces.append(piece)

        if end >= len(token_ids):
            break

        start = end - OVERLAP_TOKENS

    return pieces


def get_overlap_sentences(
    sentences: list[str],
    tokenizer,
) -> list[str]:
    """
    Preserve the final ~OVERLAP_TOKENS worth of sentences
    for the next chunk.
    """

    overlap = []
    total_tokens = 0

    for sentence in reversed(sentences):
        sentence_tokens = token_count(
            sentence,
            tokenizer,
        )

        if (
            total_tokens + sentence_tokens
            > OVERLAP_TOKENS
        ):
            break

        overlap.insert(0, sentence)
        total_tokens += sentence_tokens

    return overlap


def create_chunks(
    text: str,
    tokenizer,
) -> list[str]:
    """
    Create sentence-aware chunks while respecting the model's
    token limit.
    """

    sentences = split_into_sentences(text)

    chunks = []
    current_sentences = []
    current_tokens = 0

    for sentence in sentences:

        sentence_tokens = token_count(
            sentence,
            tokenizer,
        )

        # Handle unusually long individual sentences
        if sentence_tokens > MAX_CHUNK_TOKENS:

            if current_sentences:
                chunks.append(
                    " ".join(current_sentences)
                )

                current_sentences = []
                current_tokens = 0

            chunks.extend(
                split_long_sentence(
                    sentence,
                    tokenizer,
                )
            )

            continue

        # Sentence still fits in current chunk
        if (
            current_tokens + sentence_tokens
            <= MAX_CHUNK_TOKENS
        ):
            current_sentences.append(sentence)
            current_tokens += sentence_tokens
            continue

        # Finish the existing chunk
        chunks.append(
            " ".join(current_sentences)
        )

        # Keep some semantic overlap with the next chunk
        overlap = get_overlap_sentences(
            current_sentences,
            tokenizer,
        )

        current_sentences = overlap + [sentence]

        current_tokens = sum(
            token_count(item, tokenizer)
            for item in current_sentences
        )

    if current_sentences:
        chunks.append(
            " ".join(current_sentences)
        )

    return chunks


# ============================================================
# Main ingestion
# ============================================================

def ingest_pdf(pdf_path: Path) -> None:

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
    # Load embedding model
    # --------------------------------------------------------

    print(f"Loading model: {MODEL_NAME}")

    model = SentenceTransformer(
        MODEL_NAME
    )

    tokenizer = model.tokenizer

    # --------------------------------------------------------
    # Extract PDF
    # --------------------------------------------------------

    print("Extracting PDF text...")

    pages = extract_pages(pdf_path)

    if not pages:
        raise RuntimeError(
            "No text could be extracted from the PDF."
        )

    print(
        f"Extracted text from {len(pages)} pages."
    )

    # --------------------------------------------------------
    # Create stable paper ID
    # --------------------------------------------------------

    paper_id = generate_paper_id(pdf_path)

    print(
        f"Paper ID: {paper_id[:16]}..."
    )

    # --------------------------------------------------------
    # Create chunks
    # --------------------------------------------------------

    documents = []

    chunk_index = 0

    for page in pages:

        chunks = create_chunks(
            page["text"],
            tokenizer,
        )

        for chunk in chunks:

            documents.append(
                {
                    "paper_id": paper_id,
                    "source": pdf_path.name,
                    "page": page["page"],
                    "chunk_index": chunk_index,
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
    # Generate embeddings
    # --------------------------------------------------------

    print("Generating embeddings...")

    texts = [
        document["content"]
        for document in documents
    ]

    embeddings = model.encode(
        texts,
        batch_size=EMBEDDING_BATCH_SIZE,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    if embeddings.shape[1] != EMBEDDING_DIMENSIONS:
        raise RuntimeError(
            "Unexpected embedding dimension: "
            f"{embeddings.shape[1]}"
        )

    # --------------------------------------------------------
    # Attach embeddings + metadata
    # --------------------------------------------------------

    for document, embedding in zip(
        documents,
        embeddings,
    ):
        document["embedding"] = (
            embedding.tolist()
        )

        document["embedding_model"] = (
            MODEL_NAME
        )

        document["embedding_dimensions"] = (
            EMBEDDING_DIMENSIONS
        )

    # --------------------------------------------------------
    # Connect to MongoDB
    # --------------------------------------------------------

    print("Connecting to MongoDB...")

    client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=10000,
    )

    # Verify connection
    client.admin.command("ping")

    database = client[
        MONGODB_DATABASE
    ]

    collection = database[
        MONGODB_COLLECTION
    ]

    print("MongoDB connection successful.")

    # --------------------------------------------------------
    # Useful regular MongoDB index
    # --------------------------------------------------------

    collection.create_index(
        [
            ("paper_id", 1),
            ("chunk_index", 1),
        ],
        unique=True,
    )

    # --------------------------------------------------------
    # Upsert chunks
    # --------------------------------------------------------

    print("Uploading chunks...")

    operations = []

    for document in documents:

        operations.append(
            ReplaceOne(
                {
                    "paper_id": document["paper_id"],
                    "chunk_index": document["chunk_index"],
                },
                document,
                upsert=True,
            )
        )

    result = collection.bulk_write(
        operations,
        ordered=False,
    )

    # Remove obsolete chunks in case this document had
    # previously been ingested with different chunk settings.
    collection.delete_many(
        {
            "paper_id": paper_id,
            "chunk_index": {
                "$gte": len(documents)
            },
        }
    )

    print()
    print("Ingestion complete.")
    print(f"PDF: {pdf_path.name}")
    print(f"Pages: {len(pages)}")
    print(f"Chunks: {len(documents)}")
    print(
        f"Inserted: {result.upserted_count}"
    )
    print(
        f"Updated: {result.modified_count}"
    )
    print(
        f"Embedding dimensions: "
        f"{EMBEDDING_DIMENSIONS}"
    )

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

    path = Path(sys.argv[1])

    ingest_pdf(path)