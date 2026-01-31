"""
In-memory repository implementations for development and testing.

These implementations store all data in Python dictionaries and will lose
data when the server restarts. Use the SQLAlchemy repositories for production.
"""

from uuid import UUID

from app.domain import Author, Download, Ebook, Manuscript, Sample


class InMemoryAuthorRepository:
    def __init__(self) -> None:
        self._store: dict[UUID, Author] = {}
        self._email_index: dict[str, UUID] = {}

    def add(self, author: Author) -> Author:
        self._store[author.id] = author
        self._email_index[author.email] = author.id
        return author

    def get(self, author_id: UUID) -> Author | None:
        return self._store.get(author_id)

    def get_by_email(self, email: str) -> Author | None:
        author_id = self._email_index.get(email)
        if author_id is None:
            return None
        return self._store.get(author_id)

    def update(self, author: Author) -> Author:
        old_author = self._store.get(author.id)
        if old_author and old_author.email != author.email:
            del self._email_index[old_author.email]
            self._email_index[author.email] = author.id
        self._store[author.id] = author
        return author

    def delete(self, author_id: UUID) -> None:
        author = self._store.pop(author_id, None)
        if author:
            self._email_index.pop(author.email, None)


class InMemoryManuscriptRepository:
    def __init__(self) -> None:
        self._store: dict[UUID, Manuscript] = {}

    def add(self, manuscript: Manuscript) -> Manuscript:
        self._store[manuscript.id] = manuscript
        return manuscript

    def get(self, manuscript_id: UUID) -> Manuscript | None:
        return self._store.get(manuscript_id)

    def list_by_author(self, author_id: UUID) -> list[Manuscript]:
        return [m for m in self._store.values() if m.author_id == author_id]

    def update(self, manuscript: Manuscript) -> Manuscript:
        self._store[manuscript.id] = manuscript
        return manuscript

    def delete(self, manuscript_id: UUID) -> None:
        self._store.pop(manuscript_id, None)


class InMemorySampleRepository:
    def __init__(self) -> None:
        self._store: dict[UUID, Sample] = {}

    def add(self, sample: Sample) -> Sample:
        self._store[sample.id] = sample
        return sample

    def get(self, sample_id: UUID) -> Sample | None:
        return self._store.get(sample_id)

    def list_by_manuscript(self, manuscript_id: UUID) -> list[Sample]:
        return [s for s in self._store.values() if s.manuscript_id == manuscript_id]

    def update(self, sample: Sample) -> Sample:
        self._store[sample.id] = sample
        return sample

    def delete(self, sample_id: UUID) -> None:
        self._store.pop(sample_id, None)


class InMemoryEbookRepository:
    def __init__(self) -> None:
        self._store: dict[UUID, Ebook] = {}
        self._manuscript_to_author: dict[UUID, UUID] = {}

    def set_manuscript_author(self, manuscript_id: UUID, author_id: UUID) -> None:
        """Helper to track manuscript -> author mapping for list_by_author."""
        self._manuscript_to_author[manuscript_id] = author_id

    def add(self, ebook: Ebook) -> Ebook:
        self._store[ebook.id] = ebook
        return ebook

    def get(self, ebook_id: UUID) -> Ebook | None:
        return self._store.get(ebook_id)

    def list_by_manuscript(self, manuscript_id: UUID) -> list[Ebook]:
        return [e for e in self._store.values() if e.manuscript_id == manuscript_id]

    def list_by_author(self, author_id: UUID) -> list[Ebook]:
        return [
            e
            for e in self._store.values()
            if self._manuscript_to_author.get(e.manuscript_id) == author_id
        ]

    def update(self, ebook: Ebook) -> Ebook:
        self._store[ebook.id] = ebook
        return ebook

    def delete(self, ebook_id: UUID) -> None:
        self._store.pop(ebook_id, None)

    def delete_by_manuscript(self, manuscript_id: UUID) -> None:
        to_delete = [e.id for e in self._store.values() if e.manuscript_id == manuscript_id]
        for ebook_id in to_delete:
            self._store.pop(ebook_id, None)


class InMemoryDownloadRepository:
    def __init__(self) -> None:
        self._store: dict[UUID, Download] = {}

    def add(self, download: Download) -> Download:
        self._store[download.id] = download
        return download

    def get(self, download_id: UUID) -> Download | None:
        return self._store.get(download_id)

    def list_by_ebook(self, ebook_id: UUID) -> list[Download]:
        return [d for d in self._store.values() if d.ebook_id == ebook_id]

    def count_by_ebook(self, ebook_id: UUID) -> int:
        return len([d for d in self._store.values() if d.ebook_id == ebook_id])
