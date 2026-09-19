from __future__ import annotations

import logging
from typing import Any

from authlib.integrations.base_client.errors import OAuthError
from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, RedirectResponse

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.deps import CurrentUser
from app.core.security import safe_next_path
from app.modules.auth import service
from app.modules.auth.oauth import GOOGLE_CLAIMS_OPTIONS, oauth
from app.modules.auth.schemas import DevLoginRequest
from app.modules.users.schemas import MeOut, build_me

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

DEFAULT_LANDING = "/me"


# --------------------------------------------------------------------------- helpers
def _login_error_redirect(code: str) -> RedirectResponse:
    return RedirectResponse(f"{settings.frontend_url}/login?error={code}", status_code=303)


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=settings.session_ttl_days * 24 * 3600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def _do_login(claims: dict[str, Any]) -> service.LoginResult:
    """Runs in a worker thread (sync SQLAlchemy). Owns its own DB session."""
    with SessionLocal() as db:
        return service.login_with_google(db, claims, settings)


def _destination(result: service.LoginResult, next_path: str) -> str:
    return next_path if result.onboarding_completed else "/onboarding"


# --------------------------------------------------------------------------- Google OAuth
@router.get("/google/login", include_in_schema=False)
async def google_login(request: Request, next_path: str = Query(DEFAULT_LANDING, alias="next")):
    if not settings.google_configured:
        return _login_error_redirect("not_configured")
    request.session["next"] = safe_next_path(next_path, DEFAULT_LANDING)
    return await oauth.google.authorize_redirect(
        request, settings.google_redirect_uri, prompt="select_account"
    )


@router.get("/google/callback", include_in_schema=False)
async def google_callback(request: Request):
    if not settings.google_configured:
        return _login_error_redirect("not_configured")

    next_path = safe_next_path(request.session.get("next"), DEFAULT_LANDING)
    try:
        token = await oauth.google.authorize_access_token(
            request, claims_options=GOOGLE_CLAIMS_OPTIONS
        )
    except OAuthError as exc:
        # Includes the user pressing "Cancel" on Google's consent screen, and state mismatches.
        cancelled = request.query_params.get("error") == "access_denied"
        logger.info("OAuth callback rejected: %s", exc.error)
        request.session.clear()
        return _login_error_redirect("cancelled" if cancelled else "oauth_failed")
    except Exception:
        # Fail closed on anything unexpected (network, malformed/forged ID token, ...).
        logger.exception("Unexpected error during Google OAuth callback")
        request.session.clear()
        return _login_error_redirect("oauth_failed")
    finally:
        request.session.pop("next", None)

    claims = dict(token.get("userinfo") or {})
    try:
        result = await run_in_threadpool(_do_login, claims)
    except service.LoginError as exc:
        request.session.clear()
        return _login_error_redirect(exc.code)

    request.session.clear()
    response = RedirectResponse(
        f"{settings.frontend_url}{_destination(result, next_path)}", status_code=303
    )
    _set_session_cookie(response, result.session_token)
    return response


# --------------------------------------------------------------------------- session
@router.get("/me", response_model=MeOut)
def read_me(user: CurrentUser) -> MeOut:
    """The signed-in user, their college and profile."""
    return build_me(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request) -> Response:
    """Revoke the current session server-side and clear the cookie. Idempotent."""
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        with SessionLocal() as db:
            service.revoke_session(db, token)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(
        settings.session_cookie_name,
        path="/",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )
    return response


# --------------------------------------------------------------------------- dev only
@router.post("/dev-login", include_in_schema=False)
def dev_login(body: DevLoginRequest):
    """Local-only shortcut that skips Google. 404s unless ENVIRONMENT=local AND DEV_LOGIN_ENABLED.

    It still goes through the same allowlist and session code as real logins.
    """
    if not settings.dev_login_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    claims = {
        "sub": f"dev:{body.email.strip().lower()}",
        "email": body.email,
        "email_verified": True,
        "name": body.name,
    }
    try:
        result = _do_login(claims)
    except service.LoginError as exc:
        return JSONResponse({"error": exc.code}, status_code=status.HTTP_403_FORBIDDEN)
    response = JSONResponse({"redirect": _destination(result, DEFAULT_LANDING)})
    _set_session_cookie(response, result.session_token)
    return response
