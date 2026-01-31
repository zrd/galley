from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class Author:
    email: str
    display_name: str
    password_hash: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def update_profile(self, display_name: str | None = None) -> None:
        if display_name is not None:
            self.display_name = display_name
