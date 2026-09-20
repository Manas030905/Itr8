"""Application settings, loaded from environment variables (and an optional .env file).

Strict validation is applied whenever ENVIRONMENT != "local" so a misconfigured
staging/production deploy fails at startup instead of running insecurely.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PARENTS = Path(__file__).resolve().parents
_API_ROOT = _PARENTS[2]
# In a monorepo checkout this is the repo root (where .env lives). In a container image the
# code sits at /app/app/core/config.py and there is no such parent, so fall back safely.
_REPO_ROOT = _PARENTS[4] if len(_PARENTS) > 4 else _API_ROOT

DEFAULT_SECRET_KEY = "change-me-local-only-change-me-local-only"
_DOMAIN_RE = re.compile(r"^(?=.{1,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_REPO_ROOT / ".env", _API_ROOT / ".env"),
        extra="ignore",
        case_sensitive=False,
    )

    environment: Literal["local", "staging", "production"] = "local"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://builderhub:builderhub_dev@localhost:5432/builderhub"
    test_database_url: str | None = None

    frontend_url: str = "http://localhost:3000"

    secret_key: str = DEFAULT_SECRET_KEY
    session_cookie_name: str = "bh_session"
    session_ttl_days: int = 14
    oauth_cookie_name: str = "bh_oauth"

    google_client_id: str = ""
    google_client_secret: str = ""
    google_require_hd: bool = False

    # Comma-separated email domains allowed to sign in, e.g. "iiitr.ac.in" or
    # "iiitr.ac.in,students.iiitr.ac.in". Exact match (subdomains are NOT implied).
    # No default on purpose: an unconfigured server admits nobody (fail closed).
    allowed_email_domains: str = ""
    allowed_test_emails: str = ""
    default_college_slug: str = "iiit-raichur"
    dev_login_enabled: bool = False

    sentry_dsn: str = ""

    # ---- validators -------------------------------------------------------
    @field_validator("database_url", "test_database_url")
    @classmethod
    def _normalize_db_url(cls, v: str | None) -> str | None:
        """Managed Postgres providers hand out postgres:// or postgresql:// URLs."""
        if not v:
            return v
        if v.startswith("postgres://"):
            v = "postgresql://" + v[len("postgres://") :]
        if v.startswith("postgresql://"):
            v = "postgresql+psycopg://" + v[len("postgresql://") :]
        return v

    @field_validator("frontend_url")
    @classmethod
    def _strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")

    @field_validator("allowed_email_domains")
    @classmethod
    def _validate_domains(cls, v: str) -> str:
        for raw in v.split(","):
            domain = raw.strip().lower().removeprefix("@")
            if domain and not _DOMAIN_RE.match(domain):
                raise ValueError(f"ALLOWED_EMAIL_DOMAINS contains an invalid domain: {raw!r}")
        return v

    @model_validator(mode="after")
    def _strict_outside_local(self) -> Settings:
        if self.environment == "local":
            return self
        problems: list[str] = []
        if not self.allowed_email_domains_list:
            problems.append("ALLOWED_EMAIL_DOMAINS must list at least one domain")
        if self.secret_key == DEFAULT_SECRET_KEY or len(self.secret_key) < 32:
            problems.append("SECRET_KEY must be set to a random value of at least 32 characters")
        if self.dev_login_enabled:
            problems.append("DEV_LOGIN_ENABLED must be false outside ENVIRONMENT=local")
        if not self.frontend_url.startswith("https://"):
            problems.append("FRONTEND_URL must be https:// outside ENVIRONMENT=local")
        if not (self.google_client_id and self.google_client_secret):
            problems.append("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set")
        if problems:
            raise ValueError("Invalid configuration: " + "; ".join(problems))
        return self

    # ---- derived ----------------------------------------------------------
    @property
    def cookie_secure(self) -> bool:
        return self.environment != "local"

    @property
    def google_configured(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)

    @property
    def dev_login_active(self) -> bool:
        return self.environment == "local" and self.dev_login_enabled

    @property
    def allowed_email_domains_list(self) -> set[str]:
        return {
            d.strip().lower().removeprefix("@") for d in self.allowed_email_domains.split(",")
        } - {""}

    @property
    def allowed_test_emails_list(self) -> set[str]:
        return {e.strip().lower() for e in self.allowed_test_emails.split(",") if e.strip()}

    @property
    def allowed_origins(self) -> set[str]:
        origins = {self.frontend_url}
        if self.environment == "local":
            # Swagger UI / direct API calls during local development.
            origins |= {"http://localhost:8000", "http://127.0.0.1:8000"}
        return origins

    @property
    def google_redirect_uri(self) -> str:
        return f"{self.frontend_url}/api/v1/auth/google/callback"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
