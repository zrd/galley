from uuid import UUID

from pydantic import BaseModel


class TagRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    name: str
    slug: str
