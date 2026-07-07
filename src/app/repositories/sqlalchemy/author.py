from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AuthorModel
from app.domain import Author

from ._mappers import author_model_to_domain


class AuthorRepository:
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
        return author_model_to_domain(model)

    def get(self, author_id: UUID, *, include_deleted: bool = False) -> Author | None:
        model = self.session.get(AuthorModel, author_id)
        if model is None:
            return None
        if not include_deleted and model.deleted_at is not None:
            return None
        return author_model_to_domain(model)

    def get_by_email(self, email: str, *, include_deleted: bool = False) -> Author | None:
        stmt = select(AuthorModel).where(AuthorModel.email == email)
        if not include_deleted:
            stmt = stmt.where(AuthorModel.deleted_at.is_(None))

        model = self.session.scalars(stmt).first()
        return author_model_to_domain(model) if model else None

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
            return author_model_to_domain(model)
        raise ValueError(f"Author {author.id} not found")

    def delete(self, author_id: UUID) -> None:
        model = self.session.get(AuthorModel, author_id)
        if model:
            self.session.delete(model)
            self.session.flush()

    def soft_delete(self, author_id: UUID) -> None:
        model = self.session.get(AuthorModel, author_id)
        if model:
            model.deleted_at = datetime.now(UTC)
            self.session.flush()

    def restore(self, author_id: UUID) -> None:
        model = self.session.get(AuthorModel, author_id)
        if model:
            model.deleted_at = None
            self.session.flush()
