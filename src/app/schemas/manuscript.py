from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.domain import ManuscriptState, SourceFormat


class ManuscriptCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None
    source_format: SourceFormat

    @field_validator("title")
    @classmethod
    def title_not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title cannot be empty or whitespace only")
        return v


class ManuscriptUpdate(BaseModel):
    title: str | None = None
    description: str | None = None

    @field_validator("title")
    @classmethod
    def title_not_whitespace(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("title cannot be empty or whitespace only")
        return v


class ManuscriptRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    author_id: UUID
    title: str
    description: str | None
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
