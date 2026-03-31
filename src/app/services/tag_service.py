from uuid import UUID

from slugify import slugify

from app.domain import Tag, TagNotFound
from app.repositories import TagRepository


class TagService:
    def __init__(self, repo: TagRepository) -> None:
        self.repo = repo

    def create(self, name: str, owner_id: UUID) -> Tag:
        return self.repo.get_or_create(name=name, owner_id=owner_id)

    def get(self, name: str, owner_id: UUID) -> Tag:
        slug = slugify(name)
        tag = self.repo.get_by_slug(slug=slug, owner_id=owner_id)
        if tag is None:
            raise TagNotFound(name)
        return tag

    def list_all(self, owner_id: UUID) -> list[Tag]:
        return self.repo.list_by_owner(owner_id)

    def get_by_slug(self, slug: str, owner_id: UUID):
        return self.repo.get_by_slug(slug=slug, owner_id=owner_id)
