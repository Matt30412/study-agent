import pytest
from authlib.integrations.starlette_client import OAuthError
from fastapi.testclient import TestClient

from src import server

GOOGLE = "https://accounts.google.com"


def _claims(email="alice@example.com", verified=True):
    return {"iss": GOOGLE, "sub": "sub-1", "email": email, "email_verified": verified}


@pytest.fixture
def owners(monkeypatch):
    # Al posto di Postgres: registra le identità per cui il server chiede un owner_id.
    calls = []

    def fake_get_or_create_owner(iss, sub, email):
        calls.append((iss, sub, email))
        return "alice"

    monkeypatch.setattr(server, "get_or_create_owner", fake_get_or_create_owner)
    return calls


@pytest.fixture
def client(monkeypatch, owners):
    monkeypatch.setattr(server, "ALLOWED_EMAILS", {"alice@example.com"})
    return TestClient(server.app, base_url="https://testserver")


@pytest.fixture
def login(client, monkeypatch):
    # Al posto di Google: il callback riceve le claim che decide il test.
    def _login(claims):
        async def fake_authorize_access_token(request):
            return {"userinfo": claims}

        monkeypatch.setattr(
            server.oauth.google, "authorize_access_token", fake_authorize_access_token
        )
        return client.get("/auth/callback", follow_redirects=False)

    return _login


def test_root_without_session_redirects_to_login(client):
    assert client.get("/", follow_redirects=False).headers["location"] == "/login"


def test_chat_requires_session(client):
    # È la garanzia che conta: senza login Gradio non risponde, nemmeno le sue API.
    assert client.get("/chat/").status_code == 401
    assert client.get("/chat/config").status_code == 401


def test_allowed_user_logs_in(client, login, owners):
    r = login(_claims(email="Alice@Example.com"))

    assert r.headers["location"] == "/chat"
    assert "secure" in r.headers["set-cookie"].lower()
    # La chiave dell'identità è (iss, sub), l'email arriva normalizzata.
    assert owners == [(GOOGLE, "sub-1", "alice@example.com")]
    assert client.get("/chat/").status_code == 200


def test_unverified_email_is_rejected(client, login, owners):
    assert login(_claims(verified=False)).status_code == 403
    assert owners == []
    assert client.get("/chat/").status_code == 401


def test_email_not_in_allowlist_is_rejected(client, login, owners):
    assert login(_claims(email="mallory@example.com")).status_code == 403
    assert owners == []
    assert client.get("/chat/").status_code == 401


def test_empty_allowlist_rejects_everyone(login, monkeypatch):
    # Fail-closed: un ALLOWED_EMAILS dimenticato non apre l'app a qualsiasi account Google.
    monkeypatch.setattr(server, "ALLOWED_EMAILS", set())

    assert login(_claims()).status_code == 403


def test_oauth_error_restarts_login(client, monkeypatch, owners):
    async def failing_authorize_access_token(request):
        raise OAuthError(error="mismatching_state")

    monkeypatch.setattr(
        server.oauth.google, "authorize_access_token", failing_authorize_access_token
    )

    assert client.get("/auth/callback", follow_redirects=False).headers["location"] == "/login"
    assert owners == []


def test_logout_clears_session(client, login):
    login(_claims())
    assert client.get("/chat/").status_code == 200

    client.get("/logout", follow_redirects=False)

    assert client.get("/chat/").status_code == 401
