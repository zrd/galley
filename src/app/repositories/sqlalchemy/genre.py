from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import GenreModel
from app.domain import Genre

from ._mappers import genre_model_to_domain


class GenreRepository:
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
        return genre_model_to_domain(model)

    def get(self, genre_id: int) -> Genre | None:
        model = self.session.get(GenreModel, genre_id)
        if model is None:
            return None
        return genre_model_to_domain(model)

    def list_all(self) -> list[Genre]:
        stmt = select(GenreModel)
        models = self.session.scalars(stmt).all()
        return [genre_model_to_domain(m) for m in models]

    def list_by_parent(self, parent_id: int) -> list[Genre]:
        stmt = select(GenreModel).where(GenreModel.parent_id == parent_id)
        models = self.session.scalars(stmt).all()
        return [genre_model_to_domain(m) for m in models]

    def list_top_level(self) -> list[Genre]:
        stmt = select(GenreModel).where(GenreModel.parent_id.is_(None))
        models = self.session.scalars(stmt).all()
        return [genre_model_to_domain(m) for m in models]
