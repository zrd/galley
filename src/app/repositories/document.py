from typing import Protocol
from uuid import UUID

from app.domain.document import Document


class DocumentRepository(Protocol):
    def get(self, document_id: UUID) -> Document: ...
    def save(self, doc: Document) -> None: ...
    def delete(self, document_id: UUID) -> None: ...
