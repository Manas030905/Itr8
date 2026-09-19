from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, SmallInteger, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.users.models import User


class Profile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Builder profile (1:1 with users). Milestone 1 fields only; more arrive in Milestone 2."""

    __tablename__ = "profiles"
    __table_args__ = (
        CheckConstraint("year BETWEEN 1 AND 6", name="year_range"),
        CheckConstraint("char_length(branch) BETWEEN 1 AND 80", name="branch_length"),
        CheckConstraint("char_length(bio) <= 500", name="bio_length"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    branch: Mapped[str | None] = mapped_column(Text)
    year: Mapped[int | None] = mapped_column(SmallInteger)
    bio: Mapped[str | None] = mapped_column(Text)
    onboarding_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="profile", lazy="raise")
