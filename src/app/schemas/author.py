from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class AuthorCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)
    display_name: str = Field(min_length=1)

    @field_validator("display_name")
    @classmethod
    def display_name_not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("display_name cannot be empty or whitespace only")
        return v


class AuthorUpdate(BaseModel):
    display_name: str | None = None

    @field_validator("display_name")
    @classmethod
    def display_name_not_whitespace(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("display_name cannot be empty or whitespace only")
        return v


class AuthorRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    email: str
    display_name: str
    created_at: datetime
