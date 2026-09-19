"""Origin-based CSRF protection (see docs/ARCHITECTURE.md).

There is exactly one legitimate browser origin (FRONTEND_URL). Any state-changing request that
carries our session cookie must come from it. Combined with SameSite=Lax cookies this blocks
cross-site request forgery without per-request tokens.
"""

from __future__ import annotations

from urllib.parse import urlparse

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import settings

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _origin_from_referer(referer: str | None) -> str | None:
    if not referer:
        return None
    parsed = urlparse(referer)
    return f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else None


async def origin_check(request: Request, call_next):
    if request.method in UNSAFE_METHODS and request.cookies.get(settings.session_cookie_name):
        origin = request.headers.get("origin") or _origin_from_referer(
            request.headers.get("referer")
        )
        if origin not in settings.allowed_origins:
            return JSONResponse({"detail": "Cross-site request blocked"}, status_code=403)
    return await call_next(request)
