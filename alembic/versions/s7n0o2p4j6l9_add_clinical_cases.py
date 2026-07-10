"""Add clinical cases

Revision ID: s7n0o2p4j6l9
Revises: r6m9n1o3i5k8
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "s7n0o2p4j6l9"
down_revision: Union[str, Sequence[str], None] = "r6m9n1o3i5k8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cases",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column(
            "clinical_subject_id",
            sa.String(length=25),
            nullable=False,
            index=True,
        ),
        sa.Column("client_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("presenting_problem", sa.String(length=30), nullable=False, index=True),
        sa.Column("referral_source", sa.String(length=30), nullable=False, index=True),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="Intake",
            index=True,
        ),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column(
            "assigned_counsellor_id",
            sa.String(length=25),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "authorization_id", sa.String(length=25), nullable=True, index=True
        ),
        sa.Column("referred_by_user_id", sa.String(length=25), nullable=True),
        sa.Column("referral_notes", sa.Text(), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closure_reason", sa.String(length=30), nullable=True),
        sa.Column("closure_summary_note_id", sa.String(length=25), nullable=True),
        sa.Column(
            "intake_screener_admin_ids",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "closure_screener_admin_ids",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("cases")
