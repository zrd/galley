from slugify import slugify

from app.domain import Genre, GenreNotFound
from app.repositories import GenreRepository
from app.schemas.genre import GenreTree


class GenreService:
    def __init__(self, repo: GenreRepository) -> None:
        self.repo = repo

    def create(
        self,
        name: str,
        description: str | None = None,
        parent_id: int | None = None
    ) -> Genre:
        genre = Genre(
            id=None,
            name=name,
            slug=slugify(name),
            description=description,
            parent_id=parent_id,
        )
        return self.repo.add(genre)

    def get(self, genre_id: int) -> Genre:
        genre = self.repo.get(genre_id=genre_id)
        if genre is None:
            raise GenreNotFound(f"Genre {genre_id} not found")
        return genre

    def list_all(self) -> list[Genre]:
        return self.repo.list_all()

    def list_by_parent(self, parent_id: int) -> list[Genre]:
        return self.repo.list_by_parent(parent_id=parent_id)

    def list_top_level(self) -> list[Genre]:
        return self.repo.list_top_level()

    def get_tree(self) -> list[GenreTree]:
        genres = self.repo.list_all()
        nodes = {g.id: GenreTree(id=g.id, name=g.name, slug=g.slug, description=g.description) for g in genres}
        roots = []
        for g in genres:
            if g.parent_id is None:
                roots.append(nodes[g.id])
            else:
                nodes[g.parent_id].children.append(nodes[g.id])
        return roots
