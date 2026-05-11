"""Add crisis_contacts

Revision ID: v0q3r5s7m9o2
Revises: u9p2q4r6l8n1
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "v0q3r5s7m9o2"
down_revision: Union[str, Sequence[str], None] = "u9p2q4r6l8n1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "crisis_contacts",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("contacted_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("caller_relation", sa.String(length=20), nullable=False, index=True),
        sa.Column("presenting_concern", sa.Text(), nullable=False),
        sa.Column("clinical_subject_id", sa.String(length=25), nullable=True, index=True),
        sa.Column(
            "case_id",
            sa.String(length=25),
            sa.ForeignKey("cases.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("counsellor_id", sa.String(length=25), nullable=True, index=True),
        sa.Column(
            "cssrs_administered",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("risk_assessment_id", sa.String(length=25), nullable=True),
        sa.Column("safety_plan_id", sa.String(length=25), nullable=True),
        sa.Column("risk_level", sa.String(length=20), nullable=True, index=True),
        sa.Column(
            "warm_handoff",
            sa.String(length=30),
            nullable=False,
            server_default="None",
            index=True,
        ),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outcome", sa.String(length=30), nullable=True, index=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("transcript_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("crisis_contacts")
