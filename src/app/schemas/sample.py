from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SampleCreate(BaseModel):
    title: str = Field(min_length=1)
    excerpt_start: str
    excerpt_end: str
    promo_header: str | None = None
    promo_footer: str | None = None

    @field_validator("title")
    @classmethod
    def title_not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title cannot be empty or whitespace only")
        return v


class SampleUpdate(BaseModel):
    title: str | None = None
    excerpt_start: str | None = None
    excerpt_end: str | None = None
    promo_header: str | None = None
    promo_footer: str | None = None

    @field_validator("title")
    @classmethod
    def title_not_whitespace(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("title cannot be empty or whitespace only")
        return v


class SampleRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    manuscript_id: UUID
    title: str
    excerpt_start: str
    excerpt_end: str
    promo_header: str | None
    promo_footer: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
