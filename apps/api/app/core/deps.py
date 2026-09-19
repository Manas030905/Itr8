"""Shared FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.modules.auth.service import get_user_by_session_token
from app.modules.users.models import User

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(request: Request, db: DbSession) -> User:
    """Require a valid session cookie; otherwise 401."""
    token = request.cookies.get(settings.session_cookie_name)
    user = get_user_by_session_token(db, token) if token else None
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
