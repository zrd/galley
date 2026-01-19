from uuid import UUID
from datetime import datetime

from .exceptions import InvalidStateTransition


class Document:
    def __init__(
        self,
        document_id: UUID,
        owner_id: UUID,
        title: str,
        content: bytes,
        state: str = "draft",
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self.document_id = document_id
        self.owner_id = owner_id
        self.title = title
        self.content = content
        self.state = state
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def publish(self) -> None:
        if self.state != "draft":
            raise InvalidStateTransition(
                f"Cannot publish document in state '{self.state}'"
            )
        self.state = "published"

    def update_content(self, title: str, content: str) -> None:
        if self.state == "published":
            raise InvalidStateTransition("Cannot edit a published document")
        self.title = title
        self.content = content
        self.updated_at = datetime.utcnow()
