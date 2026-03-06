from pydantic import BaseModel, Field


class GenreCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    parent_id: int | None = None


class GenreRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    slug: str
    description: str | None
    parent_id: int | None


class GenreListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    slug: str
    parent_id: int | None


class GenreTree(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    slug: str
    description: str | None
    children: list["GenreTree"] = []
