from app.repositories.in_memory import InMemoryDocumentRepository
from app.services.document_service import DocumentService

_repo = InMemoryDocumentRepository()

def get_document_service() -> DocumentService:
    return DocumentService(_repo)
