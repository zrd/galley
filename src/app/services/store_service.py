from collections.abc import Sequence
from uuid import UUID

from app.db import AuthorModel, EbookModel, GenreModel, ManuscriptModel
from app.domain import AuthorNotFound, EbookNotFound, ManuscriptNotFound, UnlistedDownloadLimitExceeded, Visibility
from app.repositories import SQLAlchemyStoreRepository
from app.schemas.genre import StoreGenreTree


class StoreService:
    def __init__(self, repo: SQLAlchemyStoreRepository):
        self.repo = repo

    def browse_listings(
            self,
            page: int,
            per_page: int,
            author_ids: list[UUID] | None = None,
            genre_slugs: list[str] | None = None,
            tag_slugs: list[str] | None = None,
            min_price: int | None = None,
            max_price: int | None = None,
            search_term: str | None = None,
            sorting_method: str = "newest",
    ) -> tuple[Sequence[ManuscriptModel], int]:
        """Returns (results, total) for the requested page."""
        offset = (page - 1) * per_page
        return self.repo.browse_listings(
            offset=offset,
            limit=per_page,
            author_ids=author_ids,
            genre_slugs=genre_slugs,
            tag_slugs=tag_slugs,
            min_price=min_price,
            max_price=max_price,
            search_term=search_term,
            sorting_method=sorting_method,
        )

    def get_listing(self, manuscript_id: UUID) -> ManuscriptModel:
        listing = self.repo.get_listing(manuscript_id)
        if listing is None:
            raise ManuscriptNotFound(f"Manuscript {manuscript_id} not found")

        return listing

    def get_edition(self, ebook_id: UUID) -> EbookModel:
        edition = self.repo.get_edition(ebook_id)
        if edition is None:
            raise EbookNotFound(f"Ebook {ebook_id} not found")
        if (
            edition.visibility == Visibility.UNLISTED
            and edition.unlisted_download_limit is not None
            and edition.download_count >= edition.unlisted_download_limit
        ):
            raise UnlistedDownloadLimitExceeded(f"Exceeded {edition.unlisted_download_limit} downloads for this edition")

        return edition

    def list_author_profiles(self, page: int, per_page: int) -> tuple[Sequence[AuthorModel], int]:
        """Returns (results, total) for the requested page."""
        offset = (page - 1) * per_page
        return self.repo.list_author_profiles(offset, limit=per_page)

    def get_author_profile(self, author_id: UUID) -> AuthorModel:
        profile = self.repo.get_author_profile(author_id)
        if profile is None:
            raise AuthorNotFound(f"Author {author_id} not found")

        return profile

    def list_genres_with_counts(self) -> list[StoreGenreTree]:
        counted_genres: list[tuple[GenreModel, int]] = self.repo.list_genres_with_counts()
        nodes = {
            g[0].id: StoreGenreTree(
                id=g[0].id, name=g[0].name, slug=g[0].slug, published_count=g[1], description=g[0].description
            ) for g in counted_genres
        }
        roots = []
        for g in counted_genres:
            if g[0].parent_id is None:
                roots.append(nodes[g[0].id])
            else:
                nodes[g[0].parent_id].children.append(nodes[g[0].id])

        return roots
