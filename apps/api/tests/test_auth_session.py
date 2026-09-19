"""Sessions: protected routes, expiry, tampering, and server-side logout."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select, text

from app.core.config import settings
from app.modules.auth.models import UserSession
from tests.conftest import claims

COOKIE = settings.session_cookie_name


def test_protected_routes_require_a_session(client):
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/profiles/me").status_code == 401
    assert client.patch("/api/v1/profiles/me", json={"branch": "CSE"}).status_code == 401


def test_garbage_and_tampered_cookies_are_rejected(signed_in, make_client):
    real = signed_in.cookies[COOKIE]
    for bad in ["garbage", real[:-1] + ("A" if real[-1] != "A" else "B"), "", real + "x"]:
        c = make_client()
        c.cookies.set(COOKIE, bad)
        assert c.get("/api/v1/auth/me").status_code == 401, bad


def test_me_returns_user_college_and_profile_state(signed_in):
    r = signed_in.get("/api/v1/auth/me")
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "asha@iiitr.ac.in"
    assert body["college"]["slug"] == "iiit-raichur"
    assert body["onboarding_completed"] is False
    assert body["profile"]["branch"] is None
    assert body["role"] == "student"


def test_expired_session_is_rejected(signed_in, db):
    db.execute(text("UPDATE sessions SET expires_at = now() - interval '1 second'"))
    db.commit()
    assert signed_in.get("/api/v1/auth/me").status_code == 401


def test_logout_revokes_the_session_server_side(signed_in, db):
    old_cookie = signed_in.cookies[COOKIE]

    r = signed_in.post("/api/v1/auth/logout")
    assert r.status_code == 204
    assert db.scalar(select(func.count()).select_from(UserSession)) == 0
    assert signed_in.get("/api/v1/auth/me").status_code == 401

    # Replaying the OLD cookie value must fail: revocation is server-side, not just cookie removal.
    signed_in.cookies.set(COOKIE, old_cookie)
    assert signed_in.get("/api/v1/auth/me").status_code == 401


def test_logout_only_ends_the_current_session(client, make_client, google_sign_in, db):
    other = make_client()
    google_sign_in(client, claims())
    google_sign_in(other, claims())  # same user, second device
    assert db.scalar(select(func.count()).select_from(UserSession)) == 2

    client.post("/api/v1/auth/logout")
    assert client.get("/api/v1/auth/me").status_code == 401
    assert other.get("/api/v1/auth/me").status_code == 200


def test_logout_without_session_is_a_noop(client):
    assert client.post("/api/v1/auth/logout").status_code == 204


def test_session_of_deleted_user_stops_working(signed_in, db):
    db.execute(text("UPDATE users SET deleted_at = now()"))
    db.commit()
    assert signed_in.get("/api/v1/auth/me").status_code == 401


def test_last_seen_is_refreshed_but_not_on_every_request(signed_in, db):
    old = datetime.now(UTC) - timedelta(hours=1)
    db.execute(text("UPDATE sessions SET last_seen_at = :t"), {"t": old})
    db.commit()

    signed_in.get("/api/v1/auth/me")
    db.expire_all()
    refreshed = db.scalar(select(UserSession.last_seen_at))
    assert refreshed > old + timedelta(minutes=30)

    signed_in.get("/api/v1/auth/me")
    db.expire_all()
    assert db.scalar(select(UserSession.last_seen_at)) == refreshed  # within throttle window
