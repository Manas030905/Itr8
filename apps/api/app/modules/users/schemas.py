from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.users.models import User


class CollegeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    branch: str | None
    year: int | None
    bio: str | None
    onboarding_completed_at: datetime | None


class MeOut(BaseModel):
    """The signed-in user with their profile. Returned by /auth/me and /profiles/me."""

    id: uuid.UUID
    email: str
    name: str
    avatar_url: str | None
    role: str
    college: CollegeOut
    profile: ProfileOut
    onboarding_completed: bool


def build_me(user: User) -> MeOut:
    """Build MeOut from a User whose `college` and `profile` are already loaded."""
    return MeOut(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        role=user.role,
        college=CollegeOut.model_validate(user.college),
        profile=ProfileOut.model_validate(user.profile),
        onboarding_completed=user.profile.onboarding_completed_at is not None,
    )
