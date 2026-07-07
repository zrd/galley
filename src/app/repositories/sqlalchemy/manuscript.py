from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import (
    ManuscriptGenreModel,
    ManuscriptModel,
    ManuscriptTagModel,
)
from app.domain import Manuscript

from ._mappers import manuscript_model_to_domain


class ManuscriptRepository:
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
        return manuscript_model_to_domain(model)

    def get(self, manuscript_id: UUID, *, include_deleted: bool = False) -> Manuscript | None:
        model = self.session.get(ManuscriptModel, manuscript_id)
        if model is None:
            return None
        if not include_deleted and model.deleted_at is not None:
            return None
        return manuscript_model_to_domain(model)

    def list_by_author(self, author_id: UUID, *, include_deleted: bool = False) -> list[Manuscript]:
        stmt = select(ManuscriptModel).where(ManuscriptModel.author_id == author_id)
        if not include_deleted:
            stmt = stmt.where(ManuscriptModel.deleted_at.is_(None))

        stmt = stmt.order_by(ManuscriptModel.updated_at.desc())
        models = self.session.scalars(stmt).all()
        return [manuscript_model_to_domain(m) for m in models]

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
            return manuscript_model_to_domain(model)
        raise ValueError(f"Manuscript {manuscript.id} not found")

    def delete(self, manuscript_id: UUID) -> None:
        model = self.session.get(ManuscriptModel, manuscript_id)
        if model:
            self.session.delete(model)
            self.session.flush()

    def soft_delete(self, manuscript_id: UUID) -> None:
        model = self.session.get(ManuscriptModel, manuscript_id)
        if model:
            model.deleted_at = datetime.now(UTC)
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
