from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass
class Sample:
    """
    A sample definition for generating promotional excerpts from a manuscript.

    The excerpt_start and excerpt_end fields define the content range to include.
    Their interpretation depends on the source format:
    - For EPUB: chapter identifiers or navigation point IDs
    - For PDF: page numbers (e.g., "1", "25")
    - For DOCX/ODT: heading text or page numbers

    promo_header and promo_footer are optional markdown text that will be
    prepended/appended to the excerpt in the generated sample ebook.
    """

    manuscript_id: UUID
    title: str
    excerpt_start: str
    excerpt_end: str
    id: UUID = field(default_factory=uuid4)
    promo_header: str | None = None
    promo_footer: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        self.deleted_at = datetime.now(UTC)

    def restore(self) -> None:
        self.deleted_at = None

    def update(
        self,
        title: str | None = None,
        excerpt_start: str | None = None,
        excerpt_end: str | None = None,
        promo_header: str | None = None,
        promo_footer: str | None = None,
    ) -> None:
        """Update sample definition fields."""
        if title is not None:
            self.title = title
        if excerpt_start is not None:
            self.excerpt_start = excerpt_start
        if excerpt_end is not None:
            self.excerpt_end = excerpt_end
        # Allow setting to None or updating
        if promo_header is not None:
            self.promo_header = promo_header
        if promo_footer is not None:
            self.promo_footer = promo_footer
        self._touch()

    def _touch(self) -> None:
        self.updated_at = datetime.now(UTC)
