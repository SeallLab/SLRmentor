import os
import sys

from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv()

MONGODB_URI = os.environ["MONGO_URI"]
MONGODB_DATABASE = os.environ.get(
    "MONGO_DB_NAME"
)
MONGODB_COLLECTION = os.environ.get(
    "MONGO_DB_RAG_COLLECTION_NAME"
)


def main():
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

        document_count = collection.count_documents({})

        print(
            f"Database:   {MONGODB_DATABASE}"
        )
        print(
            f"Collection: {MONGODB_COLLECTION}"
        )
        print(
            f"Documents:  {document_count}"
        )

        if document_count == 0:
            print("\nCollection is already empty.")
            return

        confirmation = input(
            "\nDelete ALL documents from this collection? "
            "Type 'yes' to continue: "
        )

        if confirmation.lower() != "yes":
            print("Cancelled.")
            return

        result = collection.delete_many({})

        print()
        print(
            f"Deleted {result.deleted_count} documents."
        )
        print(
            "Collection was NOT deleted."
        )

    finally:
        client.close()


if __name__ == "__main__":
    main()