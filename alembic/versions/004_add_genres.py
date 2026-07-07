"""
Add genres table and manuscript_genres join table, and seed top-level genres.

Revision ID: 004
Revises: 003
Create Date: 2026-03-05
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "genres",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("slug", sa.String(64), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["parent_id"], ["genres.id"]),
    )

    op.create_table(
        "manuscript_genres",
        sa.Column("manuscript_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("genre_id", sa.Integer(), primary_key=True),
        sa.ForeignKeyConstraint(["manuscript_id"], ["manuscripts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["genre_id"], ["genres.id"], ondelete="CASCADE"),
    )

    op.execute("""
        INSERT INTO genres (name, slug, description, parent_id) VALUES 
            ('Fiction', 'fiction', 'Prose works including literary and genre fiction', NULL),
            ('Non-Fiction', 'non-fiction', 'Factual narrative works', NULL),
            ('Poetry', 'poetry', 'Poetic works', NULL),
            ('Drama', 'drama', 'Dramatic works including plays for stage and screen', NULL),
            ('Children''s', 'childrens', 'Works intended for young audiences such as pre-readers and early readers', NULL)
    """)


def downgrade() -> None:
    op.drop_table("manuscript_genres")
    op.drop_table("genres")
