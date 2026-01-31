from uuid import UUID

from app.domain import Manuscript, ManuscriptNotFound, ManuscriptState, SourceFormat
from app.repositories import InMemoryManuscriptRepository


class ManuscriptService:
    def __init__(self, repo: InMemoryManuscriptRepository) -> None:
        self.repo = repo

    def create(
        self,
        author_id: UUID,
        title: str,
        source_format: SourceFormat,
        source_file_key: str,
        description: str | None = None,
    ) -> Manuscript:
        manuscript = Manuscript(
            author_id=author_id,
            title=title,
            source_format=source_format,
            source_file_key=source_file_key,
            description=description,
        )
        return self.repo.add(manuscript)

    def get(self, manuscript_id: UUID) -> Manuscript:
        manuscript = self.repo.get(manuscript_id)
        if manuscript is None:
            raise ManuscriptNotFound(f"Manuscript {manuscript_id} not found")
        return manuscript

    def list_by_author(self, author_id: UUID) -> list[Manuscript]:
        return self.repo.list_by_author(author_id)

    def update_metadata(
        self,
        manuscript_id: UUID,
        title: str | None = None,
        description: str | None = None,
    ) -> Manuscript:
        manuscript = self.get(manuscript_id)
        manuscript.update_metadata(title=title, description=description)
        return self.repo.update(manuscript)

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

    def delete(self, manuscript_id: UUID) -> None:
        self.repo.delete(manuscript_id)

    def check_ownership(self, manuscript_id: UUID, author_id: UUID) -> bool:
        manuscript = self.repo.get(manuscript_id)
        return manuscript is not None and manuscript.author_id == author_id
