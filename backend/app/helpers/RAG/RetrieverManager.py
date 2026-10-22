from __future__ import annotations

from typing import TYPE_CHECKING

from pymongo import MongoClient

if TYPE_CHECKING:
    from langchain_core.documents import Document


class RetrieverManager:
    """
    Manages document retrieval from MongoDB Atlas Vector Search
    using MongoDB's hosted Automated Embedding functionality.

    Query embeddings are generated remotely by MongoDB Atlas.
    No local embedding model is loaded or executed.

    Two retrieval interfaces are provided:

    1. get_relevant_documents()
       New retrieval method that returns native Python dictionaries.
       Does not depend on LangChain for retrieval or formatting.

    2. get_relevant_documents_safe()
       Legacy retrieval method that returns LangChain Document objects.
       Maintained for backward compatibility with existing RAG code.

    Both methods share the same MongoDB retrieval pipeline.

    The class also provides utilities for formatting retrieved
    documents and managing the MongoDB connection.
    """

    def __init__(
        self,
        mongo_uri: str,
        namespace: str,
        index_name: str = "autoembed_index",
        top_k: int = 5
    ):
        """
        Initialize the MongoDB Atlas retriever.

        Args:
            mongo_uri (str):
                MongoDB Atlas connection string.

            namespace (str):
                MongoDB database and collection in the format
                "database.collection".

            index_name (str):
                Name of the MongoDB Atlas Vector Search index.
                Defaults to "autoembed_index".

            top_k (int):
                Maximum number of relevant documents to retrieve.
                Defaults to 5.

        Raises:
            ValueError:
                If top_k is invalid or namespace is incorrectly formatted.

        Notes:
            Initializes the MongoDB client and selects the collection.
            Does not load any embedding model locally.

            MongoClient manages connection pooling automatically.
            The connection is established lazily when needed.
        """

        self.mongo_uri = mongo_uri
        self.namespace = namespace
        self.index_name = index_name
        self.top_k = top_k

        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
            raise ValueError("top_k must be a positive integer.")

        if not isinstance(namespace, str) or "." not in namespace:
            raise ValueError(
                "namespace must have the format 'database.collection'."
            )

        database_name, collection_name = namespace.split(".", 1)

        if not database_name or not collection_name:
            raise ValueError("Invalid MongoDB namespace.")

        # Initialize MongoDB client.
        self.client = MongoClient(
            self.mongo_uri,
            serverSelectionTimeoutMS=10000
        )

        # Select the target database and collection.
        self.collection = self.client[database_name][collection_name]

    # ============================================================
    # New Retrieval Method (Native MongoDB)
    # ============================================================

    def get_relevant_documents(self, query: str) -> list[dict]:
        """
        Retrieve relevant documents directly from MongoDB Atlas.

        This is the NEW retrieval method and should be preferred
        for new implementations.

        Uses MongoDB Atlas Automated Embedding to convert the
        query into a vector remotely and retrieve semantically
        similar document chunks.

        Unlike the legacy method, this method returns native
        Python dictionaries and does not use LangChain.

        Args:
            query (str):
                Natural-language search query.

        Returns:
            list[dict]:
                List of MongoDB documents containing:

                - content: Retrieved document text.
                - paper_id: Associated paper identifier.
                - source: Original document source.
                - page: Page number.
                - chunk_index: Position of the text chunk.
                - score: MongoDB vector similarity score.

                Only fields present in the collection are returned.

        Raises:
            ValueError:
                If the query is empty or invalid.

            pymongo.errors.PyMongoError:
                If the MongoDB query fails.

        Notes:
            - No local embedding generation occurs.
            - MongoDB Atlas handles query embedding remotely.
            - Results are limited by self.top_k.
            - The Vector Search index must support autoEmbed.
            - The indexed text field must be "content".
        """

        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query must be a non-empty string.")

        pipeline = [
            {
                "$vectorSearch": {
                    "index": self.index_name,
                    "path": "content",
                    "query": {
                        "text": query.strip()
                    },
                    "numCandidates": min(
                        max(self.top_k * 10, 50),
                        10000
                    ),
                    "limit": self.top_k
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
                    }
                }
            }
        ]

        return list(self.collection.aggregate(pipeline))

    # ============================================================
    # Legacy Retrieval Method (LangChain Compatibility)
    # ============================================================

    def get_relevant_documents_safe(self, query: str) -> list[Document]:
        """
        Retrieve relevant documents as LangChain Document objects.

        LEGACY METHOD:
            Maintained for backward compatibility with code that
            expects LangChain Document objects.

        Internally calls the new get_relevant_documents() method
        and converts the returned MongoDB dictionaries into
        LangChain Document objects.

        This method does not use LangChain for vector retrieval.
        LangChain is only used for the Document data structure.

        Args:
            query (str):
                Natural-language search query.

        Returns:
            list[Document]:
                List of LangChain Document objects containing:

                - page_content: Retrieved text.
                - metadata: Source information, page number,
                  chunk index, paper ID, and similarity score.

        Raises:
            ValueError:
                If the query is empty or invalid.

            pymongo.errors.PyMongoError:
                If MongoDB retrieval fails.

        Notes:
            - No local embedding model is loaded.
            - Retrieval is performed using MongoDB Atlas.
            - Conversion adds LangChain compatibility overhead.
            - Prefer get_relevant_documents() for new code.
        """

        # Only legacy callers need the optional LangChain Document type.
        from langchain_core.documents import Document

        results = self.get_relevant_documents(query)

        documents = []

        for result in results:
            content = result.get("content", "")

            if not content:
                continue

            metadata = {
                key: value
                for key, value in result.items()
                if key != "content"
            }

            documents.append(
                Document(
                    page_content=content,
                    metadata=metadata
                )
            )

        return documents

    # ============================================================
    # Document Formatting Helpers
    # ============================================================

    @staticmethod
    def format_docs(docs: list) -> list[str]:
        """
        Extract text content from retrieved documents.

        Supports both retrieval formats:

        1. Native MongoDB dictionaries returned by
           get_relevant_documents().

        2. LangChain Document objects returned by
           get_relevant_documents_safe().

        Args:
            docs (list):
                List of MongoDB dictionaries or LangChain Documents.

        Returns:
            list[str]:
                List containing only the text content of each document.

        Notes:
            - Empty document content is ignored.
            - Document metadata is not included in the output.
            - Useful for preparing context for LLM prompts.
        """

        texts = []

        for doc in docs:
            if isinstance(doc, dict):
                text = (
                    doc.get("content")
                    or doc.get("text")
                    or doc.get("page_content")
                )
            else:
                text = (
                    getattr(doc, "page_content", None)
                    or getattr(doc, "text", None)
                )

            if text:
                texts.append(text)

        return texts

    @staticmethod
    def format_docs_prompt(
        docs: list[str],
        prescript: str = "",
        count: int = 0
    ) -> list[str]:
        """
        Add a prefix before each document's text.

        Useful when preparing retrieved content for inclusion
        in an LLM prompt.

        Args:
            docs (list[str]):
                List of document text strings.

            prescript (str):
                Prefix to place before each document.
                Defaults to an empty string.

            count (int):
                If 1, appends a sequential number to each prefix.
                Otherwise, uses the same prefix for all documents.

        Returns:
            list[str]:
                List of formatted text strings.

        Example:
            Input:
                docs = ["First text", "Second text"]
                prescript = "Document"
                count = 1

            Output:
                [
                    "Document 1: First text",
                    "Document 2: Second text"
                ]

        Notes:
            If prescript is empty, the original list is returned
            unchanged.
        """

        if prescript == "":
            return docs

        texts = []

        for i, d in enumerate(docs):
            if count == 1:
                pres = f"{prescript} {i + 1}: "
            else:
                pres = f"{prescript}: "

            texts.append(pres + d)

        return texts

    # ============================================================
    # Connection Management
    # ============================================================

    def close(self) -> None:
        """
        Close the MongoDB client and its connection pool.

        Should be called when the RetrieverManager is no longer
        needed, typically during application shutdown.

        Notes:
            - Releases MongoDB connection resources.
            - Does not delete documents or modify the database.
            - A closed MongoClient should not be reused.
        """

        self.client.close()
