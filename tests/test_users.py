import os

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from src.tenancy import validate_owner_id
from src.users import get_or_create_owner, init_db, link_email_to_owner

GOOGLE = "https://accounts.google.com"

# Un database separato da quello dell'app, perché i test lo svuotano.
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql://study_agent:study_agent@localhost:5432/study_agent_test"
)


@pytest.fixture(scope="module")
def database():
    name = conninfo_to_dict(TEST_DATABASE_URL)["dbname"]
    try:
        # CREATE DATABASE non può stare in una transazione: serve autocommit.
        admin = make_conninfo(TEST_DATABASE_URL, dbname="postgres", connect_timeout=3)
        with psycopg.connect(admin, autocommit=True) as conn:
            if not conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,)).fetchone():
                conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    except psycopg.OperationalError:
        pytest.skip("Postgres non raggiungibile: docker compose up -d postgres")
    init_db(TEST_DATABASE_URL)
    return TEST_DATABASE_URL


@pytest.fixture
def db(database):
    with psycopg.connect(database) as conn:
        conn.execute("TRUNCATE identities")
    return database


def test_same_identity_same_owner(db):
    first = get_or_create_owner(GOOGLE, "sub-1", "a@example.com", database_url=db)
    assert get_or_create_owner(GOOGLE, "sub-1", "a@example.com", database_url=db) == first
    assert validate_owner_id(first) == first


def test_different_sub_different_owner(db):
    a = get_or_create_owner(GOOGLE, "sub-1", "a@example.com", database_url=db)
    b = get_or_create_owner(GOOGLE, "sub-2", "b@example.com", database_url=db)
    assert a != b


def test_same_sub_different_issuer_different_owner(db):
    # sub è unico solo dentro il suo provider: la chiave è la coppia (iss, sub).
    microsoft = "https://login.microsoftonline.com/x/v2.0"
    a = get_or_create_owner(GOOGLE, "sub-1", "a@example.com", database_url=db)
    b = get_or_create_owner(microsoft, "sub-1", "a@example.com", database_url=db)
    assert a != b


def test_link_moves_identity_to_existing_owner(db):
    get_or_create_owner(GOOGLE, "sub-1", "a@example.com", database_url=db)
    assert link_email_to_owner("A@example.com", "matteo", database_url=db) == 1
    assert get_or_create_owner(GOOGLE, "sub-1", "a@example.com", database_url=db) == "matteo"


def test_link_rejects_invalid_owner(db):
    with pytest.raises(ValueError):
        link_email_to_owner("a@example.com", "../bob", database_url=db)


def test_init_db_is_idempotent(db):
    # Gira a ogni avvio del server: la seconda volta non deve fallire né perdere dati.
    owner = get_or_create_owner(GOOGLE, "sub-1", "a@example.com", database_url=db)
    init_db(db)
    assert get_or_create_owner(GOOGLE, "sub-1", "a@example.com", database_url=db) == owner
