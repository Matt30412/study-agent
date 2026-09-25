"""Retrieval: connessione alla collection Qdrant esistente."""


from functools import lru_cache
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from src.config import COLLECTION_NAME, EMBEDDING_MODEL, QDRANT_URL, RETRIEVER_K
from src.tenancy import validate_owner_id
from qdrant_client import models



@lru_cache(maxsize=1)
def _get_store() -> QdrantVectorStore:
    return QdrantVectorStore.from_existing_collection(
        embedding=HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL),
        url=QDRANT_URL,
        collection_name=COLLECTION_NAME,
    )


def owner_filter(owner_id: str) -> models.Filter:
    return models.Filter(must=[
        models.FieldCondition(key="metadata.owner_id", match=models.MatchValue(value=validate_owner_id(owner_id)))
    ])


    
def get_retriever(owner_id:str ,k: int = RETRIEVER_K):
    
    return _get_store().as_retriever(search_kwargs={"k": k, "filter": owner_filter(owner_id)})


def list_source_files(owner_id: str) -> list[str]:
    client = _get_store().client
    files, offset = set(), None
    while True:
        points, offset = client.scroll(
            COLLECTION_NAME,
            scroll_filter=owner_filter(owner_id),
            with_payload=["metadata.source_file"],
            with_vectors=False,
            limit=256,
            offset=offset,
        )
        files.update(p.payload["metadata"]["source_file"] for p in points)
        if offset is None:
            return sorted(files)