"""Ingestion: PDF -> chunk -> embedding -> Qdrant."""

import argparse
from pathlib import Path

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from qdrant_client import QdrantClient, models

from src.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    COLLECTION_NAME,
    DATA_DIR,
    EMBEDDING_MODEL,
    QDRANT_URL,
)
from src.tenancy import validate_owner_id

SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def load_pdf(path: Path) -> list[Document]:
    # Stesso testo e stessi numeri di pagina di PyPDFLoader (langchain-community è in dismissione),
    # verificato sui PDF del corso: i chunk non cambiano e i numeri dell'eval restano validi.
    reader = PdfReader(path)
    return [
        Document(
            page_content=page.extract_text().strip(),
            metadata={
                "source": str(path),
                "source_file": path.name,
                "page": i,  # 0-indexed
                "page_label": reader.page_labels[i],  # quello stampato sulla slide, usato dall'eval
                "total_pages": len(reader.pages),
            },
        )
        for i, page in enumerate(reader.pages)
    ]


def ensure_collection(client: QdrantClient, dim: int) -> None:
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
        )

    client.create_payload_index(
        COLLECTION_NAME,
        field_name="metadata.owner_id",
        field_schema=models.KeywordIndexParams(type="keyword", is_tenant=True),
    )


def delete_file_chunks(client: QdrantClient, owner_id: str, source_file: str) -> None:
    client.delete(
        COLLECTION_NAME,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.owner_id", match=models.MatchValue(value=owner_id)
                    ),
                    models.FieldCondition(
                        key="metadata.source_file", match=models.MatchValue(value=source_file)
                    ),
                ]
            )
        ),
    )


def ingest(owner_id: str, data_dir: Path) -> None:
    owner_id = validate_owner_id(owner_id)
    pdfs = sorted(data_dir.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"Nessun PDF in {data_dir.resolve()}")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    client = QdrantClient(url=QDRANT_URL)
    ensure_collection(client, dim=len(embeddings.embed_query("dim")))
    store = QdrantVectorStore(client=client, collection_name=COLLECTION_NAME, embedding=embeddings)

    for path in pdfs:
        pages = load_pdf(path)
        for p in pages:
            p.metadata["owner_id"] = owner_id
        chunks = SPLITTER.split_documents(pages)
        delete_file_chunks(client, owner_id, path.name)
        store.add_documents(chunks)
        print(
            f"{path.name}: {len(pages)} pagine, {len(chunks)} chunk creati e aggiunti "
            f"alla collection '{COLLECTION_NAME}'"
        )
    print(f"Owner '{owner_id}' indicizzato in '{COLLECTION_NAME}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Indicizza i PDF di un owner in Qdrant.")
    parser.add_argument("--owner", required=True)
    parser.add_argument("--dir", type=Path, default=DATA_DIR)
    args = parser.parse_args()
    ingest(args.owner, args.dir)
