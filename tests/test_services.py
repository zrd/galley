"""
Tests for service layer using SQLAlchemy repositories.
"""

from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.domain import ManuscriptNotFound, ManuscriptState, OutputFormat, SampleNotFound, SourceFormat, TagNotFound
from app.repositories import (
    SQLAlchemyAuthorRepository,
    SQLAlchemyEbookRepository,
    SQLAlchemyManuscriptRepository,
    SQLAlchemySampleRepository,
    SQLAlchemyTagRepository,
)
from app.schemas.ebook import EbookUpdate
from app.services import AuthorService, EbookService, ManuscriptService, SampleService, TagService


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
        tag_repo = SQLAlchemyTagRepository(db_session)
        return ManuscriptService(repo, tag_repo=tag_repo)

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
            author_id=author_id,
            title="Updated Title",
            description="New description",
        )
        db_session.commit()

        assert updated.title == "Updated Title"
        assert updated.description == "New description"

    def test_create_with_tag_names(self, service: ManuscriptService, db_session: Session, author_id):
        manuscript = service.create(
            author_id=author_id,
            title="Tagged Book",
            source_format=SourceFormat.EPUB,
            source_file_key="m/tagged.epub",
            tag_names=["Hard Sci-Fi", "Adventure"],
        )
        db_session.commit()

        assert len(manuscript.tags) == 2
        slugs = {t.slug for t in manuscript.tags}
        assert slugs == {"hard-sci-fi", "adventure"}

    def test_update_metadata_with_tag_names(self, service: ManuscriptService, db_session: Session, author_id):
        created = service.create(
            author_id=author_id,
            title="Book",
            source_format=SourceFormat.EPUB,
            source_file_key="m/book.epub",
            tag_names=["Fantasy"],
        )
        db_session.commit()

        updated = service.update_metadata(
            created.id,
            author_id=author_id,
            tag_names=["Horror", "Thriller"],
        )
        db_session.commit()

        slugs = {t.slug for t in updated.tags}
        assert slugs == {"horror", "thriller"}
        assert "fantasy" not in slugs

    def test_update_metadata_without_tag_names_preserves_tags(
        self, service: ManuscriptService, db_session: Session, author_id
    ):
        created = service.create(
            author_id=author_id,
            title="Book",
            source_format=SourceFormat.EPUB,
            source_file_key="m/book.epub",
            tag_names=["Fantasy"],
        )
        db_session.commit()

        updated = service.update_metadata(
            created.id,
            author_id=author_id,
            title="Updated Title",
        )
        db_session.commit()

        assert len(updated.tags) == 1
        assert updated.tags[0].slug == "fantasy"

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


class TestEbookService:
    @pytest.fixture
    def service(self, db_session: Session) -> EbookService:
        repo = SQLAlchemyEbookRepository(db_session)
        return EbookService(repo)

    @pytest.fixture
    def manuscript_id(self, db_session: Session):
        """Create an author and manuscript to attach ebooks to."""
        author_repo = SQLAlchemyAuthorRepository(db_session)
        author = AuthorService(author_repo).create(
            email="ebook-service-test@example.com",
            password_hash="hash",
            display_name="Test Author",
        )
        db_session.commit()

        manuscript_repo = SQLAlchemyManuscriptRepository(db_session)
        manuscript = ManuscriptService(manuscript_repo).create(
            author_id=author.id,
            title="Test Book",
            source_format=SourceFormat.EPUB,
            source_file_key="m/test.epub",
        )
        db_session.commit()
        return manuscript.id

    def test_create_ebook_persists_download_filename(
        self, service: EbookService, db_session: Session, manuscript_id
    ):
        ebook = service.create(
            manuscript_id=manuscript_id,
            output_format=OutputFormat.EPUB,
            file_key="ebooks/test.epub",
            file_size_bytes=2048,
            download_filename="Test Author - Test Book.epub",
        )
        db_session.commit()

        retrieved = service.get(ebook.id)
        assert retrieved.download_filename == "Test Author - Test Book.epub"
        assert retrieved.manuscript_id == manuscript_id

    def test_update_price(
        self, service: EbookService, db_session: Session, manuscript_id
    ):
        ebook = service.create(
            manuscript_id=manuscript_id,
            output_format=OutputFormat.EPUB,
            file_key="ebooks/test-price.epub",
            file_size_bytes=2048,
            download_filename="Test Author - Test Book.epub",
        )
        db_session.commit()

        service.update_price(
            ebook=ebook,
            update_in=EbookUpdate(list_price_cents=999, sale_price_cents=799),
        )
        db_session.commit()

        retrieved = service.get(ebook.id)
        assert retrieved.list_price_cents == 999
        assert retrieved.sale_price_cents == 799

    def test_update_price_partial(
        self, service: EbookService, db_session: Session, manuscript_id
    ):
        ebook = service.create(
            manuscript_id=manuscript_id,
            output_format=OutputFormat.EPUB,
            file_key="ebooks/test-price-partial.epub",
            file_size_bytes=2048,
            download_filename="Test Author - Test Book.epub",
        )
        service.update_price(
            ebook=ebook,
            update_in=EbookUpdate(list_price_cents=999),
        )
        db_session.commit()

        ebook = service.get(ebook.id)
        # Patch only sale price — list price must be unchanged
        service.update_price(
            ebook=ebook,
            update_in=EbookUpdate(sale_price_cents=799),
        )
        db_session.commit()

        retrieved = service.get(ebook.id)
        assert retrieved.list_price_cents == 999
        assert retrieved.sale_price_cents == 799


class TestTagRepository:
    @pytest.fixture
    def repo(self, db_session: Session) -> SQLAlchemyTagRepository:
        return SQLAlchemyTagRepository(db_session)

    @pytest.fixture
    def author_id(self, db_session: Session):
        author = AuthorService(SQLAlchemyAuthorRepository(db_session)).create(
            email="tag-repo-test@example.com",
            password_hash="hash",
            display_name="Tag Test Author",
        )
        db_session.commit()
        return author.id

    @pytest.fixture
    def other_author_id(self, db_session: Session):
        author = AuthorService(SQLAlchemyAuthorRepository(db_session)).create(
            email="tag-repo-other@example.com",
            password_hash="hash",
            display_name="Other Author",
        )
        db_session.commit()
        return author.id

    @pytest.fixture
    def manuscript_id(self, db_session: Session, author_id):
        manuscript = ManuscriptService(SQLAlchemyManuscriptRepository(db_session)).create(
            author_id=author_id,
            title="Test Book",
            source_format=SourceFormat.EPUB,
            source_file_key="m/test.epub",
        )
        db_session.commit()
        return manuscript.id

    def test_add_persists_tag(self, repo: SQLAlchemyTagRepository, db_session: Session, author_id):
        from app.domain import Tag
        tag = repo.add(Tag(name="Hard Sci-Fi", slug="hard-sci-fi", owner_id=author_id))
        db_session.commit()

        retrieved = repo.get(tag.id)
        assert retrieved is not None
        assert retrieved.name == "Hard Sci-Fi"
        assert retrieved.slug == "hard-sci-fi"
        assert retrieved.owner_id == author_id

    def test_update_persists_changes(self, repo: SQLAlchemyTagRepository, db_session: Session, author_id):
        from app.domain import Tag
        tag = repo.add(Tag(name="Hard Sci-Fi", slug="hard-sci-fi", owner_id=author_id))
        db_session.commit()

        tag.name = "Hard Science Fiction"
        tag.slug = "hard-science-fiction"
        repo.update(tag)
        db_session.commit()

        retrieved = repo.get(tag.id)
        assert retrieved.name == "Hard Science Fiction"
        assert retrieved.slug == "hard-science-fiction"

    def test_get_returns_none_for_missing(self, repo: SQLAlchemyTagRepository):
        assert repo.get(uuid4()) is None

    def test_get_by_slug_returns_tag(self, repo: SQLAlchemyTagRepository, db_session: Session, author_id):
        from app.domain import Tag
        repo.add(Tag(name="Cozy Mystery", slug="cozy-mystery", owner_id=author_id))
        db_session.commit()

        found = repo.get_by_slug("cozy-mystery", author_id)
        assert found is not None
        assert found.name == "Cozy Mystery"

    def test_get_by_slug_respects_owner_scope(
        self, repo: SQLAlchemyTagRepository, db_session: Session, author_id, other_author_id
    ):
        from app.domain import Tag
        # Both authors have the same slug
        repo.add(Tag(name="Fantasy", slug="fantasy", owner_id=author_id))
        repo.add(Tag(name="Fantasy", slug="fantasy", owner_id=other_author_id))
        db_session.commit()

        found = repo.get_by_slug("fantasy", author_id)
        assert found is not None
        assert found.owner_id == author_id

        found_other = repo.get_by_slug("fantasy", other_author_id)
        assert found_other is not None
        assert found_other.owner_id == other_author_id
        assert found.id != found_other.id

    def test_get_by_slug_returns_none_for_wrong_owner(
        self, repo: SQLAlchemyTagRepository, db_session: Session, author_id, other_author_id
    ):
        from app.domain import Tag
        repo.add(Tag(name="Thriller", slug="thriller", owner_id=author_id))
        db_session.commit()

        assert repo.get_by_slug("thriller", other_author_id) is None

    def test_get_or_create_creates_new_tag(
        self, repo: SQLAlchemyTagRepository, db_session: Session, author_id
    ):
        tag = repo.get_or_create("New Wave", author_id)
        db_session.commit()

        assert tag.name == "New Wave"
        assert tag.slug == "new-wave"
        assert tag.owner_id == author_id

    def test_get_or_create_returns_existing(
        self, repo: SQLAlchemyTagRepository, db_session: Session, author_id
    ):
        from app.domain import Tag
        existing = repo.add(Tag(name="Romance", slug="romance", owner_id=author_id))
        db_session.commit()

        tag = repo.get_or_create("Romance", author_id)
        assert tag.id == existing.id

    def test_get_or_create_resurrects_soft_deleted(
        self, repo: SQLAlchemyTagRepository, db_session: Session, author_id
    ):
        from app.domain import Tag
        tag = repo.add(Tag(name="Horror", slug="horror", owner_id=author_id))
        db_session.commit()

        tag.soft_delete()
        repo.update(tag)
        db_session.commit()

        assert repo.get(tag.id).is_deleted

        resurrected = repo.get_or_create("Horror", author_id)
        db_session.commit()

        assert resurrected.id == tag.id
        assert not resurrected.is_deleted

    def test_set_tags_assigns_tags_to_manuscript(
        self, repo: SQLAlchemyTagRepository, db_session: Session, author_id, manuscript_id
    ):
        from app.domain import Tag
        ms_repo = SQLAlchemyManuscriptRepository(db_session)
        t1 = repo.add(Tag(name="Sci-Fi", slug="sci-fi", owner_id=author_id))
        t2 = repo.add(Tag(name="Adventure", slug="adventure", owner_id=author_id))
        db_session.commit()

        ms_repo.set_tags(manuscript_id, [t1.id, t2.id])
        db_session.commit()

        manuscript = ms_repo.get(manuscript_id)
        tag_ids = {t.id for t in manuscript.tags}
        assert t1.id in tag_ids
        assert t2.id in tag_ids

    def test_set_tags_replaces_existing(
        self, repo: SQLAlchemyTagRepository, db_session: Session, author_id, manuscript_id
    ):
        from app.domain import Tag
        ms_repo = SQLAlchemyManuscriptRepository(db_session)
        t1 = repo.add(Tag(name="Sci-Fi", slug="sci-fi-replace", owner_id=author_id))
        t2 = repo.add(Tag(name="Adventure", slug="adventure-replace", owner_id=author_id))
        db_session.commit()

        ms_repo.set_tags(manuscript_id, [t1.id])
        db_session.commit()

        ms_repo.set_tags(manuscript_id, [t2.id])
        db_session.commit()

        manuscript = ms_repo.get(manuscript_id)
        tag_ids = {t.id for t in manuscript.tags}
        assert t2.id in tag_ids
        assert t1.id not in tag_ids

    def test_set_tags_with_empty_list_clears_tags(
        self, repo: SQLAlchemyTagRepository, db_session: Session, author_id, manuscript_id
    ):
        from app.domain import Tag
        ms_repo = SQLAlchemyManuscriptRepository(db_session)
        t1 = repo.add(Tag(name="Mystery", slug="mystery-clear", owner_id=author_id))
        db_session.commit()

        ms_repo.set_tags(manuscript_id, [t1.id])
        db_session.commit()

        ms_repo.set_tags(manuscript_id, [])
        db_session.commit()

        manuscript = ms_repo.get(manuscript_id)
        assert manuscript.tags == []

    def test_list_popular_orders_by_usage(
        self, repo: SQLAlchemyTagRepository, db_session: Session, author_id
    ):
        from app.domain import Tag
        ms_repo = SQLAlchemyManuscriptRepository(db_session)

        t_popular = repo.add(Tag(name="Popular", slug="popular", owner_id=author_id))
        t_rare = repo.add(Tag(name="Rare", slug="rare", owner_id=author_id))
        db_session.commit()

        for i, email in enumerate(["pop1@example.com", "pop2@example.com"]):
            author = AuthorService(SQLAlchemyAuthorRepository(db_session)).create(
                email=email, password_hash="hash", display_name=f"Author {i}"
            )
            db_session.commit()
            m = ManuscriptService(SQLAlchemyManuscriptRepository(db_session)).create(
                author_id=author.id,
                title=f"Book {i}",
                source_format=SourceFormat.EPUB,
                source_file_key=f"m/book{i}.epub",
            )
            db_session.commit()
            ms_repo.set_tags(m.id, [t_popular.id])
            db_session.commit()

        m_rare = ManuscriptService(SQLAlchemyManuscriptRepository(db_session)).create(
            author_id=author_id,
            title="Rare Book",
            source_format=SourceFormat.EPUB,
            source_file_key="m/rare.epub",
        )
        db_session.commit()
        ms_repo.set_tags(m_rare.id, [t_rare.id])
        db_session.commit()

        results = repo.list_popular(top_n=2)
        assert results[0].id == t_popular.id
        assert results[1].id == t_rare.id

    def test_list_popular_respects_top_n(
        self, repo: SQLAlchemyTagRepository, db_session: Session, author_id
    ):
        from app.domain import Tag
        for i in range(5):
            repo.add(Tag(name=f"Tag {i}", slug=f"tag-{i}", owner_id=author_id))
        db_session.commit()

        results = repo.list_popular(top_n=3)
        assert len(results) == 3


class TestTagService:
    @pytest.fixture
    def service(self, db_session: Session) -> TagService:
        return TagService(SQLAlchemyTagRepository(db_session))

    @pytest.fixture
    def author_id(self, db_session: Session):
        repo = SQLAlchemyAuthorRepository(db_session)
        author = AuthorService(repo).create(
            email="tag-service-test@example.com",
            password_hash="hash",
            display_name="Tag Test Author",
        )
        db_session.commit()
        return author.id

    @pytest.fixture
    def other_author_id(self, db_session: Session):
        repo = SQLAlchemyAuthorRepository(db_session)
        author = AuthorService(repo).create(
            email="other-tag-service-test@example.com",
            password_hash="hash",
            display_name="Other Tag Author",
        )
        db_session.commit()
        return author.id

    def test_create_returns_tag(self, service: TagService, db_session: Session, author_id):
        tag = service.create(name="Hard Sci-Fi", owner_id=author_id)
        db_session.commit()

        assert tag.name == "Hard Sci-Fi"
        assert tag.slug == "hard-sci-fi"
        assert tag.owner_id == author_id

    def test_create_is_idempotent(self, service: TagService, db_session: Session, author_id):
        t1 = service.create(name="Hard Sci-Fi", owner_id=author_id)
        db_session.commit()
        t2 = service.create(name="Hard Sci-Fi", owner_id=author_id)
        db_session.commit()

        assert t1.id == t2.id

    def test_get_returns_tag(self, service: TagService, db_session: Session, author_id):
        service.create(name="Adventure", owner_id=author_id)
        db_session.commit()

        tag = service.get(name="Adventure", owner_id=author_id)

        assert tag.name == "Adventure"
        assert tag.owner_id == author_id

    def test_get_raises_tag_not_found(self, service: TagService, author_id):
        with pytest.raises(TagNotFound):
            service.get(name="Nonexistent", owner_id=author_id)

    def test_list_all_returns_owner_tags(self, service: TagService, db_session: Session, author_id):
        service.create(name="Fantasy", owner_id=author_id)
        service.create(name="Horror", owner_id=author_id)
        db_session.commit()

        tags = service.list_all(owner_id=author_id)

        assert len(tags) == 2
        assert {t.name for t in tags} == {"Fantasy", "Horror"}

    def test_list_all_excludes_other_owners(
        self, service: TagService, db_session: Session, author_id, other_author_id
    ):
        service.create(name="Fantasy", owner_id=author_id)
        service.create(name="Horror", owner_id=other_author_id)
        db_session.commit()

        tags = service.list_all(owner_id=author_id)

        assert len(tags) == 1
        assert tags[0].name == "Fantasy"
