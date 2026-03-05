"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-01-28

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create enums
    source_format_enum = postgresql.ENUM(
        "epub", "pdf", "docx", "odt", name="source_format", create_type=False
    )
    source_format_enum.create(op.get_bind(), checkfirst=True)

    manuscript_state_enum = postgresql.ENUM(
        "draft", "ready", "archived", name="manuscript_state", create_type=False
    )
    manuscript_state_enum.create(op.get_bind(), checkfirst=True)

    output_format_enum = postgresql.ENUM(
        "epub", "pdf", name="output_format", create_type=False
    )
    output_format_enum.create(op.get_bind(), checkfirst=True)

    # Create authors table
    op.create_table(
        "authors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_authors_email", "authors", ["email"])

    # Create manuscripts table
    op.create_table(
        "manuscripts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "author_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("authors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "source_format",
            source_format_enum,
            nullable=False,
        ),
        sa.Column("source_file_key", sa.String(512), nullable=False),
        sa.Column(
            "state",
            manuscript_state_enum,
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_manuscripts_author", "manuscripts", ["author_id"])

    # Create samples table
    op.create_table(
        "samples",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "manuscript_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("manuscripts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("excerpt_start", sa.String(255), nullable=False),
        sa.Column("excerpt_end", sa.String(255), nullable=False),
        sa.Column("promo_header", sa.Text, nullable=True),
        sa.Column("promo_footer", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_samples_manuscript", "samples", ["manuscript_id"])

    # Create ebooks table
    op.create_table(
        "ebooks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "manuscript_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("manuscripts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "sample_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("samples.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "output_format",
            output_format_enum,
            nullable=False,
        ),
        sa.Column("file_key", sa.String(512), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger, nullable=False),
        sa.Column("download_count", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_ebooks_manuscript", "ebooks", ["manuscript_id"])
    op.create_index("idx_ebooks_sample", "ebooks", ["sample_id"])

    # Create downloads table
    op.create_table(
        "downloads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "ebook_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ebooks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "downloaded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("ip_hash", sa.String(64), nullable=True),
        sa.Column("tracking_code", sa.String(100), nullable=True),
    )
    op.create_index("idx_downloads_ebook", "downloads", ["ebook_id"])
    op.create_index("idx_downloads_tracking", "downloads", ["tracking_code"])


def downgrade() -> None:
    op.drop_table("downloads")
    op.drop_table("ebooks")
    op.drop_table("samples")
    op.drop_table("manuscripts")
    op.drop_table("authors")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS output_format")
    op.execute("DROP TYPE IF EXISTS manuscript_state")
    op.execute("DROP TYPE IF EXISTS source_format")
