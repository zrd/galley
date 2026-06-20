from uuid import UUID

from app.domain import Author, AuthorNotFound
from app.repositories.protocols import AuthorRepository
from app.schemas import AuthorUpdate


class AuthorService:
    def __init__(self, repo: AuthorRepository) -> None:
        self.repo = repo

    def create(self, email: str, password_hash: str, display_name: str) -> Author:
        author = Author(
            email=email,
            password_hash=password_hash,
            display_name=display_name,
        )
        return self.repo.add(author)

    def get(self, author_id: UUID, *, include_deleted: bool = False) -> Author:
        author = self.repo.get(author_id, include_deleted=include_deleted)
        if author is None:
            raise AuthorNotFound(f"Author {author_id} not found")
        return author

    def get_by_email(self, email: str, *, include_deleted: bool = False) -> Author | None:
        return self.repo.get_by_email(email, include_deleted=include_deleted)

    def update(self, author: Author, update_in: AuthorUpdate) -> Author:
        if "display_name" in update_in.model_fields_set:
            author.display_name = update_in.display_name

        if "bio" in update_in.model_fields_set:
            author.bio = update_in.bio

        if "website" in update_in.model_fields_set:
            author.website = update_in.website

        if "is_public" in update_in.model_fields_set:
            author.is_public = update_in.is_public

        return self.repo.update(author)

    def delete(self, author_id: UUID) -> None:
        self.repo.delete(author_id)

    def soft_delete(self, author_id: UUID) -> None:
        # Verify author exists before soft delete
        self.get(author_id)
        self.repo.soft_delete(author_id)

    def restore(self, author_id: UUID) -> None:
        # Get including deleted to verify it exists
        self.get(author_id, include_deleted=True)
        self.repo.restore(author_id)
