"""Login and session logic. No HTTP concerns in here (those live in router.py)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings
from app.core.security import (
    email_domain,
    generate_token,
    hash_token,
    normalize_email,
)
from app.modules.auth.models import UserSession
from app.modules.profiles.models import Profile
from app.modules.users.models import College, OAuthAccount, User

logger = logging.getLogger(__name__)

LAST_SEEN_REFRESH = timedelta(minutes=5)


class LoginError(Exception):
    """Login was refused. `code` is shown to the user via /login?error=<code>."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class LoginResult:
    user_id: Any
    session_token: str
    onboarding_completed: bool


def _is_true(value: Any) -> bool:
    return value is True or (isinstance(value, str) and value.lower() == "true")


def is_email_allowed(email: str, settings: Settings) -> bool:
    """True if the email's domain is in ALLOWED_EMAIL_DOMAINS (exact match) or the exact
    address is in ALLOWED_TEST_EMAILS."""
    return (
        email_domain(email) in settings.allowed_email_domains_list
        or email in settings.allowed_test_emails_list
    )


def get_default_college(db: Session, settings: Settings) -> College | None:
    """Every allowed domain maps to the default college until a second college exists (ADR-015)."""
    return db.scalar(select(College).where(College.slug == settings.default_college_slug))


def _clean_avatar(url: Any) -> str | None:
    return url[:500] if isinstance(url, str) and url.startswith("https://") else None


def _clean_name(name: Any, email: str) -> str:
    candidate = " ".join(str(name).split()) if name else ""
    return (candidate or email.split("@")[0])[:100]


def login_with_google(
    db: Session, claims: dict[str, Any], settings: Settings, *, _retried: bool = False
) -> LoginResult:
    """Validate Google ID-token claims against the allowlist and start a session.

    Raises LoginError (with a user-facing code) if the login must be refused.
    """
    sub = str(claims.get("sub") or "")
    email = normalize_email(str(claims.get("email") or ""))
    if not sub or "@" not in email:
        raise LoginError("oauth_failed")
    if not _is_true(claims.get("email_verified")):
        raise LoginError("email_not_verified")

    domain = email_domain(email)
    is_test_email = email in settings.allowed_test_emails_list
    if (
        settings.google_require_hd
        and not is_test_email
        and str(claims.get("hd") or "").lower() != domain
    ):
        raise LoginError("domain_not_allowed")

    if not is_email_allowed(email, settings):
        logger.info("Login refused: domain %r not allowed", domain)
        raise LoginError("domain_not_allowed")
    college = get_default_college(db, settings)
    if college is None:
        logger.error(
            "DEFAULT_COLLEGE_SLUG=%r does not match any college row", settings.default_college_slug
        )
        raise LoginError("oauth_failed")

    try:
        user = _get_or_create_user(db, sub=sub, email=email, claims=claims, college=college)
        raw_token = _create_session(db, user.id, settings)
        onboarding_completed = bool(
            db.scalar(select(Profile.onboarding_completed_at).where(Profile.user_id == user.id))
        )
        db.commit()
    except IntegrityError:
        # Two first-time logins racing each other: the loser retries exactly once and then
        # finds the winner's rows. Any second failure is a genuine error.
        db.rollback()
        if _retried:
            raise LoginError("oauth_failed") from None
        return login_with_google(db, claims, settings, _retried=True)
    return LoginResult(user.id, raw_token, onboarding_completed)


def _get_or_create_user(
    db: Session, *, sub: str, email: str, claims: dict[str, Any], college: College
) -> User:
    account = db.scalar(
        select(OAuthAccount).where(
            OAuthAccount.provider == "google", OAuthAccount.provider_user_id == sub
        )
    )
    if account is not None:
        user = db.get(User, account.user_id)
        assert user is not None  # FK guarantees this
    else:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(
                email=email,
                name=_clean_name(claims.get("name"), email),
                avatar_url=_clean_avatar(claims.get("picture")),
                college_id=college.id,
            )
            db.add(user)
            db.flush()
            db.add(Profile(user_id=user.id))
        else:
            if user.deleted_at is not None:
                raise LoginError("account_disabled")
            # The email already belongs to a user. If that user is linked to a *different*
            # Google account, refuse rather than hand the account to whoever now owns the
            # address (e.g. a reassigned mailbox).
            linked = db.scalar(
                select(OAuthAccount.id).where(
                    OAuthAccount.user_id == user.id, OAuthAccount.provider == "google"
                )
            )
            if linked is not None:
                raise LoginError("account_conflict")
        db.add(OAuthAccount(user_id=user.id, provider="google", provider_user_id=sub))
        db.flush()

    if user.deleted_at is not None:
        raise LoginError("account_disabled")
    avatar = _clean_avatar(claims.get("picture"))
    if avatar and avatar != user.avatar_url:
        user.avatar_url = avatar
    return user


def _create_session(db: Session, user_id: Any, settings: Settings) -> str:
    now = datetime.now(UTC)
    # Opportunistic cleanup of this user's expired sessions.
    db.execute(
        delete(UserSession).where(UserSession.user_id == user_id, UserSession.expires_at < now)
    )
    raw = generate_token()
    db.add(
        UserSession(
            user_id=user_id,
            token_hash=hash_token(raw),
            expires_at=now + timedelta(days=settings.session_ttl_days),
        )
    )
    return raw


def get_user_by_session_token(db: Session, raw_token: str) -> User | None:
    """Resolve a cookie token to an active user, or None (unknown/expired/deleted user)."""
    now = datetime.now(UTC)
    row = db.execute(
        select(User, UserSession)
        .join(UserSession, UserSession.user_id == User.id)
        .where(
            UserSession.token_hash == hash_token(raw_token),
            UserSession.expires_at > now,
            User.deleted_at.is_(None),
        )
        .options(selectinload(User.college), selectinload(User.profile))
    ).first()
    if row is None:
        return None
    user, session = row
    if now - session.last_seen_at > LAST_SEEN_REFRESH:
        session.last_seen_at = now
        db.commit()
    return user


def revoke_session(db: Session, raw_token: str) -> None:
    db.execute(delete(UserSession).where(UserSession.token_hash == hash_token(raw_token)))
    db.commit()
