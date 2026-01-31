from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class AuthorCreate(BaseModel):
    email: EmailStr
    password: str
    display_name: str


class AuthorUpdate(BaseModel):
    display_name: str | None = None


class AuthorRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    email: str
    display_name: str
    created_at: datetime
