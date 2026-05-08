"""Add survey_campaigns + survey_responses (Phase 3 #D-Survey)

Revision ID: l0g3h5i7c9e2
Revises: k9f2g4h6b8d1
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "l0g3h5i7c9e2"
down_revision: Union[str, Sequence[str], None] = "k9f2g4h6b8d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "survey_campaigns",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("client_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False, index=True),
        sa.Column("external_form_id", sa.String(length=255), nullable=False),
        sa.Column("webhook_secret", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="Draft",
            index=True,
        ),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column(
            "anonymous", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "response_count", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("created_by", sa.String(length=25), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "survey_responses",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column(
            "campaign_id",
            sa.String(length=25),
            sa.ForeignKey("survey_campaigns.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("external_response_id", sa.String(length=255), nullable=False),
        sa.Column(
            "submitted_at", sa.DateTime(timezone=True), nullable=False, index=True
        ),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("metrics", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "campaign_id",
            "external_response_id",
            name="uq_survey_response_external_id_per_campaign",
        ),
    )


def downgrade() -> None:
    op.drop_table("survey_responses")
    op.drop_table("survey_campaigns")
