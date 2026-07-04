from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.db.models import (
    EbookModel,
    ManuscriptModel,
)
from app.domain import Ebook

from ._mappers import ebook_model_to_domain


class EbookRepository:
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
        return ebook_model_to_domain(model)

    def get(self, ebook_id: UUID, *, include_deleted: bool = False) -> Ebook | None:
        model = self.session.get(EbookModel, ebook_id)
        if model is None:
            return None
        if not include_deleted and model.deleted_at is not None:
            return None
        return ebook_model_to_domain(model)

    def list_by_manuscript(self, manuscript_id: UUID, *, include_deleted: bool = False) -> list[Ebook]:
        stmt = select(EbookModel).where(EbookModel.manuscript_id == manuscript_id)
        if not include_deleted:
            stmt = stmt.where(EbookModel.deleted_at.is_(None))

        stmt = stmt.order_by(EbookModel.created_at.desc())
        models = self.session.scalars(stmt).all()
        return [ebook_model_to_domain(m) for m in models]

    def list_by_author(self, author_id: UUID, *, include_deleted: bool = False) -> list[Ebook]:
        stmt = (select(EbookModel)
                .join(ManuscriptModel)
                .where(ManuscriptModel.author_id == author_id)
        )
        if not include_deleted:
            stmt = stmt.where(EbookModel.deleted_at.is_(None))

        stmt = stmt.order_by(EbookModel.created_at.desc())
        models = self.session.scalars(stmt).all()
        return [ebook_model_to_domain(m) for m in models]

    def list_by_sample(self, sample_id: UUID, *, include_deleted: bool = False) -> list[Ebook]:
        stmt = select(EbookModel).where(EbookModel.sample_id == sample_id)
        if not include_deleted:
            stmt = stmt.where(EbookModel.deleted_at.is_(None))

        stmt = stmt.order_by(EbookModel.created_at.desc())
        models = self.session.scalars(stmt).all()
        return [ebook_model_to_domain(m) for m in models]

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
            return ebook_model_to_domain(model)
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
