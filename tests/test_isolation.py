import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from src import retrieval
from src.config import COLLECTION_NAME
from src.ingestion import delete_file_chunks, ensure_collection

DIM = 16


def _chunk(owner_id: str, source_file: str, text: str) -> Document:
    return Document(
        page_content=text,
        metadata={"owner_id": owner_id, "source_file": source_file, "page_label": "1"},
    )


@pytest.fixture
def store(monkeypatch):
    # Qdrant in memoria ed embedding finti: niente Docker, niente modello da scaricare.
    client = QdrantClient(":memory:")
    ensure_collection(client, dim=DIM)
    store = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=DeterministicFakeEmbedding(size=DIM),
    )
    store.add_documents([
        _chunk("alice", "alice.pdf", "ricerca in ampiezza"),
        _chunk("alice", "comune.pdf", "ricerca in profondita'"),
        _chunk("bob", "comune.pdf", "unificazione in Prolog"),
    ])
    monkeypatch.setattr(retrieval, "_get_store", lambda: store)
    return store


def test_search_returns_only_own_chunks(store):
    # La query è il testo esatto di un chunk di Alice: senza filtro sarebbe il primo risultato.
    docs = retrieval.get_retriever("bob", k=10).invoke("ricerca in ampiezza")
    assert docs
    assert {d.metadata["owner_id"] for d in docs} == {"bob"}


def test_unknown_owner_sees_nothing(store):
    assert retrieval.get_retriever("carol", k=10).invoke("ricerca in ampiezza") == []
    assert retrieval.list_source_files("carol") == []


def test_list_source_files_per_owner(store):
    assert retrieval.list_source_files("alice") == ["alice.pdf", "comune.pdf"]
    assert retrieval.list_source_files("bob") == ["comune.pdf"]


def test_reingest_deletes_only_own_file(store):
    # Stesso nome file per due owner: la cancellazione deve filtrare su owner E file.
    delete_file_chunks(store.client, "alice", "comune.pdf")
    assert retrieval.list_source_files("alice") == ["alice.pdf"]
    assert retrieval.list_source_files("bob") == ["comune.pdf"]
