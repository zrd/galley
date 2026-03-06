from dataclasses import dataclass


@dataclass
class Genre:
    id: int | None
    name: str
    slug: str
    description: str | None
    parent_id: int | None
