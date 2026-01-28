from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class DocumentCreate(BaseModel):
    owner_id: UUID
    title: str
    content: bytes


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[bytes] = None


class DocumentRead(BaseModel):
    document_id: UUID
    owner_id: UUID
    title: str
    content: bytes
    state: str
    created_at: datetime
    updated_at: datetime
