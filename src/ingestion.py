"""Ingestion: PDF -> chunk -> embedding -> Qdrant."""

from pathlib import Path
import argparse
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from src.config import CHUNK_OVERLAP, DATA_DIR, COLLECTION_NAME, EMBEDDING_MODEL, QDRANT_URL,CHUNK_SIZE
from src.tenancy import validate_owner_id
from qdrant_client import QdrantClient, models


def ensure_collection(client : QdrantClient, dim: int) -> None:
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
        )

    client.create_payload_index(
        COLLECTION_NAME,
        field_name = "metadata.owner_id",
        field_schema=models.KeywordIndexParams(type="keyword", is_tenant=True),
    )


def delete_file_chunks(client: QdrantClient, owner_id: str, source_file: str) -> None:
    client.delete(
        COLLECTION_NAME,
        points_selector=models.FilterSelector(
            filter = models.Filter(must = [
                models.FieldCondition(key="metadata.owner_id",match = models.MatchValue(value = owner_id)),
                models.FieldCondition(key = "metadata.source_file", match = models.MatchValue(value = source_file))
            ])
        ),
    )


def ingest(owner_id: str, data_dir: Path) ->None:
    owner_id = validate_owner_id(owner_id)
    pdfs = sorted(data_dir.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"NEssun PDF in {data_dir.resolve()}")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    client = QdrantClient(url=QDRANT_URL)
    ensure_collection(client, dim=len(embeddings.embed_query("dim")))
    store = QdrantVectorStore(client= client, collection_name=COLLECTION_NAME, embedding=embeddings)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    for path in pdfs:
        pages = PyPDFLoader(str(path)).load()
        for p in pages:
            p.metadata["source_file"] = path.name
            p.metadata["owner_id"] = owner_id
        chunks = splitter.split_documents(pages)
        delete_file_chunks(client, owner_id, path.name)
        store.add_documents(chunks)
        print(f"{path.name}:{len(pages)} pagine, {len(chunks)} chunk creati e aggiunti alla collection '{COLLECTION_NAME}'")
    print(f"Owner '{owner_id}' indicizzato in '{COLLECTION_NAME}'")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Indicizza i PDF di un owner in Qdrant.")
    parser.add_argument("--owner", required=True)
    parser.add_argument("--dir", type=Path, default=DATA_DIR)
    args = parser.parse_args()
    ingest(args.owner, args.dir)