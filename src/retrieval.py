"""Retrieval: connessione alla collection Qdrant esistente."""

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from src.config import COLLECTION_NAME, EMBEDDING_MODEL, QDRANT_URL, RETRIEVER_K


def get_retriever(k: int = RETRIEVER_K):
    store = QdrantVectorStore.from_existing_collection(
        embedding=HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL),
        url=QDRANT_URL,
        collection_name=COLLECTION_NAME,
    )
    return store.as_retriever(search_kwargs={"k": k})