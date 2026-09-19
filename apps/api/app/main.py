from __future__ import annotations

import logging

import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.sessions import SessionMiddleware

from app.api import api_router
from app.core.config import settings
from app.core.csrf import origin_check


def _operation_id(route: APIRoute) -> str:
    """Clean operation ids (e.g. `read_me`) => readable generated TypeScript client."""
    return route.name


def create_app() -> FastAPI:
    logging.basicConfig(level=settings.log_level)
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            send_default_pii=False,
            traces_sample_rate=0.0,
        )

    app = FastAPI(
        title="Builder Hub API",
        version="0.1.0",
        docs_url=None if settings.environment == "production" else "/api/docs",
        redoc_url=None,
        openapi_url="/api/v1/openapi.json",
        generate_unique_id_function=_operation_id,
    )

    # Middleware added last runs first (outermost). Order here is: session -> CSRF -> routes.
    app.middleware("http")(origin_check)
    # Short-lived signed cookie used ONLY for the OAuth handshake (state/nonce/PKCE/next).
    # The real login session is a separate opaque, server-side session (bh_session).
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        session_cookie=settings.oauth_cookie_name,
        max_age=600,
        same_site="lax",
        https_only=settings.cookie_secure,
    )

    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
