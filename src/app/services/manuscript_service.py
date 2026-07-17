import logging
from uuid import UUID

from app.domain import Manuscript, ManuscriptNotFound, SourceFormat
from app.repositories import EbookRepository, ManuscriptRepository, SampleRepository, TagRepository
from app.storage import (
    generate_file_key,
    get_content_type_for_format,
    get_storage_backend,
    validate_image,
)

logger = logging.getLogger(__name__)


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

    async def create(
        self,
        author_id: UUID,
        title: str,
        source_format: SourceFormat,
        filename: str,
        content: bytes,
        genre_ids: list[int] | None = None,
        tag_names: list[str] | None = None,
        description: str | None = None,
    ) -> Manuscript:
        source_file_key = generate_file_key(author_id, filename, "manuscripts", reject_unsafe=True)
        content_type = get_content_type_for_format(source_format.value)
        storage = get_storage_backend()
        await storage.upload(source_file_key, content, content_type)
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

    async def update_source(
        self,
        manuscript_id: UUID,
        author_id: UUID,
        source_format: SourceFormat,
        filename: str,
        content: bytes,
    ) -> Manuscript:
        manuscript = self.get(manuscript_id)
        old_source_key = manuscript.source_file_key
        file_key = generate_file_key(author_id, filename, "manuscripts", reject_unsafe=True)
        content_type = get_content_type_for_format(source_format.value)
        storage = get_storage_backend()
        await storage.upload(file_key, content, content_type)
        manuscript.update_source(file_key, source_format)
        updated = self.repo.update(manuscript)
        try:
            await storage.delete(old_source_key)
        except Exception as e:
            logger.warning(f"Failed to delete old source file {old_source_key}: {e}")

        return updated

    def mark_ready(self, manuscript_id: UUID) -> Manuscript:
        manuscript = self.get(manuscript_id)
        manuscript.mark_ready()
        return self.repo.update(manuscript)

    def mark_draft(self, manuscript_id: UUID) -> Manuscript:
        manuscript = self.get(manuscript_id)
        manuscript.mark_draft()
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

    async def update_cover(
        self,
        manuscript_id: UUID,
        author_id: UUID,
        cover_image_filename: str,
        cover_image_content: bytes,
    ) -> Manuscript:
        manuscript = self.get(manuscript_id)
        content_type = validate_image(cover_image_content)
        format_extension = {"image/jpeg": "jpg", "image/png": "png"}[content_type]
        if cover_image_filename:
            extension = cover_image_filename.split(".")[-1]
            if extension.lower() != format_extension:
                cover_image_filename = cover_image_filename + f".{format_extension}"

        filename = cover_image_filename or f"cover.{format_extension}"
        file_key = generate_file_key(author_id, filename, "covers", reject_unsafe=True)

        storage = get_storage_backend()
        await storage.upload(file_key, cover_image_content, content_type)
        existing_cover = manuscript.cover_image_key
        manuscript.set_cover(file_key)
        updated = self.repo.update(manuscript)
        if existing_cover:
            try:
                await storage.delete(existing_cover)
            except Exception as e:
                logger.warning(f"Failed to delete old cover {existing_cover}: {e}")

        return updated

    async def remove_cover(self, manuscript_id: UUID) -> Manuscript:
        manuscript = self.get(manuscript_id)
        existing_cover = manuscript.cover_image_key
        storage = get_storage_backend()
        if existing_cover:
            try:
                await storage.delete(existing_cover)
            except Exception as e:
                logger.warning(f"Failed to delete cover {existing_cover}: {e}")
        manuscript.remove_cover()
        return self.repo.update(manuscript)
