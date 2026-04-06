from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, BaseModel, Field

from app.domain import OutputFormat
from app.domain.enums import Visibility


def _is_valid_price(price: int | None) -> int | None:
    if price is None:
        return None

    if 0 <= price <= 99999:
        return price
    else:
        raise ValueError(f"Invalid price: {price}")


class EbookGenerateRequest(BaseModel):
    output_formats: list[OutputFormat] = Field(min_length=1)


class EbookRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    manuscript_id: UUID
    sample_id: UUID | None
    output_format: OutputFormat
    list_price_cents: int | None
    sale_price_cents: int | None
    price_currency: str
    file_size_bytes: int
    download_count: int
    visibility: Visibility
    unlisted_download_limit: int | None
    created_at: datetime
    published_at: datetime | None


class EbookListItem(BaseModel):
    """Lighter response model for list endpoints."""

    model_config = {"from_attributes": True}

    id: UUID
    manuscript_id: UUID
    sample_id: UUID | None
    output_format: OutputFormat
    list_price_cents: int | None
    sale_price_cents: int | None
    price_currency: str
    file_size_bytes: int
    download_count: int
    visibility: Visibility
    unlisted_download_limit: int | None
    created_at: datetime
    published_at: datetime | None
    deleted_at: datetime | None = None


class EbookUpdate(BaseModel):
    list_price_cents: Annotated[int | None, AfterValidator(_is_valid_price)] = None
    sale_price_cents: Annotated[int | None, AfterValidator(_is_valid_price)] = None
    price_currency: str = "USD"
