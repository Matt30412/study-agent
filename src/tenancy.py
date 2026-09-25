import re



OWNER_ID_PATTERN = re.compile(r"^[a-z0-9_-]{1,64}$")


def validate_owner_id(owner_id: str)-> str:
    if not isinstance(owner_id, str) or not OWNER_ID_PATTERN.fullmatch(owner_id):
        raise ValueError("owner_id must be a string")
    return owner_id