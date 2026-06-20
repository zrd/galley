"""Add author public profile fields (STORE-007)

Revision ID: 009
Revises: 008
Create Date: 2026-06-18 19:56:00.245422

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '009'
down_revision: Union[str, Sequence[str], None] = '008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("authors", sa.Column("bio", sa.Text(), nullable=True))
    op.add_column("authors", sa.Column("website", sa.String(1024), nullable=True))
    op.add_column("authors", sa.Column("avatar_key", sa.String(1024), nullable=True))
    op.add_column(
        "authors", sa.Column("is_public", sa.Boolean(), nullable=False, server_default="false")
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("authors", "is_public")
    op.drop_column("authors", "avatar_key")
    op.drop_column("authors", "website")
    op.drop_column("authors", "bio")
