from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from .enums import OutputFormat


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
    id: UUID = field(default_factory=uuid4)
    sample_id: UUID | None = None
    download_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        self.deleted_at = None

    def increment_download_count(self) -> None:
        """Increment the download counter."""
        self.download_count += 1

    def is_sample(self) -> bool:
        """Check if this is a sample ebook."""
        return self.sample_id is not None
