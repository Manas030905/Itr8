from pydantic import BaseModel, Field


class DevLoginRequest(BaseModel):
    email: str = Field(max_length=254)
    name: str | None = Field(default=None, max_length=100)
