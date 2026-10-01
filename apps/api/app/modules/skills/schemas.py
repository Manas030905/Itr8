from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str


class UserSkillOut(BaseModel):
    skill: SkillOut
    level: str


class UserSkillInput(BaseModel):
    skill_id: uuid.UUID
    level: str = Field(pattern=r"^(beginner|intermediate|advanced)$")


class UserSkillsUpdate(BaseModel):
    skills: list[UserSkillInput] = Field(default_factory=list, max_length=30)
