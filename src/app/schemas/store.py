from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field, computed_field

from .genre import StoreGenreTree
from .tag import TagRead

T = TypeVar("T")


def _effective_price_cents(list_price_cents: int | None, sale_price_cents: int | None) -> int:
    if sale_price_cents is not None:
        return sale_price_cents
    elif list_price_cents is not None:
        return list_price_cents
    else:
        return 0


class StorePaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int


class StoreAuthorSummary(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    display_name: str

    @computed_field
    @property
    def profile_url(self) -> str:
        return f"/store/authors/{self.id}"


class StoreAuthorListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    display_name: str
    bio: str | None
    website: str | None
    avatar_key: str | None = Field(exclude=True)

    @computed_field
    @property
    def avatar_url(self) -> str | None:
        if self.avatar_key:
            return f"/authors/{self.id}/avatar"

        return None

    @computed_field
    @property
    def profile_url(self) -> str:
        return f"/store/authors/{self.id}"


class StoreEditionSummary(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    output_format: str
    published_at: datetime | None
    list_price_cents: int | None = Field(exclude=True)
    sale_price_cents: int | None = Field(exclude=True)

    @computed_field
    @property
    def is_free(self) -> bool:
        return _effective_price_cents(self.list_price_cents, self.sale_price_cents) == 0

    @computed_field
    @property
    def formatted_price(self) -> str:
        price = _effective_price_cents(self.list_price_cents, self.sale_price_cents)
        major_currency_symbol = "$"
        if price == 0:
            return "Free"
        else:
            major, minor = divmod(price, 100)
            return f"{major_currency_symbol}{major}.{minor:02d}"


class StoreBrowseItem(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    title: str
    author: StoreAuthorSummary
    description: str | None
    genres: list[StoreGenreTree]
    tags: list[TagRead]
    editions: list[StoreEditionSummary] = Field(validation_alias="ebooks")
    cover_image_key: str | None = Field(exclude=True)

    @computed_field
    @property
    def cover_url(self) -> str | None:
        if self.cover_image_key:
            return f"/manuscripts/{self.id}/cover"

        return None

    @computed_field
    @property
    def first_published_at(self) -> datetime | None:
        return min((e.published_at for e in self.editions if e.published_at is not None), default=None)


class StoreAuthorDetail(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    display_name: str
    bio: str | None
    website: str | None
    listings: list[StoreBrowseItem] = Field(validation_alias="manuscripts")
    avatar_key: str | None = Field(exclude=True)

    @computed_field
    @property
    def avatar_url(self) -> str | None:
        if self.avatar_key:
            return f"/authors/{self.id}/avatar"

        return None

    @computed_field
    @property
    def profile_url(self) -> str:
        return f"/store/authors/{self.id}"


class StoreManuscriptDetail(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    author: StoreAuthorSummary
    title: str
    description: str | None
    genres: list[StoreGenreTree]
    tags: list[TagRead]
    editions: list[StoreEditionSummary] = Field(validation_alias="ebooks")
    cover_image_key: str | None = Field(exclude=True)

    @computed_field
    @property
    def cover_url(self) -> str | None:
        if self.cover_image_key:
            return f"/manuscripts/{self.id}/cover"

        return None

    @computed_field
    @property
    def first_published_at(self) -> datetime | None:
        return min((e.published_at for e in self.editions if e.published_at is not None), default=None)


class StoreEditionDetail(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    manuscript: StoreManuscriptDetail
    output_format: str
    file_size_bytes: int
    sample_id: UUID | None
    list_price_cents: int | None = Field(exclude=True)
    sale_price_cents: int | None = Field(exclude=True)
    price_currency: str
    direct_download: bool = False

    @computed_field
    @property
    def download_url(self) -> str:
        return f"/ebooks/{self.id}/download"

    @computed_field
    @property
    def is_free(self) -> bool:
        return _effective_price_cents(self.list_price_cents, self.sale_price_cents) == 0

    @computed_field
    @property
    def formatted_price(self) -> str:
        price = _effective_price_cents(self.list_price_cents, self.sale_price_cents)
        major_currency_symbol = "$"
        if price == 0:
            return "Free"
        else:
            major, minor = divmod(price, 100)
            return f"{major_currency_symbol}{major}.{minor:02d}"
