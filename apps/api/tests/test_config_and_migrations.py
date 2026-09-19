import pytest
from alembic import command
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.config import Settings
from app.core.db import engine
from tests.conftest import alembic_config

PROD = dict(
    _env_file=None,
    environment="production",
    secret_key="s" * 48,
    frontend_url="https://app.example.com",
    google_client_id="id",
    google_client_secret="secret",
    allowed_email_domains="iiitr.ac.in",
)


# ------------------------------------------------------------------ config
def test_domains_are_parsed_normalised_and_support_several():
    s = Settings(_env_file=None, allowed_email_domains=" IIITR.ac.in, @students.iiitr.ac.in ,,")
    assert s.allowed_email_domains_list == {"iiitr.ac.in", "students.iiitr.ac.in"}


def test_no_domains_configured_means_nobody_is_allowed():
    assert Settings(_env_file=None, allowed_email_domains="").allowed_email_domains_list == set()


@pytest.mark.parametrize(
    "bad", ["*", "*.iiitr.ac.in", "iiitr", "iiitr.ac.in/x", "a b.com", "-x.com"]
)
def test_invalid_or_wildcard_domains_fail_at_startup(bad):
    with pytest.raises(ValueError, match="ALLOWED_EMAIL_DOMAINS"):
        Settings(_env_file=None, allowed_email_domains=bad)


def test_production_settings_ok():
    assert Settings(**PROD).cookie_secure is True


@pytest.mark.parametrize(
    "override, message",
    [
        ({"secret_key": "change-me-local-only-change-me-local-only"}, "SECRET_KEY"),
        ({"secret_key": "short"}, "SECRET_KEY"),
        ({"frontend_url": "http://app.example.com"}, "FRONTEND_URL"),
        ({"google_client_id": ""}, "GOOGLE_CLIENT_ID"),
        ({"allowed_email_domains": ""}, "ALLOWED_EMAIL_DOMAINS"),
        ({"dev_login_enabled": True}, "DEV_LOGIN_ENABLED"),
    ],
)
def test_production_refuses_insecure_configuration(override, message):
    with pytest.raises(ValueError, match=message):
        Settings(**{**PROD, **override})


@pytest.mark.parametrize(
    "given",
    [
        "postgres://u:p@h:5432/db",
        "postgresql://u:p@h:5432/db",
        "postgresql+psycopg://u:p@h:5432/db",
    ],
)
def test_database_url_is_normalised_for_psycopg3(given):
    assert (
        Settings(_env_file=None, database_url=given).database_url
        == "postgresql+psycopg://u:p@h:5432/db"
    )


# ------------------------------------------------------------------ database constraints
def _exec(sql: str, **params):
    with engine.begin() as conn:
        conn.execute(text(sql), params)


def _college_id() -> str:
    with engine.connect() as conn:
        return str(conn.scalar(text("SELECT id FROM colleges WHERE slug='iiit-raichur'")))


def test_seed_college_exists_after_migrations():
    with engine.connect() as conn:
        assert (
            conn.scalar(text("SELECT name FROM colleges WHERE slug='iiit-raichur'"))
            == "IIIT Raichur"
        )


def test_db_rejects_uppercase_email():
    with pytest.raises(IntegrityError):
        _exec(
            "INSERT INTO users (email, name, college_id) VALUES ('A@X.COM','n',:c)", c=_college_id()
        )


def test_db_rejects_invalid_role():
    with pytest.raises(IntegrityError):
        _exec(
            "INSERT INTO users (email,name,college_id,role) VALUES ('a@x.com','n',:c,'root')",
            c=_college_id(),
        )


def test_db_rejects_invalid_year_and_long_bio():
    _exec(
        "INSERT INTO users (id,email,name,college_id) VALUES ('00000000-0000-0000-0000-000000000001','a@x.com','n',:c)",
        c=_college_id(),
    )
    with pytest.raises(IntegrityError):
        _exec(
            "INSERT INTO profiles (user_id, year) VALUES ('00000000-0000-0000-0000-000000000001', 9)"
        )
    with pytest.raises(IntegrityError):
        _exec(
            "INSERT INTO profiles (user_id, bio) VALUES ('00000000-0000-0000-0000-000000000001', repeat('x', 501))"
        )


def test_deleting_a_user_cascades_to_profile_sessions_and_oauth():
    _exec(
        "INSERT INTO users (id,email,name,college_id) VALUES ('00000000-0000-0000-0000-000000000002','c@x.com','n',:c)",
        c=_college_id(),
    )
    _exec("INSERT INTO profiles (user_id) VALUES ('00000000-0000-0000-0000-000000000002')")
    _exec(
        "INSERT INTO oauth_accounts (user_id,provider,provider_user_id) VALUES ('00000000-0000-0000-0000-000000000002','google','s')"
    )
    _exec(
        "INSERT INTO sessions (user_id,token_hash,expires_at) VALUES ('00000000-0000-0000-0000-000000000002',repeat('a',64), now()+interval '1 day')"
    )
    _exec("DELETE FROM users WHERE id='00000000-0000-0000-0000-000000000002'")
    with engine.connect() as conn:
        for t in ("profiles", "oauth_accounts", "sessions"):
            assert conn.scalar(text(f"SELECT count(*) FROM {t}")) == 0


# ------------------------------------------------------------------ migrations (keep LAST)
def test_migrations_downgrade_and_upgrade_cleanly():
    cfg = alembic_config()
    command.downgrade(cfg, "base")
    with engine.connect() as conn:
        tables = set(
            conn.scalars(text("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
        )
    assert tables <= {"alembic_version"}

    command.upgrade(cfg, "head")
    with engine.connect() as conn:
        tables = set(
            conn.scalars(text("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
        )
        assert {"colleges", "users", "oauth_accounts", "sessions", "profiles"} <= tables
        assert conn.scalar(text("SELECT count(*) FROM colleges")) == 1
