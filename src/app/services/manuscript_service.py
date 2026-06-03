from uuid import UUID

from app.domain import Manuscript, ManuscriptNotFound, SourceFormat
from app.repositories.protocols import EbookRepository, ManuscriptRepository, SampleRepository, TagRepository


class ManuscriptService:
    def __init__(
        self,
        repo: ManuscriptRepository,
        sample_repo: SampleRepository | None = None,
        ebook_repo: EbookRepository | None = None,
        tag_repo: TagRepository | None = None,
    ) -> None:
        self.repo = repo
        self.sample_repo = sample_repo
        self.ebook_repo = ebook_repo
        self.tag_repo = tag_repo

    def create(
        self,
        author_id: UUID,
        title: str,
        source_format: SourceFormat,
        source_file_key: str,
        genre_ids: list[int] | None = None,
        tag_names: list[str] | None = None,
        description: str | None = None,
    ) -> Manuscript:
        manuscript = Manuscript(
            author_id=author_id,
            title=title,
            source_format=source_format,
            source_file_key=source_file_key,
            description=description
        )
        created = self.repo.add(manuscript)
        if genre_ids:
            self.repo.set_genres(manuscript_id=created.id, genre_ids=genre_ids)

        if tag_names:
            tag_ids = [self.tag_repo.get_or_create(name=n, owner_id=author_id).id for n in tag_names]
            self.repo.set_tags(manuscript_id=created.id, tag_ids=tag_ids)

        return self.repo.get(created.id)

    def get(self, manuscript_id: UUID, *, include_deleted: bool = False) -> Manuscript:
        manuscript = self.repo.get(manuscript_id, include_deleted=include_deleted)
        if manuscript is None:
            raise ManuscriptNotFound(f"Manuscript {manuscript_id} not found")
        return manuscript

    def list_by_author(self, author_id: UUID, *, include_deleted: bool = False) -> list[Manuscript]:
        return self.repo.list_by_author(author_id, include_deleted=include_deleted)

    def update_metadata(
        self,
        manuscript_id: UUID,
        author_id: UUID,
        title: str | None = None,
        description: str | None = None,
        genre_ids: list[int] | None = None,
        tag_names: list[str] | None = None,
    ) -> Manuscript:
        manuscript = self.get(manuscript_id)
        manuscript.update_metadata(title=title, description=description)
        updated = self.repo.update(manuscript)
        if genre_ids is not None:
            self.repo.set_genres(manuscript_id=updated.id, genre_ids=genre_ids)

        if tag_names is not None:
            tag_ids = [self.tag_repo.get_or_create(name=n, owner_id=author_id).id for n in tag_names]
            self.repo.set_tags(manuscript_id=updated.id, tag_ids=tag_ids)

        return self.repo.get(updated.id)

    def update_source(
        self,
        manuscript_id: UUID,
        source_file_key: str,
        source_format: SourceFormat,
    ) -> Manuscript:
        manuscript = self.get(manuscript_id)
        manuscript.update_source(source_file_key, source_format)
        return self.repo.update(manuscript)

    def mark_ready(self, manuscript_id: UUID) -> Manuscript:
        manuscript = self.get(manuscript_id)
        manuscript.mark_ready()
        return self.repo.update(manuscript)

    def archive(self, manuscript_id: UUID) -> Manuscript:
        manuscript = self.get(manuscript_id)
        manuscript.archive()
        return self.repo.update(manuscript)

    def unarchive(self, manuscript_id: UUID) -> Manuscript:
        manuscript = self.get(manuscript_id)
        manuscript.unarchive()
        return self.repo.update(manuscript)

    def delete(self, manuscript_id: UUID) -> None:
        self.repo.delete(manuscript_id)

    def soft_delete(self, manuscript_id: UUID) -> None:
        """Soft delete manuscript and cascade to samples and ebooks."""
        # Verify manuscript exists
        self.get(manuscript_id)

        # Cascade soft delete to samples and ebooks
        if self.sample_repo:
            self.sample_repo.soft_delete_by_manuscript(manuscript_id)
        if self.ebook_repo:
            self.ebook_repo.soft_delete_by_manuscript(manuscript_id)

        # Soft delete the manuscript itself
        self.repo.soft_delete(manuscript_id)

    def restore(self, manuscript_id: UUID) -> None:
        """Restore manuscript and cascade restore to samples and ebooks."""
        # Get including deleted to verify it exists
        self.get(manuscript_id, include_deleted=True)

        # Restore manuscript first
        self.repo.restore(manuscript_id)

        # Cascade restore to samples and ebooks
        if self.sample_repo:
            self.sample_repo.restore_by_manuscript(manuscript_id)
        if self.ebook_repo:
            self.ebook_repo.restore_by_manuscript(manuscript_id)

    def check_ownership(self, manuscript_id: UUID, author_id: UUID, *, include_deleted: bool = False) -> bool:
        manuscript = self.repo.get(manuscript_id, include_deleted=include_deleted)
        return manuscript is not None and manuscript.author_id == author_id

    def update_cover(self, manuscript_id: UUID, cover_image_key: str) -> Manuscript:
        manuscript = self.get(manuscript_id)
        manuscript.set_cover(cover_image_key)
        return self.repo.update(manuscript)

    def remove_cover(self, manuscript_id: UUID) -> Manuscript:
        manuscript = self.get(manuscript_id)
        manuscript.remove_cover()
        return self.repo.update(manuscript)
