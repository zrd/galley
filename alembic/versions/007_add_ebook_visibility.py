"""add_ebook_visibility

Revision ID: 007
Revises: 006
Create Date: 2026-04-03 15:19:29.506623

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '007'
down_revision: Union[str, Sequence[str], None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    ebook_visibility_enum = postgresql.ENUM(
        "private", "unlisted", "published", name="ebook_visibility", create_type=False
    )
    ebook_visibility_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "ebooks", sa.Column(
            "visibility", ebook_visibility_enum, nullable=False, server_default="private"
        )
    )
    op.add_column("ebooks", sa.Column("unlisted_download_limit", sa.Integer, nullable=True))
    op.add_column("ebooks", sa.Column("published_at", sa.DateTime(timezone=True)))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("ebooks", "published_at")
    op.drop_column("ebooks", "unlisted_download_limit")
    op.drop_column("ebooks", "visibility")
    op.execute("DROP TYPE IF EXISTS ebook_visibility")
