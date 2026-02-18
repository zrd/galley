"""
Tests for domain entities and business logic.
"""

import pytest

from app.domain import (
    Author,
    Ebook,
    InvalidStateTransition,
    Manuscript,
    ManuscriptState,
    OutputFormat,
    Sample,
    SourceFormat,
)


class TestManuscript:
    def test_create_manuscript(self):
        from uuid import uuid4

        manuscript = Manuscript(
            author_id=uuid4(),
            title="Test Book",
            source_format=SourceFormat.EPUB,
            source_file_key="manuscripts/test.epub",
        )

        assert manuscript.title == "Test Book"
        assert manuscript.state == ManuscriptState.DRAFT
        assert manuscript.source_format == SourceFormat.EPUB

    def test_mark_ready(self):
        from uuid import uuid4

        manuscript = Manuscript(
            author_id=uuid4(),
            title="Test Book",
            source_format=SourceFormat.EPUB,
            source_file_key="manuscripts/test.epub",
        )

        manuscript.mark_ready()
        assert manuscript.state == ManuscriptState.READY

    def test_cannot_mark_ready_twice(self):
        from uuid import uuid4

        manuscript = Manuscript(
            author_id=uuid4(),
            title="Test Book",
            source_format=SourceFormat.EPUB,
            source_file_key="manuscripts/test.epub",
        )

        manuscript.mark_ready()

        with pytest.raises(InvalidStateTransition):
            manuscript.mark_ready()

    def test_can_generate_ebook_only_when_ready(self):
        from uuid import uuid4

        manuscript = Manuscript(
            author_id=uuid4(),
            title="Test Book",
            source_format=SourceFormat.EPUB,
            source_file_key="manuscripts/test.epub",
        )

        assert not manuscript.can_generate_ebook()

        manuscript.mark_ready()
        assert manuscript.can_generate_ebook()

    def test_archive_and_unarchive(self):
        from uuid import uuid4

        manuscript = Manuscript(
            author_id=uuid4(),
            title="Test Book",
            source_format=SourceFormat.EPUB,
            source_file_key="manuscripts/test.epub",
        )

        manuscript.mark_ready()
        manuscript.archive()
        assert manuscript.state == ManuscriptState.ARCHIVED

        manuscript.unarchive()
        assert manuscript.state == ManuscriptState.READY


class TestSample:
    def test_create_sample(self):
        from uuid import uuid4

        sample = Sample(
            manuscript_id=uuid4(),
            title="Free Preview",
            excerpt_start="Chapter 1",
            excerpt_end="Chapter 3",
            promo_header="Get the full book at...",
        )

        assert sample.title == "Free Preview"
        assert sample.excerpt_start == "Chapter 1"
        assert sample.promo_header == "Get the full book at..."


class TestEbook:
    def test_create_ebook(self):
        from uuid import uuid4

        ebook = Ebook(
            manuscript_id=uuid4(),
            output_format=OutputFormat.EPUB,
            file_key="ebooks/test.epub",
            file_size_bytes=1024,
            download_filename="Test Author - Test Book.epub",
        )

        assert ebook.output_format == OutputFormat.EPUB
        assert ebook.download_count == 0
        assert not ebook.is_sample()

    def test_increment_download(self):
        from uuid import uuid4

        ebook = Ebook(
            manuscript_id=uuid4(),
            output_format=OutputFormat.EPUB,
            file_key="ebooks/test.epub",
            file_size_bytes=1024,
            download_filename="Test Author - Test Book.epub",
        )

        ebook.increment_download_count()
        assert ebook.download_count == 1

        ebook.increment_download_count()
        assert ebook.download_count == 2

    def test_is_sample(self):
        from uuid import uuid4

        full_ebook = Ebook(
            manuscript_id=uuid4(),
            output_format=OutputFormat.EPUB,
            file_key="ebooks/test.epub",
            file_size_bytes=1024,
            download_filename="Test Author - Test Book.epub",
        )
        assert not full_ebook.is_sample()

        sample_ebook = Ebook(
            manuscript_id=uuid4(),
            output_format=OutputFormat.EPUB,
            file_key="samples/test.epub",
            file_size_bytes=512,
            download_filename="Test Author - Test Book (Sample).epub",
            sample_id=uuid4(),
        )
        assert sample_ebook.is_sample()
