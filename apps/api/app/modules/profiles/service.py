from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.modules.profiles.schemas import ProfileUpdate
from app.modules.users.models import User


def update_my_profile(db: Session, user: User, payload: ProfileUpdate) -> User:
    """Apply a partial update to *the given user's own* profile.

    There is deliberately no user-id parameter: the only profile a caller can modify is the
    one belonging to the authenticated user (no IDOR surface).
    """
    changes = payload.changes()
    if "name" in changes:
        user.name = changes["name"]
    profile = user.profile
    for field in ("branch", "year", "bio"):
        if field in changes:
            setattr(profile, field, changes[field])

    # Completion is derived server-side; clients cannot set it (ADR-010).
    if profile.onboarding_completed_at is None and user.name and profile.branch and profile.year:
        profile.onboarding_completed_at = datetime.now(UTC)

    db.commit()
    return user
