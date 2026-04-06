"""
Tests for domain entities and business logic.
"""

import pytest

from datetime import datetime, timezone

from app.domain import (
    Author,
    Ebook,
    InvalidStateTransition,
    Manuscript,
    ManuscriptState,
    OutputFormat,
    Sample,
    SourceFormat,
    Tag,
    Visibility,
)


class TestTag:
    def test_create_tag(self):
        tag = Tag(name="Hard Sci-Fi", slug="hard-sci-fi")

        assert tag.name == "Hard Sci-Fi"
        assert tag.slug == "hard-sci-fi"
        assert tag.id is not None
        assert tag.deleted_at is None
        assert not tag.is_deleted

    def test_is_deleted_false_when_active(self):
        tag = Tag(name="Cozy Mystery", slug="cozy-mystery")
        assert not tag.is_deleted

    def test_is_deleted_true_when_deleted(self):
        tag = Tag(
            name="Cozy Mystery",
            slug="cozy-mystery",
            deleted_at=datetime.now(timezone.utc),
        )
        assert tag.is_deleted

    def test_created_at_defaults_to_now(self):
        before = datetime.now(timezone.utc)
        tag = Tag(name="Fantasy", slug="fantasy")
        after = datetime.now(timezone.utc)

        assert before <= tag.created_at <= after

    def test_owner_id_defaults_to_none(self):
        tag = Tag(name="Fantasy", slug="fantasy")
        assert tag.owner_id is None

    def test_soft_delete_sets_deleted_at(self):
        tag = Tag(name="Fantasy", slug="fantasy")
        assert tag.deleted_at is None

        tag.soft_delete()

        assert tag.deleted_at is not None
        assert tag.is_deleted

    def test_restore_clears_deleted_at(self):
        tag = Tag(name="Fantasy", slug="fantasy", deleted_at=datetime.now(timezone.utc))
        assert tag.is_deleted

        tag.restore()

        assert tag.deleted_at is None
        assert not tag.is_deleted

    def test_manuscript_tags_defaults_to_empty_list(self):
        from uuid import uuid4
        manuscript = Manuscript(
            author_id=uuid4(),
            title="Test Book",
            source_format=SourceFormat.EPUB,
            source_file_key="manuscripts/test.epub",
        )
        assert manuscript.tags == []


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
        assert not ebook.is_sample

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
        assert not full_ebook.is_sample

        sample_ebook = Ebook(
            manuscript_id=uuid4(),
            output_format=OutputFormat.EPUB,
            file_key="samples/test.epub",
            file_size_bytes=512,
            download_filename="Test Author - Test Book (Sample).epub",
            sample_id=uuid4(),
        )
        assert sample_ebook.is_sample

    def test_effective_price_no_prices(self):
        from uuid import uuid4

        ebook = Ebook(
            manuscript_id=uuid4(),
            output_format=OutputFormat.EPUB,
            file_key="ebooks/test.epub",
            file_size_bytes=1024,
            download_filename="Test Author - Test Book.epub",
        )
        assert ebook.effective_price_cents == 0

    def test_effective_price_list_only(self):
        from uuid import uuid4

        ebook = Ebook(
            manuscript_id=uuid4(),
            output_format=OutputFormat.EPUB,
            file_key="ebooks/test.epub",
            file_size_bytes=1024,
            download_filename="Test Author - Test Book.epub",
            list_price_cents=999,
        )
        assert ebook.effective_price_cents == 999

    def test_effective_price_sale_overrides_list(self):
        from uuid import uuid4

        ebook = Ebook(
            manuscript_id=uuid4(),
            output_format=OutputFormat.EPUB,
            file_key="ebooks/test.epub",
            file_size_bytes=1024,
            download_filename="Test Author - Test Book.epub",
            list_price_cents=999,
            sale_price_cents=799,
        )
        assert ebook.effective_price_cents == 799

    def test_effective_price_free_sale_overrides_list(self):
        # sale_price=0 must not be treated as falsy and fall through to list_price
        from uuid import uuid4

        ebook = Ebook(
            manuscript_id=uuid4(),
            output_format=OutputFormat.EPUB,
            file_key="ebooks/test.epub",
            file_size_bytes=1024,
            download_filename="Test Author - Test Book.epub",
            list_price_cents=999,
            sale_price_cents=0,
        )
        assert ebook.effective_price_cents == 0

    def test_is_free_no_prices(self):
        from uuid import uuid4

        ebook = Ebook(
            manuscript_id=uuid4(),
            output_format=OutputFormat.EPUB,
            file_key="ebooks/test.epub",
            file_size_bytes=1024,
            download_filename="Test Author - Test Book.epub",
        )
        assert ebook.is_free

    def test_is_free_zero_list_price(self):
        from uuid import uuid4

        ebook = Ebook(
            manuscript_id=uuid4(),
            output_format=OutputFormat.EPUB,
            file_key="ebooks/test.epub",
            file_size_bytes=1024,
            download_filename="Test Author - Test Book.epub",
            list_price_cents=0,
        )
        assert ebook.is_free

    def test_is_not_free_when_priced(self):
        from uuid import uuid4

        ebook = Ebook(
            manuscript_id=uuid4(),
            output_format=OutputFormat.EPUB,
            file_key="ebooks/test.epub",
            file_size_bytes=1024,
            download_filename="Test Author - Test Book.epub",
            list_price_cents=999,
        )
        assert not ebook.is_free

    def test_formatted_price_free(self):
        from uuid import uuid4

        ebook = Ebook(
            manuscript_id=uuid4(),
            output_format=OutputFormat.EPUB,
            file_key="ebooks/test.epub",
            file_size_bytes=1024,
            download_filename="Test Author - Test Book.epub",
        )
        assert ebook.formatted_price == "Free"

    def test_formatted_price(self):
        from uuid import uuid4

        ebook = Ebook(
            manuscript_id=uuid4(),
            output_format=OutputFormat.EPUB,
            file_key="ebooks/test.epub",
            file_size_bytes=1024,
            download_filename="Test Author - Test Book.epub",
            list_price_cents=999,
        )
        assert ebook.formatted_price == "$9.99"

    def test_formatted_price_zero_padding(self):
        # Regression: 901 cents must render as $9.01 not $9.1
        from uuid import uuid4

        ebook = Ebook(
            manuscript_id=uuid4(),
            output_format=OutputFormat.EPUB,
            file_key="ebooks/test.epub",
            file_size_bytes=1024,
            download_filename="Test Author - Test Book.epub",
            list_price_cents=901,
        )
        assert ebook.formatted_price == "$9.01"

    def test_formatted_price_zero_padding_pre(self):
        from uuid import uuid4

        ebook = Ebook(
            manuscript_id=uuid4(),
            output_format=OutputFormat.EPUB,
            file_key="ebooks/test.epub",
            file_size_bytes=1024,
            download_filename="Test Author - Test Book.epub",
            list_price_cents=91,
        )
        assert ebook.formatted_price == "$0.91"


class TestEbookVisibility:
    @pytest.fixture
    def ebook(self):
        from uuid import uuid4
        return Ebook(
            manuscript_id=uuid4(),
            output_format=OutputFormat.EPUB,
            file_key="ebooks/test.epub",
            file_size_bytes=1024,
            download_filename="Test Author - Test Book.epub",
        )

    def test_default_visibility_is_private(self, ebook):
        assert ebook.visibility == Visibility.PRIVATE

    def test_default_published_at_is_none(self, ebook):
        assert ebook.published_at is None

    def test_default_unlisted_download_limit_is_none(self, ebook):
        assert ebook.unlisted_download_limit is None

    def test_publish_sets_visibility(self, ebook):
        ebook.publish()
        assert ebook.visibility == Visibility.PUBLISHED

    def test_publish_sets_published_at(self, ebook):
        before = datetime.now(timezone.utc)
        ebook.publish()
        after = datetime.now(timezone.utc)
        assert before <= ebook.published_at <= after

    def test_publish_twice_does_not_reset_published_at(self, ebook):
        ebook.publish()
        first_published_at = ebook.published_at

        ebook.make_private()
        ebook.publish()

        assert ebook.published_at == first_published_at

    def test_unlist_sets_visibility(self, ebook):
        ebook.unlist()
        assert ebook.visibility == Visibility.UNLISTED

    def test_unlist_does_not_set_published_at(self, ebook):
        ebook.unlist()
        assert ebook.published_at is None

    def test_make_private_sets_visibility(self, ebook):
        ebook.publish()
        ebook.make_private()
        assert ebook.visibility == Visibility.PRIVATE

    def test_make_private_does_not_clear_published_at(self, ebook):
        ebook.publish()
        published_at = ebook.published_at
        ebook.make_private()
        assert ebook.published_at == published_at

    def test_full_transition_cycle(self, ebook):
        ebook.publish()
        assert ebook.visibility == Visibility.PUBLISHED

        ebook.unlist()
        assert ebook.visibility == Visibility.UNLISTED

        ebook.publish()
        assert ebook.visibility == Visibility.PUBLISHED

        ebook.make_private()
        assert ebook.visibility == Visibility.PRIVATE
