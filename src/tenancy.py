import re



OWNER_ID_PATTERN = re.compile(r"^[a-z0-9_-]{1,64}$")


def validate_owner_id(owner_id: str)-> str:
    if not isinstance(owner_id, str) or not OWNER_ID_PATTERN.fullmatch(owner_id):
        raise ValueError(f"owner_id non valido: {owner_id!r}")
    return owner_id


def current_owner(request) -> str:
    # Fase 1: utente autenticato dall'auth di Gradio. In Fase 2 qui si legge il sub del token Google.
    return validate_owner_id(getattr(request, "username", None))


def load_users(raw: str) -> list[tuple[str, str]]:
    if not raw.strip():
        raise ValueError("APP_USERS è vuoto: l'app non parte senza utenti")
    users = []
    for entry in raw.split(","):
        name, sep, password = entry.strip().partition(":")
        if not sep or not password:
            raise ValueError(f"voce APP_USERS senza password per {name!r}: formato nome:password")
        users.append((validate_owner_id(name), password))
    return users
