from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.domain import ManuscriptState, SourceFormat
from app.schemas.genre import GenreRead
from app.schemas.tag import TagRead


class ManuscriptCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None
    genre_ids: list[int] = []
    tag_names: list[str] = []
    source_format: SourceFormat

    @field_validator("title")
    @classmethod
    def title_not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title cannot be empty or whitespace only")
        return v

    @field_validator("tag_names", mode="before")
    @classmethod
    def strip_and_reject_blank_tags(cls, v: list[str]) -> list[str]:
        stripped = [name.strip() for name in v]
        if any(not name for name in stripped):
            raise ValueError("tag names cannot be blank")
        return stripped


class ManuscriptUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    genre_ids: list[int] | None = None
    tag_names: list[str] | None = None

    @field_validator("title")
    @classmethod
    def title_not_whitespace(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("title cannot be empty or whitespace only")
        return v

    @field_validator("tag_names", mode="before")
    @classmethod
    def strip_and_reject_blank_tags(cls, v: list[str]) -> list[str]:
        stripped = [name.strip() for name in v]
        if any(not name for name in stripped):
            raise ValueError("tag names cannot be blank")
        return stripped


class ManuscriptRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    author_id: UUID
    title: str
    description: str | None
    genres: list[GenreRead]
    tags: list[TagRead]
    source_format: SourceFormat
    state: ManuscriptState
    created_at: datetime
    updated_at: datetime


class ManuscriptListItem(BaseModel):
    """Lighter response model for list endpoints."""

    model_config = {"from_attributes": True}

    id: UUID
    title: str
    state: ManuscriptState
    source_format: SourceFormat
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
