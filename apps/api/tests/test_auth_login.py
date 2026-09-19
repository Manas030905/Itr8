"""Google callback behaviour: who gets in, who doesn't, and what gets stored."""

import hashlib

import pytest
from sqlalchemy import func, select, text

from app.core.config import settings
from app.modules.auth.models import UserSession
from app.modules.profiles.models import Profile
from app.modules.users.models import OAuthAccount, User
from tests.conftest import FRONTEND, claims


def _location(resp) -> str:
    return resp.headers["location"]


def _user_count(db) -> int:
    return db.scalar(select(func.count()).select_from(User))


# ---------------------------------------------------------------- allowed
def test_allowed_domain_creates_user_profile_and_session(client, db, google_sign_in):
    resp = google_sign_in(client, claims())

    assert resp.status_code == 303
    assert _location(resp) == f"{FRONTEND}/onboarding"  # first login -> onboarding
    assert settings.session_cookie_name in client.cookies

    user = db.scalar(select(User).where(User.email == "asha@iiitr.ac.in"))
    assert user is not None and user.name == "Asha Rao" and user.role == "student"
    assert db.scalar(select(func.count()).select_from(Profile)) == 1
    assert db.scalar(select(func.count()).select_from(OAuthAccount)) == 1


def test_session_cookie_flags(client, google_sign_in):
    resp = google_sign_in(client, claims())
    set_cookie = resp.headers["set-cookie"].lower()
    assert set_cookie.startswith(f"{settings.session_cookie_name}=")
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie
    assert "path=/" in set_cookie
    assert "max-age=" in set_cookie
    # Local dev is plain http, so Secure is intentionally off here (on everywhere else).
    assert settings.cookie_secure is False


def test_only_a_hash_of_the_session_token_is_stored(client, db, google_sign_in):
    google_sign_in(client, claims())
    raw = client.cookies[settings.session_cookie_name]

    stored = db.scalar(select(UserSession.token_hash))
    assert stored == hashlib.sha256(raw.encode()).hexdigest()
    assert stored != raw
    assert (
        db.scalar(
            select(func.count()).select_from(UserSession).where(text(f"token_hash = '{raw}'"))
        )
        == 0
    )


def test_email_is_normalised_to_lowercase(client, db, google_sign_in):
    resp = google_sign_in(client, claims(email="Asha.Rao@IIITR.AC.IN"))
    assert resp.status_code == 303
    assert db.scalar(select(User.email)) == "asha.rao@iiitr.ac.in"


def test_returning_user_is_reused_and_completed_user_goes_to_me(client, db, google_sign_in):
    google_sign_in(client, claims())
    client.patch("/api/v1/profiles/me", json={"branch": "CSE", "year": 2})  # completes onboarding

    second = google_sign_in(client, claims())
    assert _location(second) == f"{FRONTEND}/me"
    assert _user_count(db) == 1
    assert db.scalar(select(func.count()).select_from(UserSession)) == 2


def test_next_param_is_honoured_for_completed_users_only_if_safe(client, google_sign_in):
    google_sign_in(client, claims())
    client.patch("/api/v1/profiles/me", json={"branch": "CSE", "year": 2})

    client.get("/api/v1/auth/google/login?next=/me/edit", follow_redirects=False)
    assert _location(google_sign_in(client, claims())) == f"{FRONTEND}/me/edit"

    client.get("/api/v1/auth/google/login?next=https://evil.com", follow_redirects=False)
    assert _location(google_sign_in(client, claims())) == f"{FRONTEND}/me"

    client.get("/api/v1/auth/google/login?next=//evil.com", follow_redirects=False)
    assert _location(google_sign_in(client, claims())) == f"{FRONTEND}/me"


# ---------------------------------------------------------------- refused
@pytest.mark.parametrize(
    "email",
    [
        "someone@gmail.com",
        "asha@iiitr.ac.in.evil.com",  # suffix trick
        "asha@notiiitr.ac.in",  # prefix trick
        "asha@evil-iiitr.ac.in",
        "asha@students.iiitr.ac.in",  # subdomains are NOT auto-allowed (ADR-005)
        "asha@iiitr.ac.in@evil.com",
        "asha@iiit.ac.in",  # a different IIIT
    ],
)
def test_disallowed_domains_are_refused(client, db, google_sign_in, email):
    resp = google_sign_in(client, claims(email=email))

    assert resp.status_code == 303
    assert _location(resp) == f"{FRONTEND}/login?error=domain_not_allowed"
    assert settings.session_cookie_name not in client.cookies
    assert _user_count(db) == 0
    assert db.scalar(select(func.count()).select_from(UserSession)) == 0


def test_unverified_email_is_refused(client, db, google_sign_in):
    resp = google_sign_in(client, claims(verified=False))
    assert _location(resp) == f"{FRONTEND}/login?error=email_not_verified"
    assert _user_count(db) == 0


def test_string_false_for_email_verified_is_refused(client, google_sign_in):
    resp = google_sign_in(client, {**claims(), "email_verified": "false"})
    assert _location(resp) == f"{FRONTEND}/login?error=email_not_verified"


@pytest.mark.parametrize("bad", [{"sub": ""}, {"email": ""}, {"email": "no-at-sign"}])
def test_malformed_claims_are_refused(client, db, google_sign_in, bad):
    resp = google_sign_in(client, {**claims(), **bad})
    assert _location(resp) == f"{FRONTEND}/login?error=oauth_failed"
    assert _user_count(db) == 0


def test_soft_deleted_user_cannot_sign_in(client, db, google_sign_in):
    google_sign_in(client, claims())
    db.execute(text("UPDATE users SET deleted_at = now()"))
    db.commit()
    client.cookies.clear()

    resp = google_sign_in(client, claims())
    assert _location(resp) == f"{FRONTEND}/login?error=account_disabled"
    assert settings.session_cookie_name not in client.cookies


def test_email_reused_by_a_different_google_account_is_refused(client, db, google_sign_in):
    google_sign_in(client, claims(sub="original-owner"))
    client.cookies.clear()

    resp = google_sign_in(client, claims(sub="someone-else"))
    assert _location(resp) == f"{FRONTEND}/login?error=account_conflict"
    assert db.scalar(select(func.count()).select_from(OAuthAccount)) == 1
    assert settings.session_cookie_name not in client.cookies


# ---------------------------------------------------------------- test-email allowlist + hd
def test_allowed_test_emails_admit_named_addresses_only(client, google_sign_in, monkeypatch):
    monkeypatch.setattr(settings, "allowed_test_emails", "founder@gmail.com, Other@Gmail.com")

    ok = google_sign_in(client, claims(email="founder@gmail.com", sub="s1"))
    assert _location(ok) == f"{FRONTEND}/onboarding"
    ok2 = google_sign_in(client, claims(email="other@gmail.com", sub="s2"))
    assert _location(ok2) == f"{FRONTEND}/onboarding"

    other = google_sign_in(client, claims(email="stranger@gmail.com", sub="s3"))
    assert _location(other) == f"{FRONTEND}/login?error=domain_not_allowed"


def test_require_hd_flag(client, google_sign_in, monkeypatch):
    monkeypatch.setattr(settings, "google_require_hd", True)

    no_hd = google_sign_in(client, claims())
    assert _location(no_hd) == f"{FRONTEND}/login?error=domain_not_allowed"

    wrong_hd = google_sign_in(client, claims(hd="evil.com"))
    assert _location(wrong_hd) == f"{FRONTEND}/login?error=domain_not_allowed"

    good = google_sign_in(client, claims(hd="iiitr.ac.in"))
    assert _location(good) == f"{FRONTEND}/onboarding"


# ---------------------------------------------------------------- Google-side failures
def test_user_cancelling_on_google_is_reported_as_cancelled(client):
    # Real Authlib code path: Google redirects back with ?error=access_denied.
    resp = client.get("/api/v1/auth/google/callback?error=access_denied", follow_redirects=False)
    assert _location(resp) == f"{FRONTEND}/login?error=cancelled"
    assert settings.session_cookie_name not in client.cookies


def test_callback_with_unknown_state_is_rejected(client):
    # No prior /login => no stored state => Authlib must refuse (CSRF on the OAuth flow).
    resp = client.get("/api/v1/auth/google/callback?code=abc&state=forged", follow_redirects=False)
    assert _location(resp) == f"{FRONTEND}/login?error=oauth_failed"
    assert settings.session_cookie_name not in client.cookies


def test_google_not_configured_redirects_with_clear_error(client, monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "")
    resp = client.get("/api/v1/auth/google/login", follow_redirects=False)
    assert _location(resp) == f"{FRONTEND}/login?error=not_configured"


# ---------------------------------------------------------------- configurable domains
def test_additional_domains_can_be_enabled_purely_by_configuration(
    client, google_sign_in, monkeypatch
):
    students = claims(email="council@students.iiitr.ac.in", sub="s-council")
    assert (
        _location(google_sign_in(client, students)) == f"{FRONTEND}/login?error=domain_not_allowed"
    )

    monkeypatch.setattr(settings, "allowed_email_domains", "iiitr.ac.in, students.iiitr.ac.in")
    assert _location(google_sign_in(client, students)) == f"{FRONTEND}/onboarding"
    # the original domain still works, and an unrelated one still doesn't
    assert _location(google_sign_in(client, claims(sub="s-2"))) == f"{FRONTEND}/onboarding"
    other = claims(email="x@gmail.com", sub="s-3")
    assert _location(google_sign_in(client, other)) == f"{FRONTEND}/login?error=domain_not_allowed"


def test_no_configured_domains_means_nobody_can_sign_in(client, db, google_sign_in, monkeypatch):
    monkeypatch.setattr(settings, "allowed_email_domains", "")
    resp = google_sign_in(client, claims())
    assert _location(resp) == f"{FRONTEND}/login?error=domain_not_allowed"
    assert _user_count(db) == 0


def test_missing_default_college_row_fails_closed(client, db, google_sign_in, monkeypatch):
    monkeypatch.setattr(settings, "default_college_slug", "no-such-college")
    resp = google_sign_in(client, claims())
    assert _location(resp) == f"{FRONTEND}/login?error=oauth_failed"
    assert _user_count(db) == 0
