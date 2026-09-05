"""Add clinical_notes

Revision ID: u9p2q4r6l8n1
Revises: t8o1p3q5k7m0
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op



revision: str = "u9p2q4r6l8n1"
down_revision: Union[str, Sequence[str], None] = "t8o1p3q5k7m0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "clinical_notes",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column(
            "case_id",
            sa.String(length=25),
            sa.ForeignKey("cases.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "clinical_subject_id",
            sa.String(length=25),
            nullable=False,
            index=True,
        ),
        sa.Column("note_type", sa.String(length=20), nullable=False, index=True),
        sa.Column("body", sa.JSON(), nullable=False),
        sa.Column("author_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("session_id", sa.String(length=25), nullable=True, index=True),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signed_by", sa.String(length=25), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "lock_window_seconds",
            sa.Integer(),
            nullable=False,
            server_default=str(7 * 24 * 60 * 60),
        ),
        sa.Column(
            "amendments",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("clinical_notes")
