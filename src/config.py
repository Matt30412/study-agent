import os
from pathlib import Path

import dotenv

dotenv.load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
NOTES_DIR = ROOT_DIR / "notes"

# Servizi: i default sono quelli di docker-compose.yml, l'env li sovrascrive (es. in un container).
# L'host di Ollama non è qui: lo legge direttamente il client ollama da OLLAMA_HOST.
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://study_agent:study_agent@localhost:5432/study_agent"
)
COLLECTION_NAME = "study_agent"

# Modelli
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
LLM_MODEL = "qwen2.5:7b"

# Chunking e retrieval
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
RETRIEVER_K = 3

RECURSION_LIMIT = 15

# Modalità dev (python -m src.app): utenti locali "nome:password,nome:password", senza Google.
APP_USERS = os.getenv("APP_USERS", "")

# Google OIDC (python -m uvicorn src.server:app)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
# Vuoto = non entra nessuno: l'accesso fallisce chiuso.
ALLOWED_EMAILS = {
    e.strip().lower() for e in os.getenv("ALLOWED_EMAILS", "").split(",") if e.strip()
}
SESSION_SECRET = os.getenv("SESSION_SECRET")
# Default sicuro: solo un "false" esplicito (sviluppo su http://localhost) toglie il flag Secure
# al cookie di sessione. Dimenticarsi la variabile in produzione non lo espone su HTTP.
SESSION_HTTPS_ONLY = os.getenv("SESSION_HTTPS_ONLY", "true").strip().lower() != "false"
