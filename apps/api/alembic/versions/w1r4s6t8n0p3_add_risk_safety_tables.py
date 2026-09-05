"""Add risk_assessments + safety_plans + mandatory_reports + caring_contacts

Revision ID: w1r4s6t8n0p3
Revises: v0q3r5s7m9o2
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op



revision: str = "w1r4s6t8n0p3"
down_revision: Union[str, Sequence[str], None] = "v0q3r5s7m9o2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "risk_assessments",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column(
            "clinical_subject_id",
            sa.String(length=25),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "case_id",
            sa.String(length=25),
            sa.ForeignKey("cases.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "crisis_contact_id",
            sa.String(length=25),
            sa.ForeignKey("crisis_contacts.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("assessor_id", sa.String(length=25), nullable=False),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("risk_level", sa.String(length=20), nullable=False, index=True),
        sa.Column(
            "imminent_harm_to_self",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "imminent_harm_to_others",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "child_safety_concern",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "vulnerable_adult_concern",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "requires_safety_plan",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "requires_mandatory_report",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            index=True,
        ),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column(
            "questionnaire_response_ids",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "safety_plans",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column(
            "clinical_subject_id",
            sa.String(length=25),
            nullable=False,
            index=True,
        ),
        sa.Column("case_id", sa.String(length=25), nullable=True, index=True),
        sa.Column(
            "crisis_contact_id", sa.String(length=25), nullable=True, index=True
        ),
        sa.Column("clinician_id", sa.String(length=25), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="Draft",
            index=True,
        ),
        sa.Column(
            "warning_signs",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "internal_coping_strategies",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "social_distractions",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "social_contacts_for_help",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "professional_help_resources",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "means_restriction_plan",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_review_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", sa.String(length=25), nullable=True),
        sa.Column(
            "supersedes_safety_plan_id", sa.String(length=25), nullable=True
        ),
        sa.Column("superseded_by", sa.String(length=25), nullable=True),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "mandatory_reports",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column(
            "clinical_subject_id",
            sa.String(length=25),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "risk_assessment_id",
            sa.String(length=25),
            sa.ForeignKey("risk_assessments.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("case_id", sa.String(length=25), nullable=True, index=True),
        sa.Column(
            "crisis_contact_id", sa.String(length=25), nullable=True, index=True
        ),
        sa.Column("report_type", sa.String(length=30), nullable=False, index=True),
        sa.Column("submitted_to", sa.String(length=255), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("submitted_by", sa.String(length=25), nullable=False),
        sa.Column(
            "external_reference_number", sa.String(length=255), nullable=True
        ),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("contact_phone", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "caring_contacts",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column(
            "clinical_subject_id",
            sa.String(length=25),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "crisis_contact_id",
            sa.String(length=25),
            sa.ForeignKey("crisis_contacts.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("case_id", sa.String(length=25), nullable=True, index=True),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column(
            "outcome",
            sa.String(length=20),
            nullable=False,
            server_default="Pending",
            index=True,
        ),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("handled_by", sa.String(length=25), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("caring_contacts")
    op.drop_table("mandatory_reports")
    op.drop_table("safety_plans")
    op.drop_table("risk_assessments")
