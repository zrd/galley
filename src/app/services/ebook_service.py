from uuid import UUID

from app.domain import Ebook, EbookNotFound, OutputFormat
from app.repositories.protocols import EbookRepository


class EbookService:
    def __init__(self, repo: EbookRepository) -> None:
        self.repo = repo

    def create(
        self,
        manuscript_id: UUID,
        output_format: OutputFormat,
        file_key: str,
        file_size_bytes: int,
        sample_id: UUID | None = None,
    ) -> Ebook:
        ebook = Ebook(
            manuscript_id=manuscript_id,
            output_format=output_format,
            file_key=file_key,
            file_size_bytes=file_size_bytes,
            sample_id=sample_id,
        )
        return self.repo.add(ebook)

    def get(self, ebook_id: UUID, *, include_deleted: bool = False) -> Ebook:
        ebook = self.repo.get(ebook_id, include_deleted=include_deleted)
        if ebook is None:
            raise EbookNotFound(f"Ebook {ebook_id} not found")
        return ebook

    def list_by_author(self, author_id: UUID, *, include_deleted: bool = False) -> list[Ebook]:
        return self.repo.list_by_author(author_id, include_deleted=include_deleted)

    def list_by_manuscript(self, manuscript_id: UUID, *, include_deleted: bool = False) -> list[Ebook]:
        return self.repo.list_by_manuscript(manuscript_id, include_deleted=include_deleted)

    def increment_download(self, ebook_id: UUID) -> Ebook:
        ebook = self.get(ebook_id)
        ebook.increment_download_count()
        return self.repo.update(ebook)

    def delete(self, ebook_id: UUID) -> None:
        self.repo.delete(ebook_id)

    def delete_by_manuscript(self, manuscript_id: UUID) -> None:
        self.repo.delete_by_manuscript(manuscript_id)

    def soft_delete(self, ebook_id: UUID) -> None:
        """Soft delete a single ebook."""
        # Verify ebook exists
        self.get(ebook_id)
        self.repo.soft_delete(ebook_id)

    def restore(self, ebook_id: UUID) -> None:
        """Restore a soft-deleted ebook."""
        # Get including deleted to verify it exists
        self.get(ebook_id, include_deleted=True)
        self.repo.restore(ebook_id)
