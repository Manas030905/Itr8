"""Google OAuth 2.0 / OpenID Connect client (Authlib).

Endpoints are configured explicitly (no discovery request at startup). Authlib handles `state`,
`nonce` and PKCE (S256); ID-token signature, audience and expiry are validated by Authlib, and we
pin the issuer via GOOGLE_CLAIMS_OPTIONS when exchanging the code.
"""

from __future__ import annotations

from authlib.integrations.starlette_client import OAuth

from app.core.config import settings

GOOGLE_ISSUERS = ["https://accounts.google.com", "accounts.google.com"]
# Authlib validates signature, expiry and nonce by default; issuer and audience are only checked
# if we pin them here. `aud` must contain OUR client id (verified in tests/test_oauth_tokens.py).
GOOGLE_CLAIMS_OPTIONS = {
    "iss": {"essential": True, "values": GOOGLE_ISSUERS},
    "aud": {"essential": True, "values": [settings.google_client_id]},
}

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
    access_token_url="https://oauth2.googleapis.com/token",
    jwks_uri="https://www.googleapis.com/oauth2/v3/certs",
    client_kwargs={"scope": "openid email profile", "code_challenge_method": "S256"},
)
