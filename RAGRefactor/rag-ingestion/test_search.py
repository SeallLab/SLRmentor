import os
import sys

from dotenv import load_dotenv
from pymongo import MongoClient


# ============================================================
# Configuration
# ============================================================

load_dotenv()

MONGODB_URI = os.environ["MONGO_URI"]

MONGODB_DATABASE = os.environ.get(
    "MONGO_DB_NAME"
)

MONGODB_COLLECTION = os.environ.get(
    "MONGO_DB_RAG_COLLECTION_NAME",
)

# IMPORTANT:
# Change this if your Atlas Vector Search index has
# a different name.
VECTOR_SEARCH_INDEX = os.environ.get(
    "VECTOR_SEARCH_INDEX",
    "autoembed_index",
)

DEFAULT_LIMIT = 5


# ============================================================
# Vector Search
# ============================================================

def search(
    query: str,
    limit: int = DEFAULT_LIMIT,
) -> list[dict]:
    """
    Send a plain-text query to MongoDB Atlas.

    Atlas automatically generates the query embedding using
    the embedding model configured in the Vector Search index
    and returns the most semantically similar chunks.
    """

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

        pipeline = [
            {
                "$vectorSearch": {
                    "index":
                        VECTOR_SEARCH_INDEX,

                    # Same field configured as autoEmbed
                    # in the Vector Search index.
                    "path":
                        "content",

                    # Plain text.
                    #
                    # NO local embedding generation.
                    # MongoDB embeds this automatically.
                    "query": {
                        "text": query
                    },

                    # Number of candidate vectors Atlas
                    # considers before returning the best
                    # matches.
                    "numCandidates":
                        max(limit * 10, 50),

                    "limit":
                        limit,
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
                        "$meta":
                            "vectorSearchScore"
                    },
                }
            },
        ]

        return list(
            collection.aggregate(
                pipeline
            )
        )

    finally:
        client.close()


# ============================================================
# Result display
# ============================================================

def print_results(
    query: str,
    results: list[dict],
) -> None:

    print()
    print("=" * 80)
    print("QUERY")
    print("=" * 80)
    print(query)

    if not results:

        print()
        print(
            "No results found."
        )

        return

    print()
    print(
        f"Returned "
        f"{len(results)} result(s)."
    )

    for index, result in enumerate(
        results,
        start=1,
    ):

        print()
        print("=" * 80)
        print(
            f"RESULT {index}"
        )
        print("=" * 80)

        score = result.get(
            "score"
        )

        if isinstance(
            score,
            (int, float),
        ):
            print(
                f"Score:  {score:.6f}"
            )

        else:
            print(
                f"Score:  {score}"
            )

        print(
            f"Source: "
            f"{result.get('source', 'N/A')}"
        )

        print(
            f"Page:   "
            f"{result.get('page', 'N/A')}"
        )

        print(
            f"Chunk:  "
            f"{result.get('chunk_index', 'N/A')}"
        )

        print()
        print(
            result.get(
                "content",
                "",
            )
        )


# ============================================================
# CLI
# ============================================================

def main() -> None:

    # Query supplied directly:
    #
    # uv run test_search.py "your question"

    if len(sys.argv) > 1:

        query = " ".join(
            sys.argv[1:]
        ).strip()

    # Or interactive mode:
    #
    # uv run test_search.py

    else:

        query = input(
            "Enter search query: "
        ).strip()

    if not query:

        print(
            "Query cannot be empty."
        )

        sys.exit(1)

    try:
        results = search(
            query=query,
            limit=DEFAULT_LIMIT,
        )

    except Exception as error:

        print()
        print(
            "Vector search failed:"
        )

        print(error)

        sys.exit(1)

    print_results(
        query,
        results,
    )


if __name__ == "__main__":
    main()