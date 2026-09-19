from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.profiles.models import Profile


class College(UUIDPrimaryKeyMixin, Base):
    """An institution. Which email domains may sign in is configuration (ALLOWED_EMAIL_DOMAINS)."""

    __tablename__ = "colleges"

    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("email = lower(email)", name="email_lowercase"),
        CheckConstraint("role IN ('student', 'admin')", name="role_valid"),
    )

    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text)
    college_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("colleges.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False, server_default="student")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # lazy="raise": relationships must be loaded explicitly (avoids hidden N+1 queries).
    college: Mapped[College] = relationship(lazy="raise")
    profile: Mapped[Profile] = relationship(back_populates="user", uselist=False, lazy="raise")
    oauth_accounts: Mapped[list[OAuthAccount]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="raise"
    )


class OAuthAccount(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "oauth_accounts"
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_oauth_accounts_provider_user"),
        UniqueConstraint("user_id", "provider", name="uq_oauth_accounts_user_provider"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="oauth_accounts", lazy="raise")
