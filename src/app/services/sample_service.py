from uuid import UUID

from app.domain import Sample, SampleNotFound
from app.repositories import EbookRepository, SampleRepository


class SampleService:
    def __init__(self, repo: SampleRepository, ebook_repo: EbookRepository | None = None) -> None:
        self.repo = repo
        self.ebook_repo = ebook_repo

    def create(
        self,
        manuscript_id: UUID,
        title: str,
        excerpt_start: str,
        excerpt_end: str,
        promo_header: str | None = None,
        promo_footer: str | None = None,
    ) -> Sample:
        sample = Sample(
            manuscript_id=manuscript_id,
            title=title,
            excerpt_start=excerpt_start,
            excerpt_end=excerpt_end,
            promo_header=promo_header,
            promo_footer=promo_footer,
        )
        return self.repo.add(sample)

    def get(self, sample_id: UUID, *, include_deleted: bool = False) -> Sample:
        sample = self.repo.get(sample_id, include_deleted=include_deleted)
        if sample is None:
            raise SampleNotFound(f"Sample {sample_id} not found")
        return sample

    def list_by_manuscript(self, manuscript_id: UUID, *, include_deleted: bool = False) -> list[Sample]:
        return self.repo.list_by_manuscript(manuscript_id, include_deleted=include_deleted)

    def update(
        self,
        sample_id: UUID,
        title: str | None = None,
        excerpt_start: str | None = None,
        excerpt_end: str | None = None,
        promo_header: str | None = None,
        promo_footer: str | None = None,
    ) -> Sample:
        sample = self.get(sample_id)
        sample.update(
            title=title,
            excerpt_start=excerpt_start,
            excerpt_end=excerpt_end,
            promo_header=promo_header,
            promo_footer=promo_footer,
        )
        return self.repo.update(sample)

    def delete(self, sample_id: UUID) -> None:
        self.repo.delete(sample_id)

    def soft_delete(self, sample_id: UUID) -> None:
        """Soft delete sample and cascade to sample ebooks."""
        # Verify sample exists
        self.get(sample_id)

        # Cascade soft delete to ebooks generated from this sample
        if self.ebook_repo:
            self.ebook_repo.soft_delete_by_sample(sample_id)

        # Soft delete the sample itself
        self.repo.soft_delete(sample_id)

    def restore(self, sample_id: UUID) -> None:
        """Restore sample and cascade restore to sample ebooks."""
        # Get including deleted to verify it exists
        self.get(sample_id, include_deleted=True)

        # Restore sample first
        self.repo.restore(sample_id)

        # Cascade restore to sample ebooks
        if self.ebook_repo:
            self.ebook_repo.restore_by_sample(sample_id)
