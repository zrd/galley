from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from .enums import OutputFormat, Visibility


@dataclass
class Ebook:
    """
    A generated ebook file, either a full book or a sample.

    If sample_id is None, this is a full ebook generated from the manuscript.
    If sample_id is set, this is a sample ebook generated from that sample definition.
    """

    manuscript_id: UUID
    output_format: OutputFormat
    file_key: str
    file_size_bytes: int
    download_filename: str
    id: UUID = field(default_factory=uuid4)
    sample_id: UUID | None = None
    list_price_cents: int | None = None
    sale_price_cents: int | None = None
    price_currency: str = "USD"
    download_count: int = 0
    visibility: Visibility = Visibility.PRIVATE
    unlisted_download_limit: int | None  = None     # Max downloads when UNLISTED (None = unlimited)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    published_at: datetime | None = None            # Set when first published, never reset
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def is_sample(self) -> bool:
        """Check if this is a sample ebook."""
        return self.sample_id is not None

    @property
    def effective_price_cents(self) -> int:
        if self.sale_price_cents is not None:
            return self.sale_price_cents
        elif self.list_price_cents is not None:
            return self.list_price_cents
        else:
            return 0

    @property
    def is_free(self) -> bool:
        return True if self.effective_price_cents == 0 else False

    @property
    def formatted_price(self) -> str:
        price = self.effective_price_cents
        major_currency_symbol = "$"
        if price == 0:
            return "Free"
        else:
            major, minor = divmod(price, 100)
            return f"{major_currency_symbol}{major}.{minor:02d}"

    def soft_delete(self) -> None:
        self.deleted_at = datetime.now(UTC)

    def restore(self) -> None:
        self.deleted_at = None

    def increment_download_count(self) -> None:
        """Increment the download counter."""
        self.download_count += 1

    def publish(self):
        self.visibility = Visibility.PUBLISHED
        if self.published_at is None:
            self.published_at = datetime.now(UTC)

    def unlist(self):
        self.visibility = Visibility.UNLISTED

    def make_private(self):
        self.visibility = Visibility.PRIVATE
