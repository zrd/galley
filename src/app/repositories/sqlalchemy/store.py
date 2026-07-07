from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.models import (
    AuthorModel,
    EbookModel,
    GenreModel,
    ManuscriptGenreModel,
    ManuscriptModel,
    ManuscriptTagModel,
    TagModel,
)
from app.domain import Visibility


class StoreRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def browse_listings(
            self,
            offset: int,
            limit: int,
            author_ids: list[UUID] | None = None,
            genre_slugs: list[str] | None = None,
            tag_slugs: list[str] | None = None,
            min_price: int | None = None,
            max_price: int | None = None,
            search_term: str | None = None,
            sorting_method: str = "newest",
    ) -> tuple[Sequence[ManuscriptModel], int]:
        """Return a paginated page of store listings and the total unpaged count.

        A listing is a manuscript with at least one active published edition.
        Eager-loads author, genres, tags, and published editions on each result.

        Returns (results, total) where total is the count across all pages.
        """
        has_published_ebook = (
            select(EbookModel.id)
            .where(
                EbookModel.manuscript_id == ManuscriptModel.id,
                EbookModel.visibility == Visibility.PUBLISHED,
                EbookModel.deleted_at.is_(None),
            ).exists()
        )
        stmt = (
            select(ManuscriptModel)
            .where(
                has_published_ebook,
                ManuscriptModel.deleted_at.is_(None),
            )
            .options(
                joinedload(ManuscriptModel.author),
                selectinload(ManuscriptModel.genres),
                selectinload(ManuscriptModel.tags),
                selectinload(ManuscriptModel.ebooks.and_(
                    EbookModel.visibility == Visibility.PUBLISHED,
                    EbookModel.deleted_at.is_(None),
                )),
            )
            .offset(offset)
            .limit(limit)
        )
        count_stmt = (
            select(func.count())
            .select_from(ManuscriptModel)
            .where(
                has_published_ebook,
                ManuscriptModel.deleted_at.is_(None),
            )
        )
        if author_ids:
            by_author = ManuscriptModel.author_id.in_(author_ids)
            stmt = stmt.where(by_author)
            count_stmt = count_stmt.where(by_author)

        if genre_slugs:
            genre_filter = (
                select(ManuscriptGenreModel.manuscript_id)
                .join(GenreModel)
                .where(
                    ManuscriptGenreModel.manuscript_id == ManuscriptModel.id,
                    GenreModel.slug.in_(genre_slugs),
                )
                .exists()
                .correlate(ManuscriptModel)
            )
            stmt = stmt.where(genre_filter)
            count_stmt = count_stmt.where(genre_filter)

        if tag_slugs:
            tag_filter = (
                select(ManuscriptTagModel.manuscript_id)
                .join(TagModel)
                .where(
                    ManuscriptTagModel.manuscript_id == ManuscriptModel.id,
                    TagModel.slug.in_(tag_slugs),
                )
                .exists()
                .correlate(ManuscriptModel)
            )
            stmt = stmt.where(tag_filter)
            count_stmt = count_stmt.where(tag_filter)

        effective_price = case(
            (EbookModel.sale_price_cents.is_not(None), EbookModel.sale_price_cents),
            (EbookModel.list_price_cents.is_not(None), EbookModel.list_price_cents),
            else_=0
        )
        if min_price is not None:
            min_price_filter = (
                select(EbookModel.id)
                .where(
                    EbookModel.manuscript_id == ManuscriptModel.id,
                    effective_price >= min_price,
                    EbookModel.visibility == Visibility.PUBLISHED,
                    EbookModel.deleted_at.is_(None),
                )
                .exists()
                .correlate(ManuscriptModel)
            )
            stmt = stmt.where(min_price_filter)
            count_stmt = count_stmt.where(min_price_filter)

        if max_price is not None:
            max_price_filter = (
                select(EbookModel.id)
                .where(
                    EbookModel.manuscript_id == ManuscriptModel.id,
                    effective_price <= max_price,
                    EbookModel.visibility == Visibility.PUBLISHED,
                    EbookModel.deleted_at.is_(None),
                )
                .exists()
                .correlate(ManuscriptModel)
            )
            stmt = stmt.where(max_price_filter)
            count_stmt = count_stmt.where(max_price_filter)

        if search_term is not None:
            search_filter = (
                select(AuthorModel.id)
                .where(
                    AuthorModel.id == ManuscriptModel.author_id,
                    ManuscriptModel.title.ilike(f"%{search_term}%")
                    | ManuscriptModel.description.ilike(f"%{search_term}%")
                    | AuthorModel.display_name.ilike(f"%{search_term}%"),
                )
                .exists()
                .correlate(ManuscriptModel)
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        first_published_at = (
            select(func.min(EbookModel.published_at))
            .where(
                EbookModel.manuscript_id == ManuscriptModel.id,
                EbookModel.visibility == Visibility.PUBLISHED,
                EbookModel.deleted_at.is_(None),
            )
            .scalar_subquery()
            .correlate(ManuscriptModel)
        )
        min_effective_price = (
            select(func.min(effective_price))
            .where(
                EbookModel.manuscript_id == ManuscriptModel.id,
                EbookModel.visibility == Visibility.PUBLISHED,
                EbookModel.deleted_at.is_(None),
            )
            .scalar_subquery()
            .correlate(ManuscriptModel)
        )
        ordering = {
            "a_to_z": ManuscriptModel.title.asc(),
            "z_to_a": ManuscriptModel.title.desc(),
            "newest": first_published_at.desc(),
            "oldest": first_published_at.asc(),
            "least_expensive": min_effective_price.asc(),
            "most_expensive": min_effective_price.desc(),
        }
        stmt = stmt.order_by(ordering.get(sorting_method, ordering["newest"]))
        total_count = self.session.scalar(count_stmt) or 0
        return self.session.scalars(stmt).unique().all(), total_count

    def get_listing(self, manuscript_id: UUID) -> ManuscriptModel | None:
        has_published_ebook = (
            select(EbookModel.id)
            .where(
                EbookModel.manuscript_id == ManuscriptModel.id,
                EbookModel.visibility == Visibility.PUBLISHED,
                EbookModel.deleted_at.is_(None),
            ).exists()
        )

        stmt = (
            select(ManuscriptModel)
            .where(
                ManuscriptModel.id == manuscript_id,
                has_published_ebook,
                ManuscriptModel.deleted_at.is_(None),
            )
            .options(
                joinedload(ManuscriptModel.author),
                selectinload(ManuscriptModel.genres),
                selectinload(ManuscriptModel.tags),
                selectinload(ManuscriptModel.ebooks.and_(
                    EbookModel.visibility == Visibility.PUBLISHED,
                    EbookModel.deleted_at.is_(None),
                )),
            )
        )
        return self.session.scalars(stmt).unique().first()

    def get_edition(self, ebook_id: UUID) -> EbookModel | None:
        stmt = (
            select(EbookModel)
            .where(
                EbookModel.id == ebook_id,
                EbookModel.visibility.in_([Visibility.PUBLISHED, Visibility.UNLISTED]),
                EbookModel.deleted_at.is_(None),
            ).options(
                joinedload(EbookModel.manuscript).options(
                    joinedload(ManuscriptModel.author),
                    selectinload(ManuscriptModel.genres),
                    selectinload(ManuscriptModel.tags),
                    selectinload(ManuscriptModel.ebooks.and_(
                        EbookModel.visibility == Visibility.PUBLISHED,
                        EbookModel.deleted_at.is_(None),
                    )),
                )
            )
        )
        return self.session.scalars(stmt).unique().first()

    def list_author_profiles(self, offset: int, limit: int) -> tuple[Sequence[AuthorModel], int]:
        """Return a paginated page of author listings and the total unpaged count.

        Any author with a public profile will be listed, regardless of the
        published/unpublished or visibility status of the author's Manuscripts
        and Ebooks.

        Returns (results, total) where total is the count across all pages.
        """
        stmt = (
            select(AuthorModel)
            .where(
                AuthorModel.is_public.is_(True),
                AuthorModel.deleted_at.is_(None),
            )
            .offset(offset)
            .limit(limit)
        )
        count_stmt = (
            select(func.count())
            .select_from(AuthorModel)
            .where(
                AuthorModel.is_public.is_(True),
                AuthorModel.deleted_at.is_(None),
            )
        )
        total_count = self.session.scalar(count_stmt) or 0
        return self.session.scalars(stmt).unique().all(), total_count

    def get_author_profile(self, author_id: UUID) -> AuthorModel | None:
        stmt = (
            select(AuthorModel)
            .where(
                AuthorModel.id == author_id,
                AuthorModel.is_public.is_(True),
                AuthorModel.deleted_at.is_(None),
            )
            .options(
                selectinload(AuthorModel.manuscripts.and_(
                    ManuscriptModel.deleted_at.is_(None),
                )).options(
                    joinedload(ManuscriptModel.author),
                    selectinload(ManuscriptModel.genres),
                    selectinload(ManuscriptModel.tags),
                    selectinload(ManuscriptModel.ebooks.and_(
                        EbookModel.visibility == Visibility.PUBLISHED,
                        EbookModel.deleted_at.is_(None),
                    )),
                )
            )
        )
        return self.session.scalars(stmt).unique().first()

    def list_genres_with_counts(self) -> list[tuple[GenreModel, int]]:
        on_manuscript_filter = (
            (ManuscriptGenreModel.manuscript_id == ManuscriptModel.id)
            & (ManuscriptModel.deleted_at.is_(None))
        )
        on_ebook_filter = (
            (ManuscriptModel.id == EbookModel.manuscript_id)
             & (EbookModel.visibility == Visibility.PUBLISHED)
             & (EbookModel.deleted_at.is_(None))
        )
        stmt = (
            select(GenreModel, func.count(EbookModel.manuscript_id.distinct()).label("occurs"))
            .outerjoin(ManuscriptGenreModel, GenreModel.id == ManuscriptGenreModel.genre_id)
            .outerjoin(ManuscriptModel, on_manuscript_filter)
            .outerjoin(EbookModel, on_ebook_filter)
            .group_by(GenreModel.id)
        )
        return [(row.GenreModel, row.occurs) for row in self.session.execute(stmt).all()]
