from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import DownloadModel
from app.domain import Download

from ._mappers import download_model_to_domain


class DownloadRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, download: Download) -> Download:
        model = DownloadModel(
            id=download.id,
            ebook_id=download.ebook_id,
            downloaded_at=download.downloaded_at,
            ip_hash=download.ip_hash,
            tracking_code=download.tracking_code,
            deleted_at=download.deleted_at,
        )
        self.session.add(model)
        self.session.flush()
        return download_model_to_domain(model)

    def get(self, download_id: UUID, *, include_deleted: bool = False) -> Download | None:
        model = self.session.get(DownloadModel, download_id)
        if model is None:
            return None
        if not include_deleted and model.deleted_at is not None:
            return None
        return download_model_to_domain(model)

    def list_by_ebook(self, ebook_id: UUID, *, include_deleted: bool = False) -> list[Download]:
        stmt = select(DownloadModel).where(DownloadModel.ebook_id == ebook_id)
        if not include_deleted:
            stmt = stmt.where(DownloadModel.deleted_at.is_(None))

        stmt = stmt.order_by(DownloadModel.downloaded_at.desc())
        models = self.session.scalars(stmt).all()
        return [download_model_to_domain(m) for m in models]

    def count_by_ebook(self, ebook_id: UUID, *, include_deleted: bool = False) -> int:
        stmt = select(func.count(DownloadModel.id)).where(DownloadModel.ebook_id == ebook_id)
        if not include_deleted:
            stmt = stmt.where(DownloadModel.deleted_at.is_(None))

        return self.session.scalar(stmt) or 0
