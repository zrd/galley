from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class Download:
    """
    A record of an ebook download for tracking purposes.

    ip_hash is a privacy-preserving hash of the downloader's IP.
    tracking_code is an optional identifier from QR codes or short links
    that enables per-event or per-contact tracking (Phase 2 feature).
    """

    ebook_id: UUID
    id: UUID = field(default_factory=uuid4)
    downloaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ip_hash: str | None = None
    tracking_code: str | None = None
