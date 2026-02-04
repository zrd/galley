"""
Tests for service layer.
"""

from uuid import uuid4

import pytest

from app.domain import ManuscriptNotFound, ManuscriptState, SourceFormat
from app.repositories import (
    InMemoryAuthorRepository,
    InMemoryManuscriptRepository,
    InMemorySampleRepository,
)
from app.services import AuthorService, ManuscriptService, SampleService


class TestAuthorService:
    @pytest.fixture
    def service(self) -> AuthorService:
        repo = InMemoryAuthorRepository()
        return AuthorService(repo)

    def test_create_author(self, service: AuthorService):
        author = service.create(
            email="test@example.com",
            password_hash="hashed_password",
            display_name="Test User",
        )

        assert author.email == "test@example.com"
        assert author.display_name == "Test User"
        assert author.id is not None

    def test_get_author(self, service: AuthorService):
        created = service.create(
            email="get@example.com",
            password_hash="hash",
            display_name="Get Test",
        )

        retrieved = service.get(created.id)

        assert retrieved.id == created.id
        assert retrieved.email == created.email

    def test_get_author_by_email(self, service: AuthorService):
        created = service.create(
            email="byemail@example.com",
            password_hash="hash",
            display_name="Email Test",
        )

        retrieved = service.get_by_email("byemail@example.com")

        assert retrieved is not None
        assert retrieved.id == created.id

    def test_get_author_by_email_not_found(self, service: AuthorService):
        result = service.get_by_email("nonexistent@example.com")
        assert result is None

    def test_update_author(self, service: AuthorService):
        created = service.create(
            email="update@example.com",
            password_hash="hash",
            display_name="Original Name",
        )

        updated = service.update(created.id, display_name="New Name")

        assert updated.display_name == "New Name"
        assert updated.email == "update@example.com"


class TestManuscriptService:
    @pytest.fixture
    def service(self) -> ManuscriptService:
        repo = InMemoryManuscriptRepository()
        return ManuscriptService(repo)

    def test_create_manuscript(self, service: ManuscriptService):
        author_id = uuid4()
        manuscript = service.create(
            author_id=author_id,
            title="My Book",
            source_format=SourceFormat.EPUB,
            source_file_key="manuscripts/book.epub",
            description="A great book",
        )

        assert manuscript.title == "My Book"
        assert manuscript.author_id == author_id
        assert manuscript.state == ManuscriptState.DRAFT

    def test_get_manuscript(self, service: ManuscriptService):
        author_id = uuid4()
        created = service.create(
            author_id=author_id,
            title="Get Test",
            source_format=SourceFormat.PDF,
            source_file_key="manuscripts/book.pdf",
        )

        retrieved = service.get(created.id)

        assert retrieved.id == created.id
        assert retrieved.title == "Get Test"

    def test_get_manuscript_not_found(self, service: ManuscriptService):
        with pytest.raises(ManuscriptNotFound):
            service.get(uuid4())

    def test_list_by_author(self, service: ManuscriptService):
        author1 = uuid4()
        author2 = uuid4()

        service.create(
            author_id=author1,
            title="Author 1 Book",
            source_format=SourceFormat.EPUB,
            source_file_key="m/1.epub",
        )
        service.create(
            author_id=author2,
            title="Author 2 Book",
            source_format=SourceFormat.EPUB,
            source_file_key="m/2.epub",
        )

        author1_manuscripts = service.list_by_author(author1)
        author2_manuscripts = service.list_by_author(author2)

        assert len(author1_manuscripts) == 1
        assert author1_manuscripts[0].title == "Author 1 Book"
        assert len(author2_manuscripts) == 1
        assert author2_manuscripts[0].title == "Author 2 Book"

    def test_update_metadata(self, service: ManuscriptService):
        author_id = uuid4()
        created = service.create(
            author_id=author_id,
            title="Original",
            source_format=SourceFormat.EPUB,
            source_file_key="m/book.epub",
        )

        updated = service.update_metadata(
            created.id,
            title="Updated Title",
            description="New description",
        )

        assert updated.title == "Updated Title"
        assert updated.description == "New description"

    def test_mark_ready(self, service: ManuscriptService):
        author_id = uuid4()
        created = service.create(
            author_id=author_id,
            title="Ready Book",
            source_format=SourceFormat.EPUB,
            source_file_key="m/book.epub",
        )

        ready = service.mark_ready(created.id)

        assert ready.state == ManuscriptState.READY

    def test_check_ownership(self, service: ManuscriptService):
        author_id = uuid4()
        other_author = uuid4()

        created = service.create(
            author_id=author_id,
            title="Owned Book",
            source_format=SourceFormat.EPUB,
            source_file_key="m/book.epub",
        )

        assert service.check_ownership(created.id, author_id) is True
        assert service.check_ownership(created.id, other_author) is False
        assert service.check_ownership(uuid4(), author_id) is False

    def test_delete_manuscript(self, service: ManuscriptService):
        author_id = uuid4()
        created = service.create(
            author_id=author_id,
            title="Delete Me",
            source_format=SourceFormat.EPUB,
            source_file_key="m/book.epub",
        )

        service.delete(created.id)

        with pytest.raises(ManuscriptNotFound):
            service.get(created.id)


class TestSampleService:
    @pytest.fixture
    def service(self) -> SampleService:
        repo = InMemorySampleRepository()
        return SampleService(repo)

    def test_create_sample(self, service: SampleService):
        manuscript_id = uuid4()
        sample = service.create(
            manuscript_id=manuscript_id,
            title="Preview",
            excerpt_start="Chapter 1",
            excerpt_end="Chapter 3",
            promo_header="Free sample!",
        )

        assert sample.title == "Preview"
        assert sample.manuscript_id == manuscript_id
        assert sample.excerpt_start == "Chapter 1"
        assert sample.promo_header == "Free sample!"

    def test_list_by_manuscript(self, service: SampleService):
        manuscript1 = uuid4()
        manuscript2 = uuid4()

        service.create(
            manuscript_id=manuscript1,
            title="Sample 1",
            excerpt_start="1",
            excerpt_end="5",
        )
        service.create(
            manuscript_id=manuscript2,
            title="Sample 2",
            excerpt_start="1",
            excerpt_end="10",
        )

        samples1 = service.list_by_manuscript(manuscript1)
        samples2 = service.list_by_manuscript(manuscript2)

        assert len(samples1) == 1
        assert samples1[0].title == "Sample 1"
        assert len(samples2) == 1

    def test_update_sample(self, service: SampleService):
        manuscript_id = uuid4()
        created = service.create(
            manuscript_id=manuscript_id,
            title="Original",
            excerpt_start="1",
            excerpt_end="5",
        )

        updated = service.update(
            created.id,
            title="Updated",
            promo_footer="Buy now!",
        )

        assert updated.title == "Updated"
        assert updated.promo_footer == "Buy now!"
        # Unchanged fields stay the same
        assert updated.excerpt_start == "1"
