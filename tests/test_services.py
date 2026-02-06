"""
Tests for service layer using SQLAlchemy repositories.
"""

from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.domain import ManuscriptNotFound, ManuscriptState, SampleNotFound, SourceFormat
from app.repositories import (
    SQLAlchemyAuthorRepository,
    SQLAlchemyManuscriptRepository,
    SQLAlchemySampleRepository,
)
from app.services import AuthorService, ManuscriptService, SampleService


class TestAuthorService:
    @pytest.fixture
    def service(self, db_session: Session) -> AuthorService:
        repo = SQLAlchemyAuthorRepository(db_session)
        return AuthorService(repo)

    def test_create_author(self, service: AuthorService, db_session: Session):
        author = service.create(
            email="test@example.com",
            password_hash="hashed_password",
            display_name="Test User",
        )
        db_session.commit()

        assert author.email == "test@example.com"
        assert author.display_name == "Test User"
        assert author.id is not None

    def test_get_author(self, service: AuthorService, db_session: Session):
        created = service.create(
            email="get@example.com",
            password_hash="hash",
            display_name="Get Test",
        )
        db_session.commit()

        retrieved = service.get(created.id)

        assert retrieved.id == created.id
        assert retrieved.email == created.email

    def test_get_author_by_email(self, service: AuthorService, db_session: Session):
        created = service.create(
            email="byemail@example.com",
            password_hash="hash",
            display_name="Email Test",
        )
        db_session.commit()

        retrieved = service.get_by_email("byemail@example.com")

        assert retrieved is not None
        assert retrieved.id == created.id

    def test_get_author_by_email_not_found(self, service: AuthorService):
        result = service.get_by_email("nonexistent@example.com")
        assert result is None

    def test_update_author(self, service: AuthorService, db_session: Session):
        created = service.create(
            email="update@example.com",
            password_hash="hash",
            display_name="Original Name",
        )
        db_session.commit()

        updated = service.update(created.id, display_name="New Name")
        db_session.commit()

        assert updated.display_name == "New Name"
        assert updated.email == "update@example.com"


class TestManuscriptService:
    @pytest.fixture
    def service(self, db_session: Session) -> ManuscriptService:
        repo = SQLAlchemyManuscriptRepository(db_session)
        return ManuscriptService(repo)

    @pytest.fixture
    def author_id(self, db_session: Session):
        """Create an author for manuscript tests."""
        repo = SQLAlchemyAuthorRepository(db_session)
        author_service = AuthorService(repo)
        author = author_service.create(
            email="manuscript-test@example.com",
            password_hash="hash",
            display_name="Test Author",
        )
        db_session.commit()
        return author.id

    def test_create_manuscript(self, service: ManuscriptService, db_session: Session, author_id):
        manuscript = service.create(
            author_id=author_id,
            title="My Book",
            source_format=SourceFormat.EPUB,
            source_file_key="manuscripts/book.epub",
            description="A great book",
        )
        db_session.commit()

        assert manuscript.title == "My Book"
        assert manuscript.author_id == author_id
        assert manuscript.state == ManuscriptState.DRAFT

    def test_get_manuscript(self, service: ManuscriptService, db_session: Session, author_id):
        created = service.create(
            author_id=author_id,
            title="Get Test",
            source_format=SourceFormat.PDF,
            source_file_key="manuscripts/book.pdf",
        )
        db_session.commit()

        retrieved = service.get(created.id)

        assert retrieved.id == created.id
        assert retrieved.title == "Get Test"

    def test_get_manuscript_not_found(self, service: ManuscriptService):
        with pytest.raises(ManuscriptNotFound):
            service.get(uuid4())

    def test_list_by_author(self, service: ManuscriptService, db_session: Session):
        # Create two authors
        author_repo = SQLAlchemyAuthorRepository(db_session)
        author_service = AuthorService(author_repo)
        author1 = author_service.create(
            email="author1-list@example.com",
            password_hash="hash",
            display_name="Author 1",
        )
        author2 = author_service.create(
            email="author2-list@example.com",
            password_hash="hash",
            display_name="Author 2",
        )
        db_session.commit()

        service.create(
            author_id=author1.id,
            title="Author 1 Book",
            source_format=SourceFormat.EPUB,
            source_file_key="m/1.epub",
        )
        service.create(
            author_id=author2.id,
            title="Author 2 Book",
            source_format=SourceFormat.EPUB,
            source_file_key="m/2.epub",
        )
        db_session.commit()

        author1_manuscripts = service.list_by_author(author1.id)
        author2_manuscripts = service.list_by_author(author2.id)

        assert len(author1_manuscripts) == 1
        assert author1_manuscripts[0].title == "Author 1 Book"
        assert len(author2_manuscripts) == 1
        assert author2_manuscripts[0].title == "Author 2 Book"

    def test_update_metadata(self, service: ManuscriptService, db_session: Session, author_id):
        created = service.create(
            author_id=author_id,
            title="Original",
            source_format=SourceFormat.EPUB,
            source_file_key="m/book.epub",
        )
        db_session.commit()

        updated = service.update_metadata(
            created.id,
            title="Updated Title",
            description="New description",
        )
        db_session.commit()

        assert updated.title == "Updated Title"
        assert updated.description == "New description"

    def test_mark_ready(self, service: ManuscriptService, db_session: Session, author_id):
        created = service.create(
            author_id=author_id,
            title="Ready Book",
            source_format=SourceFormat.EPUB,
            source_file_key="m/book.epub",
        )
        db_session.commit()

        ready = service.mark_ready(created.id)
        db_session.commit()

        assert ready.state == ManuscriptState.READY

    def test_check_ownership(self, service: ManuscriptService, db_session: Session):
        # Create two authors
        author_repo = SQLAlchemyAuthorRepository(db_session)
        author_service = AuthorService(author_repo)
        owner = author_service.create(
            email="owner-check@example.com",
            password_hash="hash",
            display_name="Owner",
        )
        other = author_service.create(
            email="other-check@example.com",
            password_hash="hash",
            display_name="Other",
        )
        db_session.commit()

        created = service.create(
            author_id=owner.id,
            title="Owned Book",
            source_format=SourceFormat.EPUB,
            source_file_key="m/book.epub",
        )
        db_session.commit()

        assert service.check_ownership(created.id, owner.id) is True
        assert service.check_ownership(created.id, other.id) is False
        assert service.check_ownership(uuid4(), owner.id) is False

    def test_delete_manuscript(self, service: ManuscriptService, db_session: Session, author_id):
        created = service.create(
            author_id=author_id,
            title="Delete Me",
            source_format=SourceFormat.EPUB,
            source_file_key="m/book.epub",
        )
        db_session.commit()

        service.delete(created.id)
        db_session.commit()

        with pytest.raises(ManuscriptNotFound):
            service.get(created.id)


class TestSampleService:
    @pytest.fixture
    def service(self, db_session: Session) -> SampleService:
        repo = SQLAlchemySampleRepository(db_session)
        return SampleService(repo)

    @pytest.fixture
    def manuscript_id(self, db_session: Session):
        """Create an author and manuscript to attach samples to."""
        author_repo = SQLAlchemyAuthorRepository(db_session)
        author_service = AuthorService(author_repo)
        author = author_service.create(
            email="sample-test@example.com",
            password_hash="hash",
            display_name="Sample Test Author",
        )
        db_session.commit()

        repo = SQLAlchemyManuscriptRepository(db_session)
        ms_service = ManuscriptService(repo)
        manuscript = ms_service.create(
            author_id=author.id,
            title="Test Manuscript",
            source_format=SourceFormat.EPUB,
            source_file_key="m/test.epub",
        )
        db_session.commit()
        return manuscript.id

    def test_create_sample(self, service: SampleService, db_session: Session, manuscript_id):
        sample = service.create(
            manuscript_id=manuscript_id,
            title="Preview",
            excerpt_start="Chapter 1",
            excerpt_end="Chapter 3",
            promo_header="Free sample!",
        )
        db_session.commit()

        assert sample.title == "Preview"
        assert sample.manuscript_id == manuscript_id
        assert sample.excerpt_start == "Chapter 1"
        assert sample.promo_header == "Free sample!"

    def test_get_sample(self, service: SampleService, db_session: Session, manuscript_id):
        created = service.create(
            manuscript_id=manuscript_id,
            title="Get Test",
            excerpt_start="1",
            excerpt_end="5",
        )
        db_session.commit()

        retrieved = service.get(created.id)

        assert retrieved.id == created.id
        assert retrieved.title == "Get Test"

    def test_get_sample_not_found(self, service: SampleService):
        with pytest.raises(SampleNotFound):
            service.get(uuid4())

    def test_list_by_manuscript(self, service: SampleService, db_session: Session):
        # Create author first
        author_repo = SQLAlchemyAuthorRepository(db_session)
        author_service = AuthorService(author_repo)
        author = author_service.create(
            email="list-samples-test@example.com",
            password_hash="hash",
            display_name="List Samples Author",
        )
        db_session.commit()

        # Create two manuscripts
        repo = SQLAlchemyManuscriptRepository(db_session)
        ms = ManuscriptService(repo)
        m1 = ms.create(
            author_id=author.id,
            title="M1",
            source_format=SourceFormat.EPUB,
            source_file_key="m/1.epub",
        )
        m2 = ms.create(
            author_id=author.id,
            title="M2",
            source_format=SourceFormat.EPUB,
            source_file_key="m/2.epub",
        )
        db_session.commit()

        service.create(
            manuscript_id=m1.id,
            title="Sample 1",
            excerpt_start="1",
            excerpt_end="5",
        )
        service.create(
            manuscript_id=m2.id,
            title="Sample 2",
            excerpt_start="1",
            excerpt_end="10",
        )
        db_session.commit()

        samples1 = service.list_by_manuscript(m1.id)
        samples2 = service.list_by_manuscript(m2.id)

        assert len(samples1) == 1
        assert samples1[0].title == "Sample 1"
        assert len(samples2) == 1

    def test_update_sample(self, service: SampleService, db_session: Session, manuscript_id):
        created = service.create(
            manuscript_id=manuscript_id,
            title="Original",
            excerpt_start="1",
            excerpt_end="5",
        )
        db_session.commit()

        updated = service.update(
            created.id,
            title="Updated",
            promo_footer="Buy now!",
        )
        db_session.commit()

        assert updated.title == "Updated"
        assert updated.promo_footer == "Buy now!"
        # Unchanged fields stay the same
        assert updated.excerpt_start == "1"
