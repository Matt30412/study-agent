"""Server: FastAPI con login Google (OIDC) e Gradio montato su /chat."""

from contextlib import asynccontextmanager

import gradio as gr
from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.concurrency import run_in_threadpool
from starlette.middleware.sessions import SessionMiddleware

from src.app import demo
from src.config import (
    ALLOWED_EMAILS,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    SESSION_HTTPS_ONLY,
    SESSION_SECRET,
)
from src.users import get_or_create_owner, init_db

if not SESSION_SECRET or not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    raise RuntimeError("Mancano SESSION_SECRET, GOOGLE_CLIENT_ID o GOOGLE_CLIENT_SECRET nel .env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    SessionMiddleware, secret_key=SESSION_SECRET, same_site="lax", https_only=SESSION_HTTPS_ONLY
)

oauth = OAuth()
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    client_kwargs={"scope": "openid email profile", "code_challenge_method": "S256"},
)


def session_owner(request: Request) -> str | None:
    return request.session.get("owner_id")


@app.get("/")
def root(request: Request):
    return RedirectResponse("/chat" if session_owner(request) else "/login")


@app.get("/login")
async def login(request: Request):
    return await oauth.google.authorize_redirect(request, str(request.url_for("auth_callback")))


@app.get("/auth/callback")
async def auth_callback(request: Request):
    try:
        # Scambia il code con i token e valida l'ID token: firma (JWKS), iss, aud, exp, nonce.
        token = await oauth.google.authorize_access_token(request)
    except OAuthError:
        return RedirectResponse("/login")
    claims = token["userinfo"]
    email = (claims.get("email") or "").lower()
    if not claims.get("email_verified") or email not in ALLOWED_EMAILS:
        return HTMLResponse("Account non autorizzato.", status_code=403)
    # psycopg è sincrono: la query gira in un thread, altrimenti blocca l'event loop
    # e con lui tutte le altre richieste in corso.
    owner_id = await run_in_threadpool(get_or_create_owner, claims["iss"], claims["sub"], email)
    request.session["owner_id"] = owner_id
    return RedirectResponse("/chat")


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login")


# Gradio chiama session_owner a ogni richiesta: None -> 401, altrimenti il valore
# finisce in gr.Request.username, che current_owner() già legge.
app = gr.mount_gradio_app(app, demo, path="/chat", auth_dependency=session_owner)
