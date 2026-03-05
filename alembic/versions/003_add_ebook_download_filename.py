"""Add download_filename to ebooks table.

Revision ID: 003
Revises: 002
Create Date: 2026-02-18
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add download_filename column with a default for existing rows
    op.add_column(
        "ebooks",
        sa.Column("download_filename", sa.String(512), nullable=True),
    )

    # Set default value for existing ebooks (use file_key's filename portion)
    op.execute(
        """
        UPDATE ebooks
        SET download_filename = 'ebook.' ||
            CASE output_format
                WHEN 'epub' THEN 'epub'
                WHEN 'pdf' THEN 'pdf'
                ELSE 'bin'
            END
        WHERE download_filename IS NULL
        """
    )

    # Make column non-nullable
    op.alter_column("ebooks", "download_filename", nullable=False)


def downgrade() -> None:
    op.drop_column("ebooks", "download_filename")
