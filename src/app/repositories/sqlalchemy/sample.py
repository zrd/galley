from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db.models import (
    SampleModel,
)
from app.domain import Sample

from ._mappers import sample_model_to_domain


class SampleRepository:
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
        return sample_model_to_domain(model)

    def get(self, sample_id: UUID, *, include_deleted: bool = False) -> Sample | None:
        model = self.session.get(SampleModel, sample_id)
        if model is None:
            return None
        if not include_deleted and model.deleted_at is not None:
            return None
        return sample_model_to_domain(model)

    def list_by_manuscript(self, manuscript_id: UUID, *, include_deleted: bool = False) -> list[Sample]:
        stmt = select(SampleModel).where(SampleModel.manuscript_id == manuscript_id)
        if not include_deleted:
            stmt = stmt.where(SampleModel.deleted_at.is_(None))

        stmt = stmt.order_by(SampleModel.created_at.desc())
        models = self.session.scalars(stmt).all()
        return [sample_model_to_domain(m) for m in models]

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
            return sample_model_to_domain(model)
        raise ValueError(f"Sample {sample.id} not found")

    def delete(self, sample_id: UUID) -> None:
        model = self.session.get(SampleModel, sample_id)
        if model:
            self.session.delete(model)
            self.session.flush()

    def soft_delete(self, sample_id: UUID) -> None:
        model = self.session.get(SampleModel, sample_id)
        if model:
            model.deleted_at = datetime.now(UTC)
            self.session.flush()

    def soft_delete_by_manuscript(self, manuscript_id: UUID) -> None:
        now = datetime.now(UTC)
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
