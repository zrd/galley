"""
In-memory repository implementations for development and testing.

These implementations store all data in Python dictionaries and will lose
data when the server restarts. Use the SQLAlchemy repositories for production.
"""

from datetime import datetime, timezone
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

    def get(self, author_id: UUID, *, include_deleted: bool = False) -> Author | None:
        author = self._store.get(author_id)
        if author is None:
            return None
        if not include_deleted and author.is_deleted:
            return None
        return author

    def get_by_email(self, email: str, *, include_deleted: bool = False) -> Author | None:
        author_id = self._email_index.get(email)
        if author_id is None:
            return None
        author = self._store.get(author_id)
        if author is None:
            return None
        if not include_deleted and author.is_deleted:
            return None
        return author

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

    def soft_delete(self, author_id: UUID) -> None:
        author = self._store.get(author_id)
        if author:
            author.soft_delete()

    def restore(self, author_id: UUID) -> None:
        author = self._store.get(author_id)
        if author:
            author.restore()


class InMemoryManuscriptRepository:
    def __init__(self) -> None:
        self._store: dict[UUID, Manuscript] = {}

    def add(self, manuscript: Manuscript) -> Manuscript:
        self._store[manuscript.id] = manuscript
        return manuscript

    def get(self, manuscript_id: UUID, *, include_deleted: bool = False) -> Manuscript | None:
        manuscript = self._store.get(manuscript_id)
        if manuscript is None:
            return None
        if not include_deleted and manuscript.is_deleted:
            return None
        return manuscript

    def list_by_author(self, author_id: UUID, *, include_deleted: bool = False) -> list[Manuscript]:
        manuscripts = [m for m in self._store.values() if m.author_id == author_id]
        if not include_deleted:
            manuscripts = [m for m in manuscripts if not m.is_deleted]
        return manuscripts

    def update(self, manuscript: Manuscript) -> Manuscript:
        self._store[manuscript.id] = manuscript
        return manuscript

    def delete(self, manuscript_id: UUID) -> None:
        self._store.pop(manuscript_id, None)

    def soft_delete(self, manuscript_id: UUID) -> None:
        manuscript = self._store.get(manuscript_id)
        if manuscript:
            manuscript.soft_delete()

    def restore(self, manuscript_id: UUID) -> None:
        manuscript = self._store.get(manuscript_id)
        if manuscript:
            manuscript.restore()


class InMemorySampleRepository:
    def __init__(self) -> None:
        self._store: dict[UUID, Sample] = {}

    def add(self, sample: Sample) -> Sample:
        self._store[sample.id] = sample
        return sample

    def get(self, sample_id: UUID, *, include_deleted: bool = False) -> Sample | None:
        sample = self._store.get(sample_id)
        if sample is None:
            return None
        if not include_deleted and sample.is_deleted:
            return None
        return sample

    def list_by_manuscript(self, manuscript_id: UUID, *, include_deleted: bool = False) -> list[Sample]:
        samples = [s for s in self._store.values() if s.manuscript_id == manuscript_id]
        if not include_deleted:
            samples = [s for s in samples if not s.is_deleted]
        return samples

    def update(self, sample: Sample) -> Sample:
        self._store[sample.id] = sample
        return sample

    def delete(self, sample_id: UUID) -> None:
        self._store.pop(sample_id, None)

    def soft_delete(self, sample_id: UUID) -> None:
        sample = self._store.get(sample_id)
        if sample:
            sample.soft_delete()

    def soft_delete_by_manuscript(self, manuscript_id: UUID) -> None:
        for sample in self._store.values():
            if sample.manuscript_id == manuscript_id and not sample.is_deleted:
                sample.soft_delete()

    def restore(self, sample_id: UUID) -> None:
        sample = self._store.get(sample_id)
        if sample:
            sample.restore()

    def restore_by_manuscript(self, manuscript_id: UUID) -> None:
        for sample in self._store.values():
            if sample.manuscript_id == manuscript_id and sample.is_deleted:
                sample.restore()


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

    def get(self, ebook_id: UUID, *, include_deleted: bool = False) -> Ebook | None:
        ebook = self._store.get(ebook_id)
        if ebook is None:
            return None
        if not include_deleted and ebook.is_deleted:
            return None
        return ebook

    def list_by_manuscript(self, manuscript_id: UUID, *, include_deleted: bool = False) -> list[Ebook]:
        ebooks = [e for e in self._store.values() if e.manuscript_id == manuscript_id]
        if not include_deleted:
            ebooks = [e for e in ebooks if not e.is_deleted]
        return ebooks

    def list_by_author(self, author_id: UUID, *, include_deleted: bool = False) -> list[Ebook]:
        ebooks = [
            e
            for e in self._store.values()
            if self._manuscript_to_author.get(e.manuscript_id) == author_id
        ]
        if not include_deleted:
            ebooks = [e for e in ebooks if not e.is_deleted]
        return ebooks

    def list_by_sample(self, sample_id: UUID, *, include_deleted: bool = False) -> list[Ebook]:
        ebooks = [e for e in self._store.values() if e.sample_id == sample_id]
        if not include_deleted:
            ebooks = [e for e in ebooks if not e.is_deleted]
        return ebooks

    def update(self, ebook: Ebook) -> Ebook:
        self._store[ebook.id] = ebook
        return ebook

    def delete(self, ebook_id: UUID) -> None:
        self._store.pop(ebook_id, None)

    def delete_by_manuscript(self, manuscript_id: UUID) -> None:
        to_delete = [e.id for e in self._store.values() if e.manuscript_id == manuscript_id]
        for ebook_id in to_delete:
            self._store.pop(ebook_id, None)

    def soft_delete(self, ebook_id: UUID) -> None:
        ebook = self._store.get(ebook_id)
        if ebook:
            ebook.soft_delete()

    def soft_delete_by_manuscript(self, manuscript_id: UUID) -> None:
        for ebook in self._store.values():
            if ebook.manuscript_id == manuscript_id and not ebook.is_deleted:
                ebook.soft_delete()

    def soft_delete_by_sample(self, sample_id: UUID) -> None:
        for ebook in self._store.values():
            if ebook.sample_id == sample_id and not ebook.is_deleted:
                ebook.soft_delete()

    def restore(self, ebook_id: UUID) -> None:
        ebook = self._store.get(ebook_id)
        if ebook:
            ebook.restore()

    def restore_by_manuscript(self, manuscript_id: UUID) -> None:
        for ebook in self._store.values():
            if ebook.manuscript_id == manuscript_id and ebook.is_deleted:
                ebook.restore()

    def restore_by_sample(self, sample_id: UUID) -> None:
        for ebook in self._store.values():
            if ebook.sample_id == sample_id and ebook.is_deleted:
                ebook.restore()


class InMemoryDownloadRepository:
    def __init__(self) -> None:
        self._store: dict[UUID, Download] = {}

    def add(self, download: Download) -> Download:
        self._store[download.id] = download
        return download

    def get(self, download_id: UUID, *, include_deleted: bool = False) -> Download | None:
        download = self._store.get(download_id)
        if download is None:
            return None
        if not include_deleted and download.is_deleted:
            return None
        return download

    def list_by_ebook(self, ebook_id: UUID, *, include_deleted: bool = False) -> list[Download]:
        downloads = [d for d in self._store.values() if d.ebook_id == ebook_id]
        if not include_deleted:
            downloads = [d for d in downloads if not d.is_deleted]
        return downloads

    def count_by_ebook(self, ebook_id: UUID, *, include_deleted: bool = False) -> int:
        downloads = [d for d in self._store.values() if d.ebook_id == ebook_id]
        if not include_deleted:
            downloads = [d for d in downloads if not d.is_deleted]
        return len(downloads)
