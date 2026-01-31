"""
SQLAlchemy repository implementations for production use with PostgreSQL.
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import (
    AuthorModel,
    DownloadModel,
    EbookModel,
    ManuscriptModel,
    SampleModel,
)
from app.domain import Author, Download, Ebook, Manuscript, Sample


def _author_model_to_domain(model: AuthorModel) -> Author:
    return Author(
        id=model.id,
        email=model.email,
        password_hash=model.password_hash,
        display_name=model.display_name,
        created_at=model.created_at,
    )


def _manuscript_model_to_domain(model: ManuscriptModel) -> Manuscript:
    return Manuscript(
        id=model.id,
        author_id=model.author_id,
        title=model.title,
        description=model.description,
        source_format=model.source_format,
        source_file_key=model.source_file_key,
        state=model.state,
        created_at=model.created_at,
        updated_at=model.updated_at,
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
    )


def _ebook_model_to_domain(model: EbookModel) -> Ebook:
    return Ebook(
        id=model.id,
        manuscript_id=model.manuscript_id,
        sample_id=model.sample_id,
        output_format=model.output_format,
        file_key=model.file_key,
        file_size_bytes=model.file_size_bytes,
        download_count=model.download_count,
        created_at=model.created_at,
    )


def _download_model_to_domain(model: DownloadModel) -> Download:
    return Download(
        id=model.id,
        ebook_id=model.ebook_id,
        downloaded_at=model.downloaded_at,
        ip_hash=model.ip_hash,
        tracking_code=model.tracking_code,
    )


class SQLAlchemyAuthorRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, author: Author) -> Author:
        model = AuthorModel(
            id=author.id,
            email=author.email,
            password_hash=author.password_hash,
            display_name=author.display_name,
            created_at=author.created_at,
        )
        self.session.add(model)
        self.session.flush()
        return _author_model_to_domain(model)

    def get(self, author_id: UUID) -> Author | None:
        model = self.session.get(AuthorModel, author_id)
        return _author_model_to_domain(model) if model else None

    def get_by_email(self, email: str) -> Author | None:
        model = self.session.query(AuthorModel).filter(AuthorModel.email == email).first()
        return _author_model_to_domain(model) if model else None

    def update(self, author: Author) -> Author:
        model = self.session.get(AuthorModel, author.id)
        if model:
            model.email = author.email
            model.display_name = author.display_name
            model.password_hash = author.password_hash
            self.session.flush()
            return _author_model_to_domain(model)
        raise ValueError(f"Author {author.id} not found")

    def delete(self, author_id: UUID) -> None:
        model = self.session.get(AuthorModel, author_id)
        if model:
            self.session.delete(model)
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
            state=manuscript.state,
            created_at=manuscript.created_at,
            updated_at=manuscript.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return _manuscript_model_to_domain(model)

    def get(self, manuscript_id: UUID) -> Manuscript | None:
        model = self.session.get(ManuscriptModel, manuscript_id)
        return _manuscript_model_to_domain(model) if model else None

    def list_by_author(self, author_id: UUID) -> list[Manuscript]:
        models = (
            self.session.query(ManuscriptModel)
            .filter(ManuscriptModel.author_id == author_id)
            .order_by(ManuscriptModel.updated_at.desc())
            .all()
        )
        return [_manuscript_model_to_domain(m) for m in models]

    def update(self, manuscript: Manuscript) -> Manuscript:
        model = self.session.get(ManuscriptModel, manuscript.id)
        if model:
            model.title = manuscript.title
            model.description = manuscript.description
            model.source_format = manuscript.source_format
            model.source_file_key = manuscript.source_file_key
            model.state = manuscript.state
            model.updated_at = manuscript.updated_at
            self.session.flush()
            return _manuscript_model_to_domain(model)
        raise ValueError(f"Manuscript {manuscript.id} not found")

    def delete(self, manuscript_id: UUID) -> None:
        model = self.session.get(ManuscriptModel, manuscript_id)
        if model:
            self.session.delete(model)
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
        )
        self.session.add(model)
        self.session.flush()
        return _sample_model_to_domain(model)

    def get(self, sample_id: UUID) -> Sample | None:
        model = self.session.get(SampleModel, sample_id)
        return _sample_model_to_domain(model) if model else None

    def list_by_manuscript(self, manuscript_id: UUID) -> list[Sample]:
        models = (
            self.session.query(SampleModel)
            .filter(SampleModel.manuscript_id == manuscript_id)
            .order_by(SampleModel.created_at.desc())
            .all()
        )
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
            self.session.flush()
            return _sample_model_to_domain(model)
        raise ValueError(f"Sample {sample.id} not found")

    def delete(self, sample_id: UUID) -> None:
        model = self.session.get(SampleModel, sample_id)
        if model:
            self.session.delete(model)
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
            file_key=ebook.file_key,
            file_size_bytes=ebook.file_size_bytes,
            download_count=ebook.download_count,
            created_at=ebook.created_at,
        )
        self.session.add(model)
        self.session.flush()
        return _ebook_model_to_domain(model)

    def get(self, ebook_id: UUID) -> Ebook | None:
        model = self.session.get(EbookModel, ebook_id)
        return _ebook_model_to_domain(model) if model else None

    def list_by_manuscript(self, manuscript_id: UUID) -> list[Ebook]:
        models = (
            self.session.query(EbookModel)
            .filter(EbookModel.manuscript_id == manuscript_id)
            .order_by(EbookModel.created_at.desc())
            .all()
        )
        return [_ebook_model_to_domain(m) for m in models]

    def list_by_author(self, author_id: UUID) -> list[Ebook]:
        models = (
            self.session.query(EbookModel)
            .join(ManuscriptModel)
            .filter(ManuscriptModel.author_id == author_id)
            .order_by(EbookModel.created_at.desc())
            .all()
        )
        return [_ebook_model_to_domain(m) for m in models]

    def update(self, ebook: Ebook) -> Ebook:
        model = self.session.get(EbookModel, ebook.id)
        if model:
            model.download_count = ebook.download_count
            self.session.flush()
            return _ebook_model_to_domain(model)
        raise ValueError(f"Ebook {ebook.id} not found")

    def delete(self, ebook_id: UUID) -> None:
        model = self.session.get(EbookModel, ebook_id)
        if model:
            self.session.delete(model)
            self.session.flush()

    def delete_by_manuscript(self, manuscript_id: UUID) -> None:
        self.session.query(EbookModel).filter(
            EbookModel.manuscript_id == manuscript_id
        ).delete()
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
        )
        self.session.add(model)
        self.session.flush()
        return _download_model_to_domain(model)

    def get(self, download_id: UUID) -> Download | None:
        model = self.session.get(DownloadModel, download_id)
        return _download_model_to_domain(model) if model else None

    def list_by_ebook(self, ebook_id: UUID) -> list[Download]:
        models = (
            self.session.query(DownloadModel)
            .filter(DownloadModel.ebook_id == ebook_id)
            .order_by(DownloadModel.downloaded_at.desc())
            .all()
        )
        return [_download_model_to_domain(m) for m in models]

    def count_by_ebook(self, ebook_id: UUID) -> int:
        return (
            self.session.query(DownloadModel)
            .filter(DownloadModel.ebook_id == ebook_id)
            .count()
        )
