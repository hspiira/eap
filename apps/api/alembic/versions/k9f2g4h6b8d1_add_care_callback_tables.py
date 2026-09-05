"""Add care_callback_campaigns + outreach_records (Phase 3 #D-CareCallback)

Revision ID: k9f2g4h6b8d1
Revises: j8e1f3a5c7d9
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op



revision: str = "k9f2g4h6b8d1"
down_revision: Union[str, Sequence[str], None] = "j8e1f3a5c7d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "care_callback_campaigns",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("client_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False, index=True),
        sa.Column("period_end", sa.Date(), nullable=False, index=True),
        sa.Column("target_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "counsellor_pool",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="Draft", index=True),
        sa.Column("sampling_notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=25), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True, index=True),
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

    op.create_table(
        "outreach_records",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column(
            "campaign_id",
            sa.String(length=25),
            sa.ForeignKey("care_callback_campaigns.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("person_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("counsellor_id", sa.String(length=25), nullable=True, index=True),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="Pending",
            index=True,
        ),
        sa.Column("contact_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("triage_instrument_code", sa.String(length=100), nullable=True),
        sa.Column("triage_responses", sa.JSON(), nullable=True),
        sa.Column("triage_scores", sa.JSON(), nullable=True),
        sa.Column(
            "triage_risk_level", sa.String(length=20), nullable=True, index=True
        ),
        sa.Column(
            "crisis_flag",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("notes", sa.Text(), nullable=True),
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
    op.drop_table("outreach_records")
    op.drop_table("care_callback_campaigns")
