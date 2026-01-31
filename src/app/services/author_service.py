from uuid import UUID

from app.domain import Author, AuthorNotFound
from app.repositories import InMemoryAuthorRepository


class AuthorService:
    def __init__(self, repo: InMemoryAuthorRepository) -> None:
        self.repo = repo

    def create(self, email: str, password_hash: str, display_name: str) -> Author:
        author = Author(
            email=email,
            password_hash=password_hash,
            display_name=display_name,
        )
        return self.repo.add(author)

    def get(self, author_id: UUID) -> Author:
        author = self.repo.get(author_id)
        if author is None:
            raise AuthorNotFound(f"Author {author_id} not found")
        return author

    def get_by_email(self, email: str) -> Author | None:
        return self.repo.get_by_email(email)

    def update(self, author_id: UUID, display_name: str | None = None) -> Author:
        author = self.get(author_id)
        author.update_profile(display_name=display_name)
        return self.repo.update(author)

    def delete(self, author_id: UUID) -> None:
        self.repo.delete(author_id)
