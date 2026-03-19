"""add_ebook_pricing

Revision ID: 005
Revises: 004
Create Date: 2026-03-12 18:07:25.056091

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, Sequence[str], None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("ebooks", sa.Column("list_price_cents", sa.Integer, nullable=True))
    op.add_column("ebooks", sa.Column("sale_price_cents", sa.Integer, nullable=True))
    op.add_column("ebooks", sa.Column("price_currency", sa.String(64), nullable=False, server_default="USD"))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("ebooks", "list_price_cents")
    op.drop_column("ebooks", "sale_price_cents")
    op.drop_column("ebooks", "price_currency")
