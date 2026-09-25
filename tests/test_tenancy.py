import pytest

from src.tenancy import validate_owner_id


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