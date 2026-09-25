from types import SimpleNamespace

import pytest

from src.tenancy import current_owner, load_users, validate_owner_id


@pytest.mark.parametrize("owner_id", ["alice", "user_01", "a-b", "a" * 64])
def test_valid_owner_id(owner_id):
    assert validate_owner_id(owner_id) == owner_id


@pytest.mark.parametrize(
    "owner_id",
    ["", "../bob", "alice/bob", "Alice", "alice\n", "a" * 65, "alice bob", "alice:x", None],
)
def test_invalid_owner_id(owner_id):
    with pytest.raises(ValueError):
        validate_owner_id(owner_id)


def test_current_owner_from_request():
    assert current_owner(SimpleNamespace(username="alice")) == "alice"


def test_current_owner_fails_closed_without_login():
    # Senza utente autenticato si rifiuta: mai un owner di default.
    with pytest.raises(ValueError):
        current_owner(SimpleNamespace(username=None))


def test_load_users():
    assert load_users("matteo:pw1, alice:pw:2") == [("matteo", "pw1"), ("alice", "pw:2")]


@pytest.mark.parametrize("raw", ["", "   ", "matteo", "matteo:", "../bob:pw", "Matteo:pw"])
def test_load_users_rejects(raw):
    with pytest.raises(ValueError):
        load_users(raw)