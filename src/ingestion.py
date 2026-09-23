"""Ingestion: PDF -> chunk -> embedding -> Qdrant."""

from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from src.config import CHUNK_OVERLAP, DATA_DIR, COLLECTION_NAME, EMBEDDING_MODEL, QDRANT_URL,CHUNK_SIZE


def main():
    pdfs = list(DATA_DIR.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"Nessun PDF in {DATA_DIR.resolve()}")

    docs = []
    for path in pdfs:
        pages = PyPDFLoader(str(path)).load()
        for p in pages:
            p.metadata["source_file"] = path.name
        docs.extend(pages)
        print(f"  {path.name}: {len(pages)} pagine")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    print(f"{len(chunks)} chunk creati")

    QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL),
        url=QDRANT_URL,
        collection_name=COLLECTION_NAME,
        force_recreate=True,
    )
    print(f"Collection '{COLLECTION_NAME}' pronta")


if __name__ == "__main__":
    main()