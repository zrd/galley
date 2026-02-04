from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from .enums import ManuscriptState, SourceFormat
from .exceptions import InvalidStateTransition


@dataclass
class Manuscript:
    author_id: UUID
    title: str
    source_format: SourceFormat
    source_file_key: str
    id: UUID = field(default_factory=uuid4)
    description: str | None = None
    state: ManuscriptState = ManuscriptState.DRAFT
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        self.deleted_at = None

    def mark_ready(self) -> None:
        """Transition manuscript to ready state, allowing ebook generation."""
        if self.state != ManuscriptState.DRAFT:
            raise InvalidStateTransition(
                f"Cannot mark manuscript as ready from state '{self.state.value}'"
            )
        self.state = ManuscriptState.READY
        self._touch()

    def archive(self) -> None:
        """Archive the manuscript."""
        if self.state == ManuscriptState.ARCHIVED:
            raise InvalidStateTransition("Manuscript is already archived")
        self.state = ManuscriptState.ARCHIVED
        self._touch()

    def unarchive(self) -> None:
        """Restore archived manuscript to ready state."""
        if self.state != ManuscriptState.ARCHIVED:
            raise InvalidStateTransition("Can only unarchive an archived manuscript")
        self.state = ManuscriptState.READY
        self._touch()

    def update_metadata(
        self,
        title: str | None = None,
        description: str | None = None,
    ) -> None:
        """Update manuscript metadata. Only allowed in draft or ready state."""
        if self.state == ManuscriptState.ARCHIVED:
            raise InvalidStateTransition("Cannot update an archived manuscript")
        if title is not None:
            self.title = title
        if description is not None:
            self.description = description
        self._touch()

    def update_source(self, source_file_key: str, source_format: SourceFormat) -> None:
        """Replace manuscript source file. Resets state to draft."""
        self.source_file_key = source_file_key
        self.source_format = source_format
        self.state = ManuscriptState.DRAFT
        self._touch()

    def can_generate_ebook(self) -> bool:
        """Check if manuscript is in a state that allows ebook generation."""
        return self.state == ManuscriptState.READY

    def _touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
