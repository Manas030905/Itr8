from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.users.models import User


class Skill(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "skills"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_skills_slug"),
    )

    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False)
    user_skills: Mapped[list[UserSkill]] = relationship(
        back_populates="skill", cascade="all, delete-orphan", lazy="raise"
    )


class UserSkill(Base):
    __tablename__ = "user_skills"
    __table_args__ = (
        CheckConstraint(
            "level IN ('beginner', 'intermediate', 'advanced')",
            name="level_valid",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    )
    level: Mapped[str] = mapped_column(String(20), nullable=False, server_default="beginner")

    skill: Mapped[Skill] = relationship(back_populates="user_skills", lazy="raise")
    user: Mapped[User] = relationship(lazy="raise")
