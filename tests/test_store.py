"""
Repository and service layer tests for the store.

Covers sort ordering and genre tree assembly — logic that the API tests don't
exercise at enough granularity.
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.db.models import (
    AuthorModel,
    EbookModel,
    GenreModel,
    ManuscriptGenreModel,
    ManuscriptModel,
    ManuscriptTagModel,
    TagModel,
)
from app.domain.enums import ManuscriptState, OutputFormat, SourceFormat, Visibility
from app.repositories import StoreRepository
from app.services import StoreService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _author(db: Session, display_name: str = "Author", is_public: bool = True) -> AuthorModel:
    a = AuthorModel(
        email=f"{uuid4()}@example.com",
        password_hash="x",
        display_name=display_name,
        is_public=is_public,
    )
    db.add(a)
    db.flush()
    return a


def _manuscript(db: Session, author_id, title: str = "Book") -> ManuscriptModel:
    m = ManuscriptModel(
        author_id=author_id,
        title=title,
        source_format=SourceFormat.EPUB,
        source_file_key="test.epub",
        state=ManuscriptState.READY,
    )
    db.add(m)
    db.flush()
    return m


def _ebook(
    db: Session,
    manuscript_id,
    visibility: Visibility = Visibility.PUBLISHED,
    published_at: datetime | None = None,
    list_price_cents: int | None = None,
    sale_price_cents: int | None = None,
) -> EbookModel:
    if visibility == Visibility.PUBLISHED and published_at is None:
        published_at = datetime.now(timezone.utc)
    e = EbookModel(
        manuscript_id=manuscript_id,
        output_format=OutputFormat.EPUB,
        file_key="test.epub",
        file_size_bytes=1000,
        download_filename="book.epub",
        visibility=visibility,
        published_at=published_at,
        list_price_cents=list_price_cents,
        sale_price_cents=sale_price_cents,
        price_currency="USD",
    )
    db.add(e)
    db.flush()
    return e


def _genre(db: Session, name: str, parent_id: int | None = None) -> GenreModel:
    g = GenreModel(name=name, slug=name.lower().replace(" ", "-"), parent_id=parent_id)
    db.add(g)
    db.flush()
    return g


def _tag(db: Session, owner_id, name: str) -> TagModel:
    t = TagModel(name=name, slug=name.lower().replace(" ", "-"), owner_id=owner_id)
    db.add(t)
    db.flush()
    return t


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

NOW = datetime.now(timezone.utc)
EARLIER = NOW - timedelta(days=10)


@pytest.fixture
def repo(db_session: Session) -> StoreRepository:
    return StoreRepository(db_session)


@pytest.fixture
def service(db_session: Session) -> StoreService:
    return StoreService(StoreRepository(db_session))


@pytest.fixture
def two_books(db_session: Session) -> tuple:
    """Two published manuscripts: m1 older and more expensive, m2 newer and cheaper."""
    author = _author(db_session)
    m1 = _manuscript(db_session, author.id, "Aardvark")
    _ebook(db_session, m1.id, published_at=EARLIER, list_price_cents=1000)
    m2 = _manuscript(db_session, author.id, "Zebra")
    _ebook(db_session, m2.id, published_at=NOW, list_price_cents=500)
    db_session.commit()
    return m1, m2


# ---------------------------------------------------------------------------
# Browse listings — sort order
# ---------------------------------------------------------------------------

class TestBrowseListingsSorting:
    def test_newest(self, repo: StoreRepository, two_books):
        results, _ = repo.browse_listings(offset=0, limit=10, sorting_method="newest")
        assert [r.title for r in results] == ["Zebra", "Aardvark"]

    def test_oldest(self, repo: StoreRepository, two_books):
        results, _ = repo.browse_listings(offset=0, limit=10, sorting_method="oldest")
        assert [r.title for r in results] == ["Aardvark", "Zebra"]

    def test_a_to_z(self, repo: StoreRepository, two_books):
        results, _ = repo.browse_listings(offset=0, limit=10, sorting_method="a_to_z")
        assert [r.title for r in results] == ["Aardvark", "Zebra"]

    def test_z_to_a(self, repo: StoreRepository, two_books):
        results, _ = repo.browse_listings(offset=0, limit=10, sorting_method="z_to_a")
        assert [r.title for r in results] == ["Zebra", "Aardvark"]

    def test_least_expensive(self, repo: StoreRepository, two_books):
        results, _ = repo.browse_listings(offset=0, limit=10, sorting_method="least_expensive")
        assert [r.title for r in results] == ["Zebra", "Aardvark"]

    def test_most_expensive(self, repo: StoreRepository, two_books):
        results, _ = repo.browse_listings(offset=0, limit=10, sorting_method="most_expensive")
        assert [r.title for r in results] == ["Aardvark", "Zebra"]

    def test_unknown_sort_falls_back_to_newest(self, repo: StoreRepository, two_books):
        results, _ = repo.browse_listings(offset=0, limit=10, sorting_method="bogus")
        assert [r.title for r in results] == ["Zebra", "Aardvark"]

    def test_sale_price_used_over_list_price(self, repo: StoreRepository, db_session: Session):
        """Effective price uses sale_price_cents when set."""
        author = _author(db_session)
        m1 = _manuscript(db_session, author.id, "Expensive")
        _ebook(db_session, m1.id, list_price_cents=2000, sale_price_cents=100)
        m2 = _manuscript(db_session, author.id, "Cheap")
        _ebook(db_session, m2.id, list_price_cents=500)
        db_session.commit()

        results, _ = repo.browse_listings(offset=0, limit=10, sorting_method="most_expensive")
        assert results[0].title == "Cheap"  # 500 > 100 (sale price wins)


# ---------------------------------------------------------------------------
# Genre tree assembly (service layer)
# ---------------------------------------------------------------------------

class TestGenreTreeAssembly:
    def test_children_nested_under_parent(self, service: StoreService, db_session: Session):
        parent = _genre(db_session, "Fiction")
        _genre(db_session, "Science Fiction", parent_id=parent.id)
        db_session.commit()

        tree = service.list_genres_with_counts()

        fiction = next(g for g in tree if g.name == "Fiction")
        assert len(fiction.children) == 1
        assert fiction.children[0].name == "Science Fiction"

    def test_child_genres_not_at_root(self, service: StoreService, db_session: Session):
        parent = _genre(db_session, "Nonfiction")
        _genre(db_session, "History", parent_id=parent.id)
        db_session.commit()

        tree = service.list_genres_with_counts()

        top_level_names = [g.name for g in tree]
        assert "Nonfiction" in top_level_names
        assert "History" not in top_level_names

    def test_published_count_reflects_published_ebooks_only(
        self, service: StoreService, db_session: Session
    ):
        author = _author(db_session)
        genre = _genre(db_session, "Romance")

        published = _manuscript(db_session, author.id)
        _ebook(db_session, published.id)
        db_session.add(ManuscriptGenreModel(manuscript_id=published.id, genre_id=genre.id))

        private = _manuscript(db_session, author.id)
        _ebook(db_session, private.id, visibility=Visibility.PRIVATE)
        db_session.add(ManuscriptGenreModel(manuscript_id=private.id, genre_id=genre.id))

        db_session.commit()

        tree = service.list_genres_with_counts()
        romance = next(g for g in tree if g.name == "Romance")
        assert romance.published_count == 1

    def test_manuscript_with_multiple_editions_counts_once(
        self, service: StoreService, db_session: Session
    ):
        author = _author(db_session)
        genre = _genre(db_session, "Thriller")

        m = _manuscript(db_session, author.id)
        _ebook(db_session, m.id)
        _ebook(db_session, m.id)  # second edition (epub + mobi)
        db_session.add(ManuscriptGenreModel(manuscript_id=m.id, genre_id=genre.id))
        db_session.commit()

        tree = service.list_genres_with_counts()
        thriller = next(g for g in tree if g.name == "Thriller")
        assert thriller.published_count == 1


# ---------------------------------------------------------------------------
# browse_listings — filters
# ---------------------------------------------------------------------------

class TestBrowseListingsFilters:
    def test_filter_by_genre_slug(self, repo: StoreRepository, db_session: Session):
        author = _author(db_session)
        genre = _genre(db_session, "Fiction")
        m1 = _manuscript(db_session, author.id, "Tagged")
        _ebook(db_session, m1.id)
        db_session.add(ManuscriptGenreModel(manuscript_id=m1.id, genre_id=genre.id))
        m2 = _manuscript(db_session, author.id, "Untagged")
        _ebook(db_session, m2.id)
        db_session.commit()

        results, total = repo.browse_listings(offset=0, limit=10, genre_slugs=["fiction"])
        assert total == 1
        assert results[0].title == "Tagged"

    def test_filter_by_tag_slug(self, repo: StoreRepository, db_session: Session):
        author = _author(db_session)
        tag = _tag(db_session, author.id, "Fantasy")
        m1 = _manuscript(db_session, author.id, "Tagged")
        _ebook(db_session, m1.id)
        db_session.add(ManuscriptTagModel(manuscript_id=m1.id, tag_id=tag.id))
        m2 = _manuscript(db_session, author.id, "Untagged")
        _ebook(db_session, m2.id)
        db_session.commit()

        results, total = repo.browse_listings(offset=0, limit=10, tag_slugs=["fantasy"])
        assert total == 1
        assert results[0].title == "Tagged"

    def test_filter_by_author_id(self, repo: StoreRepository, db_session: Session):
        a1 = _author(db_session, "Alice")
        a2 = _author(db_session, "Bob")
        m1 = _manuscript(db_session, a1.id, "Alice Book")
        _ebook(db_session, m1.id)
        m2 = _manuscript(db_session, a2.id, "Bob Book")
        _ebook(db_session, m2.id)
        db_session.commit()

        results, total = repo.browse_listings(offset=0, limit=10, author_ids=[a1.id])
        assert total == 1
        assert results[0].title == "Alice Book"

    def test_filter_by_min_price(self, repo: StoreRepository, db_session: Session):
        author = _author(db_session)
        m_cheap = _manuscript(db_session, author.id, "Cheap")
        _ebook(db_session, m_cheap.id, list_price_cents=100)
        m_pricey = _manuscript(db_session, author.id, "Pricey")
        _ebook(db_session, m_pricey.id, list_price_cents=1000)
        db_session.commit()

        results, total = repo.browse_listings(offset=0, limit=10, min_price=500)
        assert total == 1
        assert results[0].title == "Pricey"

    def test_filter_by_max_price(self, repo: StoreRepository, db_session: Session):
        author = _author(db_session)
        m_cheap = _manuscript(db_session, author.id, "Cheap")
        _ebook(db_session, m_cheap.id, list_price_cents=100)
        m_pricey = _manuscript(db_session, author.id, "Pricey")
        _ebook(db_session, m_pricey.id, list_price_cents=1000)
        db_session.commit()

        results, total = repo.browse_listings(offset=0, limit=10, max_price=500)
        assert total == 1
        assert results[0].title == "Cheap"

    def test_price_filter_uses_sale_over_list(self, repo: StoreRepository, db_session: Session):
        """min_price filter uses effective price (sale_price beats list_price)."""
        author = _author(db_session)
        m = _manuscript(db_session, author.id, "On Sale")
        _ebook(db_session, m.id, list_price_cents=2000, sale_price_cents=100)
        db_session.commit()

        # list price would match, but sale price (effective) does not
        results, _ = repo.browse_listings(offset=0, limit=10, min_price=1000)
        assert len(results) == 0

    def test_search_by_title(self, repo: StoreRepository, db_session: Session):
        author = _author(db_session)
        m1 = _manuscript(db_session, author.id, "Space Opera")
        _ebook(db_session, m1.id)
        m2 = _manuscript(db_session, author.id, "Fantasy Quest")
        _ebook(db_session, m2.id)
        db_session.commit()

        results, total = repo.browse_listings(offset=0, limit=10, search_term="space")
        assert total == 1
        assert results[0].title == "Space Opera"

    def test_search_by_author_name(self, repo: StoreRepository, db_session: Session):
        a1 = _author(db_session, "Alice Wordsworth")
        a2 = _author(db_session, "Bob Jones")
        m1 = _manuscript(db_session, a1.id, "Book One")
        _ebook(db_session, m1.id)
        m2 = _manuscript(db_session, a2.id, "Book Two")
        _ebook(db_session, m2.id)
        db_session.commit()

        results, total = repo.browse_listings(offset=0, limit=10, search_term="wordsworth")
        assert total == 1
        assert results[0].title == "Book One"

    def test_excludes_soft_deleted_manuscripts(self, repo: StoreRepository, db_session: Session):
        author = _author(db_session)
        m = _manuscript(db_session, author.id)
        _ebook(db_session, m.id)
        m.deleted_at = datetime.now(timezone.utc)
        db_session.commit()

        _, total = repo.browse_listings(offset=0, limit=10)
        assert total == 0

    def test_excludes_manuscripts_with_no_published_ebook(self, repo: StoreRepository, db_session: Session):
        author = _author(db_session)
        m = _manuscript(db_session, author.id)
        _ebook(db_session, m.id, visibility=Visibility.PRIVATE)
        db_session.commit()

        _, total = repo.browse_listings(offset=0, limit=10)
        assert total == 0

    def test_pagination_returns_correct_slice(self, repo: StoreRepository, db_session: Session):
        author = _author(db_session)
        for i in range(5):
            m = _manuscript(db_session, author.id, f"Book {i}")
            _ebook(db_session, m.id)
        db_session.commit()

        results, total = repo.browse_listings(offset=0, limit=3)
        assert total == 5
        assert len(results) == 3

        results2, total2 = repo.browse_listings(offset=3, limit=3)
        assert total2 == 5
        assert len(results2) == 2

    def test_total_count_independent_of_limit(self, repo: StoreRepository, db_session: Session):
        author = _author(db_session)
        for i in range(4):
            m = _manuscript(db_session, author.id, f"Book {i}")
            _ebook(db_session, m.id)
        db_session.commit()

        _, total = repo.browse_listings(offset=0, limit=1)
        assert total == 4


# ---------------------------------------------------------------------------
# get_listing
# ---------------------------------------------------------------------------

class TestGetListing:
    def test_returns_manuscript_with_published_ebook(self, repo: StoreRepository, db_session: Session):
        author = _author(db_session)
        m = _manuscript(db_session, author.id, "Published")
        _ebook(db_session, m.id)
        db_session.commit()

        result = repo.get_listing(m.id)
        assert result is not None
        assert result.id == m.id

    def test_returns_none_when_no_published_ebook(self, repo: StoreRepository, db_session: Session):
        author = _author(db_session)
        m = _manuscript(db_session, author.id)
        _ebook(db_session, m.id, visibility=Visibility.PRIVATE)
        db_session.commit()

        assert repo.get_listing(m.id) is None

    def test_returns_none_for_unlisted_only(self, repo: StoreRepository, db_session: Session):
        """Unlisted alone does not qualify a manuscript as a store listing."""
        author = _author(db_session)
        m = _manuscript(db_session, author.id)
        _ebook(db_session, m.id, visibility=Visibility.UNLISTED)
        db_session.commit()

        assert repo.get_listing(m.id) is None

    def test_returns_none_for_soft_deleted(self, repo: StoreRepository, db_session: Session):
        author = _author(db_session)
        m = _manuscript(db_session, author.id)
        _ebook(db_session, m.id)
        m.deleted_at = datetime.now(timezone.utc)
        db_session.commit()

        assert repo.get_listing(m.id) is None

    def test_editions_excludes_private_siblings(self, repo: StoreRepository, db_session: Session):
        """Private ebook on a published manuscript must not appear in the editions list."""
        author = _author(db_session)
        m = _manuscript(db_session, author.id)
        _ebook(db_session, m.id, visibility=Visibility.PUBLISHED)
        _ebook(db_session, m.id, visibility=Visibility.PRIVATE)
        db_session.commit()

        result = repo.get_listing(m.id)
        assert result is not None
        assert len(result.ebooks) == 1
        assert result.ebooks[0].visibility == Visibility.PUBLISHED


# ---------------------------------------------------------------------------
# get_edition
# ---------------------------------------------------------------------------

class TestGetEdition:
    def test_returns_published_edition(self, repo: StoreRepository, db_session: Session):
        author = _author(db_session)
        m = _manuscript(db_session, author.id)
        e = _ebook(db_session, m.id, visibility=Visibility.PUBLISHED)
        db_session.commit()

        result = repo.get_edition(e.id)
        assert result is not None
        assert result.id == e.id

    def test_returns_unlisted_edition(self, repo: StoreRepository, db_session: Session):
        author = _author(db_session)
        m = _manuscript(db_session, author.id)
        e = _ebook(db_session, m.id, visibility=Visibility.UNLISTED)
        db_session.commit()

        assert repo.get_edition(e.id) is not None

    def test_returns_none_for_private_edition(self, repo: StoreRepository, db_session: Session):
        author = _author(db_session)
        m = _manuscript(db_session, author.id)
        e = _ebook(db_session, m.id, visibility=Visibility.PRIVATE)
        db_session.commit()

        assert repo.get_edition(e.id) is None

    def test_returns_none_for_deleted_edition(self, repo: StoreRepository, db_session: Session):
        author = _author(db_session)
        m = _manuscript(db_session, author.id)
        e = _ebook(db_session, m.id, visibility=Visibility.PUBLISHED)
        e.deleted_at = datetime.now(timezone.utc)
        db_session.commit()

        assert repo.get_edition(e.id) is None

    def test_manuscript_ebooks_excludes_private_siblings(self, repo: StoreRepository, db_session: Session):
        """manuscript.ebooks on the returned edition should only be PUBLISHED."""
        author = _author(db_session)
        m = _manuscript(db_session, author.id)
        e_pub = _ebook(db_session, m.id, visibility=Visibility.PUBLISHED)
        _ebook(db_session, m.id, visibility=Visibility.PRIVATE)
        db_session.commit()

        result = repo.get_edition(e_pub.id)
        assert result is not None
        assert all(e.visibility == Visibility.PUBLISHED for e in result.manuscript.ebooks)


# ---------------------------------------------------------------------------
# get_author_profile
# ---------------------------------------------------------------------------

class TestGetAuthorProfile:
    def test_returns_public_author(self, repo: StoreRepository, db_session: Session):
        author = _author(db_session, is_public=True)
        db_session.commit()

        result = repo.get_author_profile(author.id)
        assert result is not None
        assert result.id == author.id

    def test_returns_none_for_private_author(self, repo: StoreRepository, db_session: Session):
        author = _author(db_session, is_public=False)
        db_session.commit()

        assert repo.get_author_profile(author.id) is None

    def test_returns_none_for_deleted_author(self, repo: StoreRepository, db_session: Session):
        author = _author(db_session, is_public=True)
        author.deleted_at = datetime.now(timezone.utc)
        db_session.commit()

        assert repo.get_author_profile(author.id) is None

    def test_manuscript_ebooks_excludes_non_published(self, repo: StoreRepository, db_session: Session):
        """Only PUBLISHED ebooks should appear within each manuscript on the profile."""
        author = _author(db_session, is_public=True)
        m = _manuscript(db_session, author.id)
        _ebook(db_session, m.id, visibility=Visibility.PUBLISHED)
        _ebook(db_session, m.id, visibility=Visibility.PRIVATE)
        db_session.commit()

        result = repo.get_author_profile(author.id)
        assert len(result.manuscripts) == 1
        assert all(e.visibility == Visibility.PUBLISHED for e in result.manuscripts[0].ebooks)

    def test_includes_manuscript_with_no_published_ebook(self, repo: StoreRepository, db_session: Session):
        """Author profile shows all non-deleted manuscripts regardless of ebook state."""
        author = _author(db_session, is_public=True)
        m = _manuscript(db_session, author.id)
        _ebook(db_session, m.id, visibility=Visibility.PRIVATE)
        db_session.commit()

        result = repo.get_author_profile(author.id)
        assert len(result.manuscripts) == 1
        assert len(result.manuscripts[0].ebooks) == 0

    def test_excludes_deleted_manuscripts(self, repo: StoreRepository, db_session: Session):
        author = _author(db_session, is_public=True)
        m = _manuscript(db_session, author.id)
        m.deleted_at = datetime.now(timezone.utc)
        db_session.commit()

        result = repo.get_author_profile(author.id)
        assert result is not None
        assert len(result.manuscripts) == 0


# ---------------------------------------------------------------------------
# list_author_profiles
# ---------------------------------------------------------------------------

class TestListAuthorProfiles:
    def test_returns_public_authors_only(self, repo: StoreRepository, db_session: Session):
        _author(db_session, "Public", is_public=True)
        _author(db_session, "Private", is_public=False)
        db_session.commit()

        results, total = repo.list_author_profiles(offset=0, limit=10)
        assert total == 1
        assert results[0].display_name == "Public"

    def test_excludes_deleted_authors(self, repo: StoreRepository, db_session: Session):
        a = _author(db_session, is_public=True)
        a.deleted_at = datetime.now(timezone.utc)
        db_session.commit()

        _, total = repo.list_author_profiles(offset=0, limit=10)
        assert total == 0

    def test_pagination(self, repo: StoreRepository, db_session: Session):
        for i in range(4):
            _author(db_session, f"Author {i}", is_public=True)
        db_session.commit()

        results, total = repo.list_author_profiles(offset=0, limit=2)
        assert total == 4
        assert len(results) == 2

        results2, _ = repo.list_author_profiles(offset=2, limit=2)
        assert len(results2) == 2


# ---------------------------------------------------------------------------
# Eager loading — expunge_all() simulates session close
# ---------------------------------------------------------------------------

class TestEagerLoading:
    """
    Each test calls expunge_all() after the repository method returns, then
    accesses every relationship that the Pydantic schemas will touch during
    serialization.  A DetachedInstanceError here means a missing eager load.
    """

    def test_browse_listings_loads_all_relationships(
        self, repo: StoreRepository, db_session: Session
    ):
        author = _author(db_session)
        genre = _genre(db_session, "Sci-Fi")
        tag = _tag(db_session, author.id, "space")
        m = _manuscript(db_session, author.id, "Test Book")
        _ebook(db_session, m.id)
        db_session.add(ManuscriptGenreModel(manuscript_id=m.id, genre_id=genre.id))
        db_session.add(ManuscriptTagModel(manuscript_id=m.id, tag_id=tag.id))
        db_session.commit()

        results, _ = repo.browse_listings(offset=0, limit=10)
        db_session.expunge_all()

        r = results[0]
        _ = r.author.display_name          # joinedload
        _ = [g.name for g in r.genres]    # selectinload
        _ = [t.name for t in r.tags]      # selectinload
        _ = [e.id for e in r.ebooks]      # selectinload (filtered to published)

    def test_get_listing_loads_all_relationships(
        self, repo: StoreRepository, db_session: Session
    ):
        author = _author(db_session)
        genre = _genre(db_session, "Nonfiction")
        tag = _tag(db_session, author.id, "history")
        m = _manuscript(db_session, author.id)
        _ebook(db_session, m.id)
        db_session.add(ManuscriptGenreModel(manuscript_id=m.id, genre_id=genre.id))
        db_session.add(ManuscriptTagModel(manuscript_id=m.id, tag_id=tag.id))
        db_session.commit()

        result = repo.get_listing(m.id)
        db_session.expunge_all()

        _ = result.author.display_name
        _ = [g.name for g in result.genres]
        _ = [t.name for t in result.tags]
        _ = [e.id for e in result.ebooks]

    def test_get_edition_loads_nested_manuscript_relationships(
        self, repo: StoreRepository, db_session: Session
    ):
        author = _author(db_session)
        genre = _genre(db_session, "Thriller")
        tag = _tag(db_session, author.id, "suspense")
        m = _manuscript(db_session, author.id)
        e = _ebook(db_session, m.id)
        db_session.add(ManuscriptGenreModel(manuscript_id=m.id, genre_id=genre.id))
        db_session.add(ManuscriptTagModel(manuscript_id=m.id, tag_id=tag.id))
        db_session.commit()

        result = repo.get_edition(e.id)
        db_session.expunge_all()

        ms = result.manuscript
        _ = ms.author.display_name          # joinedload(manuscript → author)
        _ = [g.name for g in ms.genres]    # selectinload(manuscript → genres)
        _ = [t.name for t in ms.tags]      # selectinload(manuscript → tags)
        _ = [e.id for e in ms.ebooks]      # selectinload(manuscript → ebooks filtered)

    def test_get_author_profile_loads_nested_manuscript_relationships(
        self, repo: StoreRepository, db_session: Session
    ):
        author = _author(db_session, is_public=True)
        genre = _genre(db_session, "Romance")
        tag = _tag(db_session, author.id, "love")
        m = _manuscript(db_session, author.id)
        _ebook(db_session, m.id)
        db_session.add(ManuscriptGenreModel(manuscript_id=m.id, genre_id=genre.id))
        db_session.add(ManuscriptTagModel(manuscript_id=m.id, tag_id=tag.id))
        db_session.commit()

        result = repo.get_author_profile(author.id)
        db_session.expunge_all()

        ms = result.manuscripts[0]
        _ = ms.author.display_name
        _ = [g.name for g in ms.genres]
        _ = [t.name for t in ms.tags]
        _ = [e.id for e in ms.ebooks]
