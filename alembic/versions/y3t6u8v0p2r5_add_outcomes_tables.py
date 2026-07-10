"""Add outcome_measures + fitness_for_duty + return_to_work_plans

Revision ID: y3t6u8v0p2r5
Revises: x2s5t7u9o1q4
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op



revision: str = "y3t6u8v0p2r5"
down_revision: Union[str, Sequence[str], None] = "x2s5t7u9o1q4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "outcome_measures",
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
        sa.Column("instrument_code", sa.String(length=20), nullable=False, index=True),
        sa.Column("intake_response_id", sa.String(length=25), nullable=False),
        sa.Column("closure_response_id", sa.String(length=25), nullable=False),
        sa.Column("pre_score", sa.Float(), nullable=False),
        sa.Column("post_score", sa.Float(), nullable=False),
        sa.Column("delta", sa.Float(), nullable=False),
        sa.Column("reliable_change_index", sa.Float(), nullable=False),
        sa.Column(
            "meets_clinically_significant_change",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "fitness_for_duty",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column(
            "clinical_subject_id",
            sa.String(length=25),
            nullable=False,
            index=True,
        ),
        sa.Column("client_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("case_id", sa.String(length=25), nullable=True, index=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("requested_by", sa.String(length=25), nullable=False),
        sa.Column("business_necessity_rationale", sa.Text(), nullable=False),
        sa.Column("job_role_summary", sa.Text(), nullable=False),
        sa.Column(
            "outcome",
            sa.String(length=30),
            nullable=False,
            server_default="Pending",
            index=True,
        ),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assessor_id", sa.String(length=25), nullable=True),
        sa.Column(
            "accommodation_recommendations",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("employer_report_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "return_to_work_plans",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column(
            "clinical_subject_id",
            sa.String(length=25),
            nullable=False,
            index=True,
        ),
        sa.Column("client_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("case_id", sa.String(length=25), nullable=True, index=True),
        sa.Column(
            "fitness_for_duty_id",
            sa.String(length=25),
            nullable=True,
            index=True,
        ),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="Draft",
            index=True,
        ),
        sa.Column(
            "accommodations",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "employer_signoff_user_id", sa.String(length=25), nullable=True
        ),
        sa.Column(
            "clinician_signoff_user_id", sa.String(length=25), nullable=True
        ),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("review_at", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("return_to_work_plans")
    op.drop_table("fitness_for_duty")
    op.drop_table("outcome_measures")
