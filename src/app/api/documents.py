from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from typing import List

from app.services.document_service import DocumentService
from app.repositories.in_memory import InMemoryDocumentRepository
from app.schemas.document import DocumentCreate, DocumentRead, DocumentUpdate
from app.security.auth import require_api_key, get_current_user_id


router = APIRouter()
repo = InMemoryDocumentRepository()
service = DocumentService(repo)


@router.post("/", response_model=DocumentRead, dependencies=[Depends(get_current_user_id)])
def create_document(doc_in: DocumentCreate, owner_id: UUID = Depends(get_current_user_id)):
    doc = service.create(title=doc_in.title, content=doc_in.content, owner_id=owner_id)
    return DocumentRead(
        document_id=doc.document_id,
        owner_id=doc.owner_id,
        title=doc.title,
        content=doc.content,
        state=doc.state,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.patch("/", response_model=DocumentRead, dependencies=[Depends(get_current_user_id)])
def update_document(doc_in: DocumentUpdate, owner_id: UUID = Depends(get_current_user_id)):
    doc = service.update(doc_in)
    return DocumentRead(
        document_id=doc.document_id,
        owner_id=doc.owner_id,
        title=doc.title,
        content=doc.content,
        state=doc.state,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.get("/", response_model=List[DocumentRead], dependencies=[Depends(get_current_user_id)])
def list_documents(owner_id: UUID = Depends(get_current_user_id)):
    docs = service.list(owner_id)
    return [
        DocumentRead(
            document_id=d.document_id,
            owner_id=d.owner_id,
            title=d.title,
            content=d.content,
            state=d.state,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )
        for d in docs
    ]

@router.get("/{document_id}", response_model=DocumentRead, dependencies=[Depends(get_current_user_id)])
def get_document(document_id: UUID, owner_id: UUID = Depends(get_current_user_id)):
    doc = service.get(document_id)
    if not doc or doc.owner_id != owner_id:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentRead(
        document_id=doc.document_id,
        owner_id=doc.owner_id,
        title=doc.title,
        content=doc.content,
        state=doc.state,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )

@router.delete("/{document_id}", dependencies=[Depends(get_current_user_id)])
def delete_document(document_id: UUID, owner_id: UUID = Depends(get_current_user_id)):
    doc = service.get(document_id)
    if not doc or doc.owner_id != owner_id:
        raise HTTPException(status_code=404, detail="Document not found")
    service.delete(document_id)
    return {"detail": "Document deleted"}
