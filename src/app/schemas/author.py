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
    bio: str | None = None
    website: str | None = None
    is_public: bool = False

    @field_validator("display_name")
    @classmethod
    def display_name_not_whitespace(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("display_name cannot be empty or whitespace only")
        return v

    @field_validator("website")
    @classmethod
    def website_valid_url(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                return None

            parts = v.split("://")
            if len(parts) > 2:
                raise ValueError("website must be a valid URL")

            if len(parts) == 2:
                prefix = parts[0].lower()
                if prefix in ("https", "http"):
                    # Lowercase the prefix but leave the rest alone
                    return "://".join([prefix] + parts[1:])
                else:
                    raise ValueError("website scheme must be 'https' or 'http'")

            return "://".join(["https"] + parts)

        return v


class AuthorRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    email: str
    display_name: str
    bio: str | None
    website: str | None
    avatar_key: str | None
    is_public: bool
    created_at: datetime


class AuthorPublicRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    display_name: str
    bio: str | None
    website: str | None
    is_public: bool
    created_at: datetime
