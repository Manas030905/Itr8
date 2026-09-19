"""Prove Authlib enforces what we rely on when validating Google's ID token.

We sign tokens with a local RSA key and feed our real client (with the JWKS fetch stubbed)
forged variants. If any forged token were accepted, the login flow would be unsafe.
"""

import asyncio
import time
from unittest.mock import AsyncMock

import pytest
from joserfc import jwt
from joserfc.errors import (
    BadSignatureError,
    ExpiredTokenError,
    InvalidClaimError,
    MissingClaimError,
)
from joserfc.jwk import RSAKey

from app.core.config import settings
from app.modules.auth.oauth import GOOGLE_CLAIMS_OPTIONS, oauth

NONCE = "expected-nonce"
ISS = "https://accounts.google.com"


@pytest.fixture(scope="module")
def signing_key() -> RSAKey:
    return RSAKey.generate_key(2048, parameters={"kid": "test-key-1"})


@pytest.fixture
def parse(signing_key, monkeypatch):
    other = RSAKey.generate_key(2048, parameters={"kid": "test-key-1"})  # same kid, wrong key

    def _parse(overrides: dict | None = None, *, key=None, nonce=NONCE, drop: tuple = ()):
        now = int(time.time())
        payload = {
            "iss": ISS,
            "aud": settings.google_client_id,
            "sub": "123",
            "email": "asha@iiitr.ac.in",
            "email_verified": True,
            "iat": now,
            "exp": now + 300,
            "nonce": NONCE,
            **(overrides or {}),
        }
        for k in drop:
            payload.pop(k)
        signer = other if key == "other" else signing_key
        token = jwt.encode({"alg": "RS256", "kid": signing_key.kid}, payload, signer)
        monkeypatch.setattr(
            oauth.google,
            "fetch_jwk_set",
            AsyncMock(return_value={"keys": [signing_key.as_dict(private=False)]}),
        )
        return asyncio.run(
            oauth.google.parse_id_token(
                {"id_token": token, "access_token": "at"},
                nonce=nonce,
                claims_options=GOOGLE_CLAIMS_OPTIONS,
            )
        )

    return _parse


def test_a_valid_token_is_accepted(parse):
    assert parse()["email"] == "asha@iiitr.ac.in"


def test_legacy_google_issuer_form_is_accepted(parse):
    assert parse({"iss": "accounts.google.com"})["sub"] == "123"


def test_a_multi_audience_token_that_includes_us_is_accepted(parse):
    cid = settings.google_client_id
    assert parse({"aud": [cid, "other"], "azp": cid})["sub"] == "123"


@pytest.mark.parametrize(
    ("overrides", "error"),
    [
        ({"iss": "https://evil.example"}, InvalidClaimError),
        ({"aud": "someone-elses-client-id"}, InvalidClaimError),
        # A foreign audience must be refused even if `azp` claims to be us.
        ({"aud": "someone-else", "azp": settings.google_client_id}, InvalidClaimError),
        ({"aud": ["someone-else"]}, InvalidClaimError),
        ({"exp": int(time.time()) - 3600}, ExpiredTokenError),
        ({"iat": int(time.time()) + 3600}, InvalidClaimError),
    ],
    ids=[
        "wrong-issuer",
        "wrong-audience",
        "foreign-aud-with-our-azp",
        "foreign-aud-list",
        "expired",
        "issued-in-future",
    ],
)
def test_forged_or_stale_claims_are_rejected(parse, overrides, error):
    with pytest.raises(error):
        parse(overrides)


def test_wrong_nonce_is_rejected(parse):
    with pytest.raises(InvalidClaimError):
        parse(nonce="a-different-nonce")


@pytest.mark.parametrize("claim", ["iss", "aud"])
def test_missing_issuer_or_audience_is_rejected(parse, claim):
    with pytest.raises(MissingClaimError):
        parse(drop=(claim,))


def test_token_signed_by_an_unknown_key_is_rejected(parse):
    with pytest.raises(BadSignatureError):
        parse(key="other")


def test_login_redirect_uses_state_nonce_and_pkce(client):
    r = client.get("/api/v1/auth/google/login", follow_redirects=False)
    assert r.status_code == 302
    from urllib.parse import parse_qs, urlparse

    url = urlparse(r.headers["location"])
    q = {k: v[0] for k, v in parse_qs(url.query).items()}
    assert url.netloc == "accounts.google.com"
    assert q["client_id"] == settings.google_client_id
    assert q["redirect_uri"] == "http://localhost:3000/api/v1/auth/google/callback"
    assert q["response_type"] == "code" and q["scope"] == "openid email profile"
    assert q["code_challenge_method"] == "S256" and len(q["code_challenge"]) >= 43
    assert len(q["state"]) >= 16 and len(q["nonce"]) >= 16
    assert settings.oauth_cookie_name in client.cookies
