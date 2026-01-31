from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SampleCreate(BaseModel):
    title: str
    excerpt_start: str
    excerpt_end: str
    promo_header: str | None = None
    promo_footer: str | None = None


class SampleUpdate(BaseModel):
    title: str | None = None
    excerpt_start: str | None = None
    excerpt_end: str | None = None
    promo_header: str | None = None
    promo_footer: str | None = None


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
