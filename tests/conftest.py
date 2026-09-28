import os

# Valori finti impostati prima che qualsiasi test importi src.config: i test non devono
# dipendere dal .env locale (e in CI non c'è). load_dotenv() non sovrascrive l'env esistente.
os.environ.update(
    {
        "GOOGLE_CLIENT_ID": "test-client-id",
        "GOOGLE_CLIENT_SECRET": "test-client-secret",
        "SESSION_SECRET": "test-session-secret",
        "SESSION_HTTPS_ONLY": "true",
    }
)
