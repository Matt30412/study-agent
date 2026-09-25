from pathlib import Path
import dotenv
import os
dotenv.load_dotenv()
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
NOTES_DIR = ROOT_DIR / "notes"

# Qdrant
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "study_agent"

# Modelli
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
LLM_MODEL = "qwen2.5:7b"

# Chunking e retrieval
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
RETRIEVER_K = 3

RECURSION_LIMIT = 15

#Google Oauth
ID_CLIENT = os.getenv("id_client")
CLIENT_SECRET = os.getenv("client_secret")