"""Test setup.

Tests run against a REAL PostgreSQL database (TEST_DATABASE_URL, must end in `_test`) with the
schema built by running the Alembic migrations from scratch, so migrations are exercised too.
"""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import AsyncMock

# --- Environment must be fixed BEFORE the app (and its settings) are imported. -------------
_DEFAULT_TEST_DB = "postgresql+psycopg://builderhub:builderhub_dev@localhost:5432/builderhub_test"
_test_db = os.environ.get("TEST_DATABASE_URL") or _DEFAULT_TEST_DB
if not _test_db.rsplit("/", 1)[-1].split("?")[0].endswith("_test"):
    raise RuntimeError(f"Refusing to run tests: TEST_DATABASE_URL must end in '_test' ({_test_db})")

os.environ.update(
    {
        "DATABASE_URL": _test_db,
        "ENVIRONMENT": "local",
        "FRONTEND_URL": "http://localhost:3000",
        "GOOGLE_CLIENT_ID": "test-client-id",
        "GOOGLE_CLIENT_SECRET": "test-client-secret",
        "GOOGLE_REQUIRE_HD": "false",
        "ALLOWED_EMAIL_DOMAINS": "iiitr.ac.in",
        "ALLOWED_TEST_EMAILS": "",
        "DEV_LOGIN_ENABLED": "false",
        "SENTRY_DSN": "",
    }
)

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.db import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.modules.auth.oauth import oauth  # noqa: E402

FRONTEND = "http://localhost:3000"


def alembic_config() -> Config:
    cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    cfg.set_main_option(
        "script_location", os.path.join(os.path.dirname(__file__), "..", "migrations")
    )
    return cfg


@pytest.fixture(scope="session", autouse=True)
def _database() -> None:
    """Rebuild the schema from scratch via migrations once per test session."""
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    command.upgrade(alembic_config(), "head")


@pytest.fixture(autouse=True)
def _clean_tables() -> None:
    """Empty per-test data. `colleges` keeps its migration seed."""
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE sessions, oauth_accounts, profiles, users CASCADE"))


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


@pytest.fixture
def client() -> TestClient:
    """A browser-like client: always sends the legitimate Origin header."""
    return TestClient(app, headers={"Origin": FRONTEND})


@pytest.fixture
def make_client():
    """Factory for extra independent clients (own cookie jar), e.g. a second user."""
    return lambda: TestClient(app, headers={"Origin": FRONTEND})


def claims(
    email: str = "asha@iiitr.ac.in", sub: str = "google-sub-1", verified: bool = True, **extra: Any
) -> dict[str, Any]:
    return {
        "sub": sub,
        "email": email,
        "email_verified": verified,
        "name": "Asha Rao",
        "picture": "https://lh3.googleusercontent.com/a/photo",
        **extra,
    }


@pytest.fixture
def google_sign_in(monkeypatch):
    """Drive the REAL callback route with Google's token exchange mocked out.

    Usage: resp = google_sign_in(client, claims(email=...))
    """

    def _sign_in(test_client: TestClient, id_claims: dict[str, Any]):
        monkeypatch.setattr(
            oauth.google,
            "authorize_access_token",
            AsyncMock(return_value={"userinfo": id_claims}),
        )
        return test_client.get(
            "/api/v1/auth/google/callback?code=fake&state=fake", follow_redirects=False
        )

    return _sign_in


@pytest.fixture
def signed_in(client, google_sign_in):
    """A client already signed in as an allowed IIIT Raichur user (onboarding NOT completed)."""
    resp = google_sign_in(client, claims())
    assert resp.status_code == 303 and settings.session_cookie_name in client.cookies
    return client
