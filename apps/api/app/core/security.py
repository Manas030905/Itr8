"""Small, dependency-free security helpers."""

from __future__ import annotations

import hashlib
import re
import secrets
from urllib.parse import urlparse

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f\\]")


def generate_token() -> str:
    """256 bits of randomness, URL-safe. Only ever sent to the client in a cookie."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """SHA-256 hex digest; this is what the database stores."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def normalize_email(email: str) -> str:
    return email.strip().lower()


def email_domain(email: str) -> str:
    return email.rsplit("@", 1)[-1] if "@" in email else ""


def safe_next_path(value: str | None, default: str = "/") -> str:
    """Return `value` only if it is a same-site relative path; otherwise `default`.

    Prevents open redirects via the post-login `next` parameter: no scheme, no host,
    no protocol-relative (`//evil.com`), no backslashes or control characters.
    """
    if not value or len(value) > 200:
        return default
    if not value.startswith("/") or value.startswith("//") or _CONTROL_CHARS.search(value):
        return default
    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc:
        return default
    return value
