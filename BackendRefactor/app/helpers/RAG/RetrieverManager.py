from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import MongoDBAtlasVectorSearch
import os

class RetrieverManager:
    """
    Manages initialization and use of a MongoDB Atlas vector retriever,
    along with helper formatting utilities for retrieved documents.
    """

    def __init__(
        self,
        mongo_uri: str,
        namespace: str = "SLRMentor.document_rag",
        index_name: str = "vector_index",
        top_k: int = 5
    ):
        """
        Initialize the retriever.
        """
        self.mongo_uri = mongo_uri
        self.namespace = namespace
        self.index_name = index_name
        self.top_k = top_k

        # Initialize embedding model
        self.embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        # Initialize vector store
        self.vector_store = MongoDBAtlasVectorSearch.from_connection_string(
            connection_string=self.mongo_uri,
            namespace=self.namespace,
            embedding=self.embedding_model,
            index_name=self.index_name
        )

        # Initialize retriever
        self.retriever = self.vector_store.as_retriever(
            search_kwargs={"k": self.top_k}
        )

    # ---------------------------
    # Retriever Access Helpers
    # ---------------------------
    def get_relevant_documents_safe(self, query: str):
        """
        Safely call whichever method the retriever provides.
        """
        if hasattr(self.retriever, "get_relevant_documents"):
            return self.retriever.get_relevant_documents(query)
        elif hasattr(self.retriever, "retrieve"):
            return self.retriever.retrieve(query)
        elif hasattr(self.retriever, "invoke"):
            return self.retriever.invoke(query)
        else:
            raise AttributeError("Retriever does not support any known query method.")

    # ---------------------------
    # Document Formatting Helpers
    # ---------------------------
    @staticmethod
    def format_docs(docs: list) -> list:
        """
        Extract text from list of documents (dicts or LangChain Document objects).
        """
        texts = []

        for doc in docs:
            if isinstance(doc, dict):  # MongoDB dict
                text = doc.get("text") or doc.get("page_content")
            else:  # LangChain Document
                text = (
                    getattr(doc, "page_content", None)
                    or getattr(doc, "text", None)
                )
            if text:
                texts.append(text)

        return texts

    @staticmethod
    def format_docs_prompt(
        docs: list,
        prescript: str = "",
        count: int = 0
    ) -> list:
        """
        Same as format_docs but also injects a prescript before each item.
        """
        if prescript == "":
            return docs

        texts = []
        for i, d in enumerate(docs):
            if count == 1:
                pres = f"{prescript} {i+1}: "
            else:
                pres = f"{prescript}: "
            texts.append(pres + d)

        return texts
