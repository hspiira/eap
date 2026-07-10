"""Add provider_profile JSON + non_compete_clauses (Phase 2 #D-Provider)

Revision ID: h6c8d2e4f7a9
Revises: g5b7c9d2e4f6
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "h6c8d2e4f7a9"
down_revision: Union[str, Sequence[str], None] = "g5b7c9d2e4f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "persons",
        sa.Column("provider_profile", sa.JSON(), nullable=True),
    )

    op.create_table(
        "non_compete_clauses",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("provider_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="Draft", index=True),
        sa.Column("terms_summary", sa.Text(), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_until", sa.Date(), nullable=True),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signed_by", sa.String(length=25), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.Text(), nullable=True),
        sa.Column("document_id", sa.String(length=25), nullable=True),
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


def downgrade() -> None:
    op.drop_table("non_compete_clauses")
    op.drop_column("persons", "provider_profile")
