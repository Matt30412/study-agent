"""Identità esterne (iss, sub) -> owner_id interno, su PostgreSQL."""

import argparse
import secrets

import psycopg

from src.config import DATABASE_URL
from src.tenancy import validate_owner_id


def init_db(database_url: str = DATABASE_URL) -> None:
    """Crea la tabella delle identità se manca. Si chiama all'avvio, non a ogni login."""
    with psycopg.connect(database_url) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS identities (
                iss      TEXT NOT NULL,
                sub      TEXT NOT NULL,
                email    TEXT,
                owner_id TEXT NOT NULL,
                PRIMARY KEY (iss, sub)
            )""")


def get_or_create_owner(iss: str, sub: str, email: str, database_url: str = DATABASE_URL) -> str:
    """Recupera o crea un owner_id per l'identità (iss, sub)."""
    # "with connect" fa commit all'uscita (rollback se c'è un'eccezione) e chiude la connessione.
    with psycopg.connect(database_url) as conn:
        # ON CONFLICT DO NOTHING + SELECT invece di SELECT + INSERT: due primi login simultanei
        # dello stesso utente non vanno in conflitto sulla chiave. In READ COMMITTED (il default)
        # la SELECT è un nuovo snapshot e vede anche la riga appena inserita dall'altro login.
        conn.execute(
            "INSERT INTO identities (iss, sub, email, owner_id) VALUES (%s, %s, %s, %s)"
            " ON CONFLICT (iss, sub) DO NOTHING",
            (iss, sub, email, "u_" + secrets.token_hex(8)),
        )
        row = conn.execute(
            "SELECT owner_id FROM identities WHERE iss = %s AND sub = %s", (iss, sub)
        ).fetchone()
        return row[0]


def link_email_to_owner(email: str, owner_id: str, database_url: str = DATABASE_URL) -> int:
    """Associa a owner_id le identità già registrate con questa email. Restituisce quante."""
    owner_id = validate_owner_id(owner_id)
    with psycopg.connect(database_url) as conn:
        cur = conn.execute(
            "UPDATE identities SET owner_id = %s WHERE lower(email) = lower(%s)", (owner_id, email)
        )
        return cur.rowcount


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gestione delle identità utente.")
    sub = parser.add_subparsers(dest="command", required=True)
    link = sub.add_parser("link", help="associa un account (per email) a un owner esistente")
    link.add_argument("--email", required=True)
    link.add_argument("--owner", required=True)
    args = parser.parse_args()

    init_db()
    n = link_email_to_owner(args.email, args.owner)
    if n == 0:
        print(f"Nessuna identità con email {args.email}: fai prima un login con quell'account.")
    else:
        print(f"{n} identità associate a '{args.owner}'. Fai logout e rientra.")
