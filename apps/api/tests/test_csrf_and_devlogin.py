"""Origin-based CSRF protection and the guarded local-only dev login."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, settings
from app.main import app


def _no_origin_client(signed_in):
    c = TestClient(app)  # no Origin header at all
    c.cookies.set(settings.session_cookie_name, signed_in.cookies[settings.session_cookie_name])
    return c


@pytest.mark.parametrize("origin", ["https://evil.example", "null", "http://localhost:3001"])
def test_state_changing_request_from_foreign_origin_is_blocked(signed_in, origin):
    r = signed_in.patch("/api/v1/profiles/me", json={"branch": "CSE"}, headers={"Origin": origin})
    assert r.status_code == 403
    assert signed_in.get("/api/v1/auth/me").json()["profile"]["branch"] is None  # unchanged


def test_logout_from_foreign_origin_is_blocked_and_session_survives(signed_in):
    assert (
        signed_in.post(
            "/api/v1/auth/logout", headers={"Origin": "https://evil.example"}
        ).status_code
        == 403
    )
    assert signed_in.get("/api/v1/auth/me").status_code == 200


def test_missing_origin_and_referer_is_blocked_when_cookie_present(signed_in):
    c = _no_origin_client(signed_in)
    assert c.patch("/api/v1/profiles/me", json={"branch": "CSE"}).status_code == 403


def test_referer_is_accepted_as_a_fallback(signed_in):
    c = _no_origin_client(signed_in)
    r = c.patch(
        "/api/v1/profiles/me",
        json={"branch": "CSE"},
        headers={"Referer": "http://localhost:3000/me/edit"},
    )
    assert r.status_code == 200


def test_safe_methods_are_not_restricted(signed_in):
    assert (
        signed_in.get("/api/v1/auth/me", headers={"Origin": "https://evil.example"}).status_code
        == 200
    )


# ------------------------------------------------------------------ dev login
def test_dev_login_is_404_by_default(client):
    r = client.post("/api/v1/auth/dev-login", json={"email": "x@iiitr.ac.in"})
    assert r.status_code == 404
    assert settings.session_cookie_name not in client.cookies


def test_dev_login_works_locally_when_enabled_and_uses_the_allowlist(client, monkeypatch):
    monkeypatch.setattr(settings, "dev_login_enabled", True)

    ok = client.post("/api/v1/auth/dev-login", json={"email": "dev@iiitr.ac.in", "name": "Dev"})
    assert ok.status_code == 200 and ok.json() == {"redirect": "/onboarding"}
    assert client.get("/api/v1/auth/me").json()["email"] == "dev@iiitr.ac.in"

    blocked = client.post("/api/v1/auth/dev-login", json={"email": "dev@gmail.com"})
    assert blocked.status_code == 403 and blocked.json() == {"error": "domain_not_allowed"}


def test_dev_login_is_inactive_outside_local_even_if_flag_set(monkeypatch, client):
    monkeypatch.setattr(settings, "dev_login_enabled", True)
    monkeypatch.setattr(settings, "environment", "staging")
    assert client.post("/api/v1/auth/dev-login", json={"email": "d@iiitr.ac.in"}).status_code == 404


def test_app_refuses_to_start_with_dev_login_outside_local():
    with pytest.raises(ValueError, match="DEV_LOGIN_ENABLED"):
        Settings(
            _env_file=None,
            environment="production",
            dev_login_enabled=True,
            secret_key="x" * 40,
            frontend_url="https://app.example.com",
            google_client_id="id",
            google_client_secret="secret",
            allowed_email_domains="iiitr.ac.in",
        )
