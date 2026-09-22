"""Retrieval: connessione alla collection Qdrant esistente."""

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore

COLLECTION_NAME = "study_agent"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
QDRANT_URL = "http://localhost:6333"


def get_retriever(k: int = 3):
    store = QdrantVectorStore.from_existing_collection(
        embedding=HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL),
        url=QDRANT_URL,
        collection_name=COLLECTION_NAME,
    )
    return store.as_retriever(search_kwargs={"k": k})