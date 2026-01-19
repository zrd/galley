from datetime import datetime
from uuid import UUID
from app.domain.document import Document
from app.domain.exceptions import DocumentNotFound
from app.repositories.document import DocumentRepository


class InMemoryDocumentRepository(DocumentRepository):
    def __init__(self):
        self._store: dict[UUID, Document] = {}

    def add(self, doc: Document) -> Document:
        self._store[doc.document_id] = doc
        return doc

    def list(self, owner_id: UUID) -> list[Document]:
        return [d for d in self._store.values() if d.owner_id == owner_id]

    def get(self, document_id: UUID) -> Document:
        try:
            return self._store[document_id]
        except KeyError:
            raise DocumentNotFound(document_id)

    def update(self, doc: Document) -> Document:
        if doc.document_id not in self._store:
            raise KeyError("Document not found")
        doc.updated_at = datetime.utcnow()
        self._store[doc.document_id] = doc
        return doc

    def delete(self, document_id: UUID) -> None:
        if document_id not in self._store:
            raise DocumentNotFound(document_id)
        self._store.pop(document_id, None)
