import argparse
import os
import sys

from dotenv import load_dotenv
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer


# ============================================================
# Configuration
# ============================================================

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384

VECTOR_INDEX_NAME = "paper_vector_index"
VECTOR_FIELD = "embedding"

DEFAULT_LIMIT = 5


# ============================================================
# Environment
# ============================================================

load_dotenv()

MONGODB_URI = os.environ["MONGO_URI"]
MONGODB_DATABASE = os.environ.get(
    "MONGO_DB_NAME",
    "rag_db",
)
MONGODB_COLLECTION = os.environ.get(
    "MONGO_DB_COLLECTION_NAME",
    "rag_paper_chunks",
)


# ============================================================
# Search
# ============================================================

def search(
    query: str,
    limit: int = DEFAULT_LIMIT,
) -> list[dict]:

    print(f'Query: "{query}"')
    print()

    # --------------------------------------------------------
    # Load same embedding model used for ingestion
    # --------------------------------------------------------

    print(f"Loading model: {MODEL_NAME}")

    model = SentenceTransformer(
        MODEL_NAME
    )

    # --------------------------------------------------------
    # Generate query embedding
    # --------------------------------------------------------

    print("Generating query embedding...")

    query_embedding = model.encode(
        query,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    if len(query_embedding) != EMBEDDING_DIMENSIONS:
        raise RuntimeError(
            "Unexpected embedding dimension: "
            f"{len(query_embedding)}"
        )

    query_vector = query_embedding.tolist()

    # --------------------------------------------------------
    # MongoDB connection
    # --------------------------------------------------------

    print("Connecting to MongoDB...")

    client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=10000,
    )

    try:
        client.admin.command("ping")

        collection = client[
            MONGODB_DATABASE
        ][
            MONGODB_COLLECTION
        ]

        print("MongoDB connection successful.")

        # MongoDB recommends considering substantially more
        # candidates than the final number of results.
        num_candidates = max(
            limit * 20,
            100,
        )

        # ----------------------------------------------------
        # Vector Search
        # ----------------------------------------------------

        pipeline = [
            {
                "$vectorSearch": {
                    "index": VECTOR_INDEX_NAME,
                    "path": VECTOR_FIELD,
                    "queryVector": query_vector,
                    "numCandidates": num_candidates,
                    "limit": limit,
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "paper_id": 1,
                    "source": 1,
                    "page": 1,
                    "chunk_index": 1,
                    "content": 1,
                    "score": {
                        "$meta": "vectorSearchScore"
                    },
                }
            },
        ]

        return list(
            collection.aggregate(pipeline)
        )

    finally:
        client.close()


# ============================================================
# Output
# ============================================================

def print_results(results: list[dict]) -> None:

    if not results:
        print()
        print("No results found.")
        print(
            "Make sure paper_vector_index is READY "
            "and that documents have been ingested."
        )
        return

    print()
    print("=" * 70)
    print(f"FOUND {len(results)} RESULTS")
    print("=" * 70)

    for position, result in enumerate(
        results,
        start=1,
    ):
        print()
        print(f"RESULT #{position}")
        print("-" * 70)

        print(
            f"Score:       "
            f"{result.get('score', 0):.4f}"
        )

        print(
            f"Source:      "
            f"{result.get('source', 'unknown')}"
        )

        print(
            f"Page:        "
            f"{result.get('page', 'unknown')}"
        )

        print(
            f"Chunk:       "
            f"{result.get('chunk_index', 'unknown')}"
        )

        print()
        print(result.get("content", ""))

        print()
        print("-" * 70)


# ============================================================
# CLI
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Test semantic search against "
            "MongoDB Vector Search."
        )
    )

    parser.add_argument(
        "query",
        nargs="*",
        help="Natural-language query",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help="Number of results to return (default: 5)",
    )

    args = parser.parse_args()

    # Allow either:
    #
    # uv run test_search.py "some query"
    #
    # or:
    #
    # uv run test_search.py
    # Query: ...

    if args.query:
        query = " ".join(args.query)
    else:
        query = input("Query: ").strip()

    if not query:
        print("Query cannot be empty.")
        sys.exit(1)

    if args.limit < 1:
        print("--limit must be at least 1.")
        sys.exit(1)

    try:
        results = search(
            query=query,
            limit=args.limit,
        )

        print_results(results)

    except Exception as error:
        print()
        print("Search failed:")
        print(error)
        sys.exit(1)


if __name__ == "__main__":
    main()