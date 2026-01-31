from uuid import UUID

from app.domain import Sample, SampleNotFound
from app.repositories import InMemorySampleRepository


class SampleService:
    def __init__(self, repo: InMemorySampleRepository) -> None:
        self.repo = repo

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

    def get(self, sample_id: UUID) -> Sample:
        sample = self.repo.get(sample_id)
        if sample is None:
            raise SampleNotFound(f"Sample {sample_id} not found")
        return sample

    def list_by_manuscript(self, manuscript_id: UUID) -> list[Sample]:
        return self.repo.list_by_manuscript(manuscript_id)

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
