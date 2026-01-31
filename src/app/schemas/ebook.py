from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.domain import OutputFormat


class EbookGenerateRequest(BaseModel):
    output_formats: list[OutputFormat]


class EbookRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    manuscript_id: UUID
    sample_id: UUID | None
    output_format: OutputFormat
    file_size_bytes: int
    download_count: int
    created_at: datetime


class EbookListItem(BaseModel):
    """Lighter response model for list endpoints."""

    model_config = {"from_attributes": True}

    id: UUID
    manuscript_id: UUID
    sample_id: UUID | None
    output_format: OutputFormat
    file_size_bytes: int
    download_count: int
    created_at: datetime
