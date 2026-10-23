# backend/auth.py
"""Simple cookie-based login. Credentials come from ENV (USR, PAS).

The session cookie is stateless: "<expiry>.<hmac>" signed with a key derived
from the credentials (or SECRET_KEY if set). Changing USR/PAS/SECRET_KEY
invalidates all existing sessions.
"""
import hashlib
import hmac
import os
import time

COOKIE_NAME = "vocas_session"
COOKIE_MAX_AGE = 365 * 24 * 3600  # 365 days

# Paths reachable without a session
PUBLIC_PATHS = {"/login", "/static/favicon.svg"}


def credentials() -> tuple[str, str]:
    return os.getenv("USR", ""), os.getenv("PAS", "")


def auth_enabled() -> bool:
    usr, pas = credentials()
    return bool(usr and pas)


def _key() -> bytes:
    usr, pas = credentials()
    secret = os.getenv("SECRET_KEY") or f"{usr}:{pas}"
    return hashlib.sha256(f"vocas-session:{secret}".encode()).digest()


def _sign(expiry: str) -> str:
    return hmac.new(_key(), expiry.encode(), hashlib.sha256).hexdigest()


def check_credentials(username: str, password: str) -> bool:
    usr, pas = credentials()
    # Evaluate both comparisons so timing does not reveal which one failed
    user_ok = hmac.compare_digest(username.encode(), usr.encode())
    pass_ok = hmac.compare_digest(password.encode(), pas.encode())
    return user_ok and pass_ok


def make_token() -> str:
    expiry = str(int(time.time()) + COOKIE_MAX_AGE)
    return f"{expiry}.{_sign(expiry)}"


def valid_token(token: str | None) -> bool:
    if not token or "." not in token:
        return False
    expiry, sig = token.split(".", 1)
    if not expiry.isdigit() or int(expiry) < time.time():
        return False
    return hmac.compare_digest(sig, _sign(expiry))


def safe_next(target: str | None) -> str:
    """Allow only local absolute paths (prevents open redirect)."""
    if target and target.startswith("/") and not target.startswith("//") and "\\" not in target:
        return target
    return "/"
