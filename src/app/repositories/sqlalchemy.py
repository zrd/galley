"""
SQLAlchemy repository implementations for production use with PostgreSQL.
"""

from datetime import datetime, timezone
from uuid import UUID

from slugify import slugify

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app.db.models import (
    AuthorModel,
    DownloadModel,
    EbookModel,
    GenreModel,
    ManuscriptModel,
    ManuscriptGenreModel,
    SampleModel,
    TagModel,
    ManuscriptTagModel,
)
from app.domain import Author, Download, Ebook, Genre, Manuscript, Sample, Tag


def _author_model_to_domain(model: AuthorModel) -> Author:
    return Author(
        id=model.id,
        email=model.email,
        display_name=model.display_name,
        bio=model.bio,
        website=model.website,
        avatar_key=model.avatar_key,
        is_public=model.is_public,
        password_hash=model.password_hash,
        created_at=model.created_at,
        deleted_at=model.deleted_at,
    )


def _manuscript_model_to_domain(model: ManuscriptModel) -> Manuscript:
    return Manuscript(
        id=model.id,
        author_id=model.author_id,
        title=model.title,
        description=model.description,
        genres=[_genre_model_to_domain(g) for g in model.genres],
        tags=[_tag_model_to_domain(t) for t in model.tags],
        source_format=model.source_format,
        source_file_key=model.source_file_key,
        cover_image_key=model.cover_image_key,
        state=model.state,
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted_at=model.deleted_at,
    )


def _sample_model_to_domain(model: SampleModel) -> Sample:
    return Sample(
        id=model.id,
        manuscript_id=model.manuscript_id,
        title=model.title,
        excerpt_start=model.excerpt_start,
        excerpt_end=model.excerpt_end,
        promo_header=model.promo_header,
        promo_footer=model.promo_footer,
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted_at=model.deleted_at,
    )


def _ebook_model_to_domain(model: EbookModel) -> Ebook:
    return Ebook(
        id=model.id,
        manuscript_id=model.manuscript_id,
        sample_id=model.sample_id,
        output_format=model.output_format,
        list_price_cents=model.list_price_cents,
        sale_price_cents=model.sale_price_cents,
        price_currency=model.price_currency,
        file_key=model.file_key,
        file_size_bytes=model.file_size_bytes,
        download_filename=model.download_filename,
        download_count=model.download_count,
        visibility=model.visibility,
        unlisted_download_limit=model.unlisted_download_limit,
        created_at=model.created_at,
        published_at=model.published_at,
        deleted_at=model.deleted_at,
    )


def _download_model_to_domain(model: DownloadModel) -> Download:
    return Download(
        id=model.id,
        ebook_id=model.ebook_id,
        downloaded_at=model.downloaded_at,
        ip_hash=model.ip_hash,
        tracking_code=model.tracking_code,
        deleted_at=model.deleted_at,
    )


def _genre_model_to_domain(model: GenreModel) -> Genre:
    return Genre(
        id=model.id,
        name=model.name,
        slug=model.slug,
        description=model.description,
        parent_id=model.parent_id,
    )


def _tag_model_to_domain(model: TagModel) -> Tag:
    return Tag(
        id=model.id,
        name=model.name,
        slug=model.slug,
        owner_id=model.owner_id,
        created_at=model.created_at,
        deleted_at=model.deleted_at,
    )


class SQLAlchemyAuthorRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, author: Author) -> Author:
        model = AuthorModel(
            id=author.id,
            email=author.email,
            display_name=author.display_name,
            bio=author.bio,
            website=author.website,
            avatar_key=author.avatar_key,
            is_public=author.is_public,
            password_hash=author.password_hash,
            created_at=author.created_at,
            deleted_at=author.deleted_at,
        )
        self.session.add(model)
        self.session.flush()
        return _author_model_to_domain(model)

    def get(self, author_id: UUID, *, include_deleted: bool = False) -> Author | None:
        model = self.session.get(AuthorModel, author_id)
        if model is None:
            return None
        if not include_deleted and model.deleted_at is not None:
            return None
        return _author_model_to_domain(model)

    def get_by_email(self, email: str, *, include_deleted: bool = False) -> Author | None:
        stmt = select(AuthorModel).where(AuthorModel.email == email)
        if not include_deleted:
            stmt = stmt.where(AuthorModel.deleted_at.is_(None))

        model = self.session.scalars(stmt).first()
        return _author_model_to_domain(model) if model else None

    def update(self, author: Author) -> Author:
        model = self.session.get(AuthorModel, author.id)
        if model:
            model.email = author.email
            model.display_name = author.display_name
            model.bio = author.bio
            model.website = author.website
            model.avatar_key = author.avatar_key
            model.is_public = author.is_public
            model.password_hash = author.password_hash
            model.deleted_at = author.deleted_at
            self.session.flush()
            return _author_model_to_domain(model)
        raise ValueError(f"Author {author.id} not found")

    def delete(self, author_id: UUID) -> None:
        model = self.session.get(AuthorModel, author_id)
        if model:
            self.session.delete(model)
            self.session.flush()

    def soft_delete(self, author_id: UUID) -> None:
        model = self.session.get(AuthorModel, author_id)
        if model:
            model.deleted_at = datetime.now(timezone.utc)
            self.session.flush()

    def restore(self, author_id: UUID) -> None:
        model = self.session.get(AuthorModel, author_id)
        if model:
            model.deleted_at = None
            self.session.flush()


class SQLAlchemyManuscriptRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, manuscript: Manuscript) -> Manuscript:
        model = ManuscriptModel(
            id=manuscript.id,
            author_id=manuscript.author_id,
            title=manuscript.title,
            description=manuscript.description,
            source_format=manuscript.source_format,
            source_file_key=manuscript.source_file_key,
            cover_image_key=manuscript.cover_image_key,
            state=manuscript.state,
            created_at=manuscript.created_at,
            updated_at=manuscript.updated_at,
            deleted_at=manuscript.deleted_at,
        )
        self.session.add(model)
        self.session.flush()
        return _manuscript_model_to_domain(model)

    def get(self, manuscript_id: UUID, *, include_deleted: bool = False) -> Manuscript | None:
        model = self.session.get(ManuscriptModel, manuscript_id)
        if model is None:
            return None
        if not include_deleted and model.deleted_at is not None:
            return None
        return _manuscript_model_to_domain(model)

    def list_by_author(self, author_id: UUID, *, include_deleted: bool = False) -> list[Manuscript]:
        stmt = select(ManuscriptModel).where(ManuscriptModel.author_id == author_id)
        if not include_deleted:
            stmt = stmt.where(ManuscriptModel.deleted_at.is_(None))

        stmt = stmt.order_by(ManuscriptModel.updated_at.desc())
        models = self.session.scalars(stmt).all()
        return [_manuscript_model_to_domain(m) for m in models]

    def update(self, manuscript: Manuscript) -> Manuscript:
        model = self.session.get(ManuscriptModel, manuscript.id)
        if model:
            model.title = manuscript.title
            model.description = manuscript.description
            model.source_format = manuscript.source_format
            model.source_file_key = manuscript.source_file_key
            model.cover_image_key = manuscript.cover_image_key
            model.state = manuscript.state
            model.updated_at = manuscript.updated_at
            model.deleted_at = manuscript.deleted_at
            self.session.flush()
            return _manuscript_model_to_domain(model)
        raise ValueError(f"Manuscript {manuscript.id} not found")

    def delete(self, manuscript_id: UUID) -> None:
        model = self.session.get(ManuscriptModel, manuscript_id)
        if model:
            self.session.delete(model)
            self.session.flush()

    def soft_delete(self, manuscript_id: UUID) -> None:
        model = self.session.get(ManuscriptModel, manuscript_id)
        if model:
            model.deleted_at = datetime.now(timezone.utc)
            self.session.flush()

    def restore(self, manuscript_id: UUID) -> None:
        model = self.session.get(ManuscriptModel, manuscript_id)
        if model:
            model.deleted_at = None
            self.session.flush()

    def set_genres(self, manuscript_id: UUID, genre_ids: list[int]) -> None:
        stmt = delete(ManuscriptGenreModel).where(ManuscriptGenreModel.manuscript_id == manuscript_id)
        self.session.execute(stmt)
        for genre_id in genre_ids:
            self.session.add(
                ManuscriptGenreModel(manuscript_id=manuscript_id, genre_id=genre_id)
            )
        self.session.flush()

    def set_tags(self, manuscript_id: UUID, tag_ids: list[UUID]) -> None:
        stmt = delete(ManuscriptTagModel).where(ManuscriptTagModel.manuscript_id == manuscript_id)
        self.session.execute(stmt)
        for tag_id in tag_ids:
            self.session.add(
                ManuscriptTagModel(manuscript_id=manuscript_id, tag_id=tag_id)
            )
        self.session.flush()


class SQLAlchemySampleRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, sample: Sample) -> Sample:
        model = SampleModel(
            id=sample.id,
            manuscript_id=sample.manuscript_id,
            title=sample.title,
            excerpt_start=sample.excerpt_start,
            excerpt_end=sample.excerpt_end,
            promo_header=sample.promo_header,
            promo_footer=sample.promo_footer,
            created_at=sample.created_at,
            updated_at=sample.updated_at,
            deleted_at=sample.deleted_at,
        )
        self.session.add(model)
        self.session.flush()
        return _sample_model_to_domain(model)

    def get(self, sample_id: UUID, *, include_deleted: bool = False) -> Sample | None:
        model = self.session.get(SampleModel, sample_id)
        if model is None:
            return None
        if not include_deleted and model.deleted_at is not None:
            return None
        return _sample_model_to_domain(model)

    def list_by_manuscript(self, manuscript_id: UUID, *, include_deleted: bool = False) -> list[Sample]:
        stmt = select(SampleModel).where(SampleModel.manuscript_id == manuscript_id)
        if not include_deleted:
            stmt = stmt.where(SampleModel.deleted_at.is_(None))

        stmt = stmt.order_by(SampleModel.created_at.desc())
        models = self.session.scalars(stmt).all()
        return [_sample_model_to_domain(m) for m in models]

    def update(self, sample: Sample) -> Sample:
        model = self.session.get(SampleModel, sample.id)
        if model:
            model.title = sample.title
            model.excerpt_start = sample.excerpt_start
            model.excerpt_end = sample.excerpt_end
            model.promo_header = sample.promo_header
            model.promo_footer = sample.promo_footer
            model.updated_at = sample.updated_at
            model.deleted_at = sample.deleted_at
            self.session.flush()
            return _sample_model_to_domain(model)
        raise ValueError(f"Sample {sample.id} not found")

    def delete(self, sample_id: UUID) -> None:
        model = self.session.get(SampleModel, sample_id)
        if model:
            self.session.delete(model)
            self.session.flush()

    def soft_delete(self, sample_id: UUID) -> None:
        model = self.session.get(SampleModel, sample_id)
        if model:
            model.deleted_at = datetime.now(timezone.utc)
            self.session.flush()

    def soft_delete_by_manuscript(self, manuscript_id: UUID) -> None:
        now = datetime.now(timezone.utc)
        stmt = update(SampleModel).where(
            SampleModel.manuscript_id == manuscript_id, SampleModel.deleted_at.is_(None)
        ).values(deleted_at=now)
        self.session.execute(stmt)
        self.session.flush()

    def restore(self, sample_id: UUID) -> None:
        model = self.session.get(SampleModel, sample_id)
        if model:
            model.deleted_at = None
            self.session.flush()

    def restore_by_manuscript(self, manuscript_id: UUID) -> None:
        stmt = update(SampleModel).where(
            SampleModel.manuscript_id == manuscript_id, SampleModel.deleted_at.is_not(None)
        ).values(deleted_at=None)
        self.session.execute(stmt)
        self.session.flush()


class SQLAlchemyEbookRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, ebook: Ebook) -> Ebook:
        model = EbookModel(
            id=ebook.id,
            manuscript_id=ebook.manuscript_id,
            sample_id=ebook.sample_id,
            output_format=ebook.output_format,
            list_price_cents=ebook.list_price_cents,
            sale_price_cents=ebook.sale_price_cents,
            price_currency=ebook.price_currency,
            file_key=ebook.file_key,
            file_size_bytes=ebook.file_size_bytes,
            download_filename=ebook.download_filename,
            download_count=ebook.download_count,
            visibility=ebook.visibility,
            unlisted_download_limit=ebook.unlisted_download_limit,
            created_at=ebook.created_at,
            published_at=ebook.published_at,
            deleted_at=ebook.deleted_at,
        )
        self.session.add(model)
        self.session.flush()
        return _ebook_model_to_domain(model)

    def get(self, ebook_id: UUID, *, include_deleted: bool = False) -> Ebook | None:
        model = self.session.get(EbookModel, ebook_id)
        if model is None:
            return None
        if not include_deleted and model.deleted_at is not None:
            return None
        return _ebook_model_to_domain(model)

    def list_by_manuscript(self, manuscript_id: UUID, *, include_deleted: bool = False) -> list[Ebook]:
        stmt = select(EbookModel).where(EbookModel.manuscript_id == manuscript_id)
        if not include_deleted:
            stmt = stmt.where(EbookModel.deleted_at.is_(None))

        stmt = stmt.order_by(EbookModel.created_at.desc())
        models = self.session.scalars(stmt).all()
        return [_ebook_model_to_domain(m) for m in models]

    def list_by_author(self, author_id: UUID, *, include_deleted: bool = False) -> list[Ebook]:
        stmt = (select(EbookModel)
                .join(ManuscriptModel)
                .where(ManuscriptModel.author_id == author_id)
        )
        if not include_deleted:
            stmt = stmt.where(EbookModel.deleted_at.is_(None))

        stmt = stmt.order_by(EbookModel.created_at.desc())
        models = self.session.scalars(stmt).all()
        return [_ebook_model_to_domain(m) for m in models]

    def list_by_sample(self, sample_id: UUID, *, include_deleted: bool = False) -> list[Ebook]:
        stmt = select(EbookModel).where(EbookModel.sample_id == sample_id)
        if not include_deleted:
            stmt = stmt.where(EbookModel.deleted_at.is_(None))

        stmt = stmt.order_by(EbookModel.created_at.desc())
        models = self.session.scalars(stmt).all()
        return [_ebook_model_to_domain(m) for m in models]

    def update(self, ebook: Ebook) -> Ebook:
        model = self.session.get(EbookModel, ebook.id)
        if model:
            model.list_price_cents = ebook.list_price_cents
            model.sale_price_cents = ebook.sale_price_cents
            model.price_currency = ebook.price_currency
            model.download_count = ebook.download_count
            model.visibility = ebook.visibility
            model.unlisted_download_limit = ebook.unlisted_download_limit
            model.published_at = ebook.published_at
            model.deleted_at = ebook.deleted_at
            self.session.flush()
            return _ebook_model_to_domain(model)
        raise ValueError(f"Ebook {ebook.id} not found")

    def delete(self, ebook_id: UUID) -> None:
        model = self.session.get(EbookModel, ebook_id)
        if model:
            self.session.delete(model)
            self.session.flush()

    def delete_by_manuscript(self, manuscript_id: UUID) -> None:
        stmt = delete(EbookModel).where(EbookModel.manuscript_id == manuscript_id)
        self.session.execute(stmt)
        self.session.flush()

    def soft_delete(self, ebook_id: UUID) -> None:
        model = self.session.get(EbookModel, ebook_id)
        if model:
            model.deleted_at = datetime.now(timezone.utc)
            self.session.flush()

    def soft_delete_by_manuscript(self, manuscript_id: UUID) -> None:
        now = datetime.now(timezone.utc)
        stmt = update(EbookModel).where(
            EbookModel.manuscript_id == manuscript_id, EbookModel.deleted_at.is_(None)
        ).values(deleted_at=now)
        self.session.execute(stmt)
        self.session.flush()

    def soft_delete_by_sample(self, sample_id: UUID) -> None:
        now = datetime.now(timezone.utc)
        stmt = update(EbookModel).where(
            EbookModel.sample_id == sample_id, EbookModel.deleted_at.is_(None)
        ).values(deleted_at=now)
        self.session.execute(stmt)
        self.session.flush()

    def restore(self, ebook_id: UUID) -> None:
        model = self.session.get(EbookModel, ebook_id)
        if model:
            model.deleted_at = None
            self.session.flush()

    def restore_by_manuscript(self, manuscript_id: UUID) -> None:
        stmt = update(EbookModel).where(
            EbookModel.manuscript_id == manuscript_id, EbookModel.deleted_at.is_not(None)
        ).values(deleted_at=None)
        self.session.execute(stmt)
        self.session.flush()

    def restore_by_sample(self, sample_id: UUID) -> None:
        stmt = update(EbookModel).where(
            EbookModel.sample_id == sample_id, EbookModel.deleted_at.is_not(None)
        ).values(deleted_at=None)
        self.session.execute(stmt)
        self.session.flush()


class SQLAlchemyDownloadRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, download: Download) -> Download:
        model = DownloadModel(
            id=download.id,
            ebook_id=download.ebook_id,
            downloaded_at=download.downloaded_at,
            ip_hash=download.ip_hash,
            tracking_code=download.tracking_code,
            deleted_at=download.deleted_at,
        )
        self.session.add(model)
        self.session.flush()
        return _download_model_to_domain(model)

    def get(self, download_id: UUID, *, include_deleted: bool = False) -> Download | None:
        model = self.session.get(DownloadModel, download_id)
        if model is None:
            return None
        if not include_deleted and model.deleted_at is not None:
            return None
        return _download_model_to_domain(model)

    def list_by_ebook(self, ebook_id: UUID, *, include_deleted: bool = False) -> list[Download]:
        stmt = select(DownloadModel).where(DownloadModel.ebook_id == ebook_id)
        if not include_deleted:
            stmt = stmt.where(DownloadModel.deleted_at.is_(None))

        stmt = stmt.order_by(DownloadModel.downloaded_at.desc())
        models = self.session.scalars(stmt).all()
        return [_download_model_to_domain(m) for m in models]

    def count_by_ebook(self, ebook_id: UUID, *, include_deleted: bool = False) -> int:
        stmt = select(func.count(DownloadModel.id)).where(DownloadModel.ebook_id == ebook_id)
        if not include_deleted:
            stmt = stmt.where(DownloadModel.deleted_at.is_(None))

        return self.session.scalar(stmt) or 0


class SQLAlchemyGenreRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, genre: Genre) -> Genre:
        model = GenreModel(
            name=genre.name,
            slug=genre.slug,
            description=genre.description,
            parent_id=genre.parent_id,
        )
        self.session.add(model)
        self.session.flush()
        return _genre_model_to_domain(model)

    def get(self, genre_id: int) -> Genre | None:
        model = self.session.get(GenreModel, genre_id)
        if model is None:
            return None
        return _genre_model_to_domain(model)

    def list_all(self) -> list[Genre]:
        stmt = select(GenreModel)
        models = self.session.scalars(stmt).all()
        return [_genre_model_to_domain(m) for m in models]

    def list_by_parent(self, parent_id: int) -> list[Genre]:
        stmt = select(GenreModel).where(GenreModel.parent_id == parent_id)
        models = self.session.scalars(stmt).all()
        return [_genre_model_to_domain(m) for m in models]

    def list_top_level(self) -> list[Genre]:
        stmt = select(GenreModel).where(GenreModel.parent_id.is_(None))
        models = self.session.scalars(stmt).all()
        return [_genre_model_to_domain(m) for m in models]


class SQLAlchemyTagRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, tag: Tag) -> Tag:
        model = TagModel(
            id=tag.id,
            name=tag.name,
            slug=tag.slug,
            owner_id=tag.owner_id,
            created_at=tag.created_at,
            deleted_at=tag.deleted_at,
        )
        self.session.add(model)
        self.session.flush()
        return _tag_model_to_domain(model)

    def get(self, tag_id: UUID) -> Tag | None:
        stmt = select(TagModel).where(TagModel.id == tag_id)
        model = self.session.scalars(stmt).one_or_none()
        if model is None:
            return None
        return _tag_model_to_domain(model)

    def list_by_owner(self, owner_id: UUID) -> list[Tag]:
        stmt = select(TagModel).where(TagModel.owner_id == owner_id).order_by(TagModel.name)
        models = self.session.scalars(stmt).all()
        return [_tag_model_to_domain(m) for m in models]

    def update(self, tag: Tag) -> Tag:
        model = self.session.get(TagModel, tag.id)
        if model:
            model.name = tag.name
            model.slug = tag.slug
            model.owner_id = tag.owner_id
            model.created_at = tag.created_at
            model.deleted_at = tag.deleted_at
            self.session.flush()
            return _tag_model_to_domain(model)
        raise ValueError(f"Tag {tag.id} not found")

    def get_by_slug(self, slug: str, owner_id: UUID) -> Tag | None:
        stmt = select(TagModel).where(TagModel.slug == slug, TagModel.owner_id == owner_id)
        model = self.session.scalars(stmt).one_or_none()
        if model is None:
            return None
        return _tag_model_to_domain(model)

    def get_or_create(self, name: str, owner_id: UUID) -> Tag:
        slug = slugify(name)
        tag = self.get_by_slug(slug, owner_id)
        if tag is None:
            tag = self.add(Tag(
                name=name,
                slug=slug,
                owner_id=owner_id,
            ))
        elif tag.is_deleted:
            tag.restore()
            tag = self.update(tag)

        return tag

    def list_popular(self, top_n: int) -> list[Tag]:
        stmt = (
            select(TagModel, func.count(ManuscriptTagModel.manuscript_id).label("usage_count"))
            .join(ManuscriptTagModel, ManuscriptTagModel.tag_id == TagModel.id, isouter=True)
            .where(TagModel.deleted_at.is_(None))
            .group_by(TagModel.id)
            .order_by(func.count(ManuscriptTagModel.manuscript_id).desc())
            .limit(top_n)
        )
        rows = self.session.execute(stmt).all()
        return [_tag_model_to_domain(row.TagModel) for row in rows]

    def list_all(self) -> list[Tag]:
        stmt = (
            select(TagModel, func.count(ManuscriptTagModel.manuscript_id).label("usage_count"))
            .join(ManuscriptTagModel, ManuscriptTagModel.tag_id == TagModel.id, isouter=True)
            .where(TagModel.deleted_at.is_(None))
            .group_by(TagModel.id)
            .order_by(func.count(ManuscriptTagModel.manuscript_id).desc())
        )
        rows = self.session.execute(stmt).all()
        return [_tag_model_to_domain(row.TagModel) for row in rows]
