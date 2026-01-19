from uuid import uuid4, UUID

from app.domain.document import Document
from app.repositories.in_memory import InMemoryDocumentRepository


class DocumentService:
    def __init__(self, repo: InMemoryDocumentRepository):
        self.repo = repo

    def create(self, title: str, content: bytes, owner_id: UUID) -> Document:
        doc = Document(document_id=uuid4(), title=title, owner_id=owner_id, content=content)
        return self.repo.add(doc)

    def get(self, document_id: UUID) -> Document | None:
        return self.repo.get(document_id)

    def list(self, owner_id: UUID) -> list[Document]:
        return self.repo.list(owner_id)

    def update(self, doc: Document) -> Document:
        return self.repo.update(doc)

    def delete(self, document_id: UUID):
        self.repo.delete(document_id)
