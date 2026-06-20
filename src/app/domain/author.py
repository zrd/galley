from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class Author:
    email: str
    display_name: str
    password_hash: str
    id: UUID = field(default_factory=uuid4)
    bio: str | None = None
    website: str | None = None
    avatar_key: str | None = None
    is_public: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        self.deleted_at = None
