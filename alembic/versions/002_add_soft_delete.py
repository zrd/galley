"""Add soft delete columns

Revision ID: 002
Revises: 001
Create Date: 2026-02-04

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add deleted_at column to authors
    op.add_column(
        "authors",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_authors_deleted_at", "authors", ["deleted_at"])

    # Add deleted_at column to manuscripts
    op.add_column(
        "manuscripts",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_manuscripts_deleted_at", "manuscripts", ["deleted_at"])

    # Add deleted_at column to samples
    op.add_column(
        "samples",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_samples_deleted_at", "samples", ["deleted_at"])

    # Add deleted_at column to ebooks
    op.add_column(
        "ebooks",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ebooks_deleted_at", "ebooks", ["deleted_at"])

    # Add deleted_at column to downloads (no index needed - rarely queried)
    op.add_column(
        "downloads",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    # Remove deleted_at columns
    op.drop_column("downloads", "deleted_at")

    op.drop_index("ix_ebooks_deleted_at", table_name="ebooks")
    op.drop_column("ebooks", "deleted_at")

    op.drop_index("ix_samples_deleted_at", table_name="samples")
    op.drop_column("samples", "deleted_at")

    op.drop_index("ix_manuscripts_deleted_at", table_name="manuscripts")
    op.drop_column("manuscripts", "deleted_at")

    op.drop_index("ix_authors_deleted_at", table_name="authors")
    op.drop_column("authors", "deleted_at")
