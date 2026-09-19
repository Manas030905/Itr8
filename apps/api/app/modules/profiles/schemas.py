from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _single_line(value: str) -> str:
    return " ".join(_CONTROL.sub("", value).split())


class ProfileUpdate(BaseModel):
    """Partial update of the signed-in user's own profile.

    Omitted fields are left unchanged. `name`, `branch` and `year` cannot be cleared;
    `bio` can be cleared by sending null or an empty string.
    """

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, max_length=100)
    branch: str | None = Field(default=None, max_length=80)
    year: int | None = Field(default=None, ge=1, le=6)
    bio: str | None = Field(default=None, max_length=500)

    @field_validator("name", "branch")
    @classmethod
    def _clean_single_line(cls, v: str | None) -> str | None:
        return None if v is None else _single_line(v)

    @field_validator("bio")
    @classmethod
    def _clean_bio(cls, v: str | None) -> str | None:
        if v is None:
            return None
        cleaned = _CONTROL.sub("", v).replace("\r\n", "\n").strip()
        return cleaned or None

    @model_validator(mode="after")
    def _required_fields_not_blank(self) -> ProfileUpdate:
        for field in ("name", "branch", "year"):
            if field in self.model_fields_set and getattr(self, field) in (None, ""):
                raise ValueError(f"{field} cannot be empty")
        return self

    def changes(self) -> dict[str, Any]:
        return {f: getattr(self, f) for f in self.model_fields_set}
