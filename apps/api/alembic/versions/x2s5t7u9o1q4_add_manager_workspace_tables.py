"""Add manager_consults + work_life_providers + work_life_referrals + training_enrolments

Revision ID: x2s5t7u9o1q4
Revises: w1r4s6t8n0p3
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op



revision: str = "x2s5t7u9o1q4"
down_revision: Union[str, Sequence[str], None] = "w1r4s6t8n0p3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "manager_consults",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("manager_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("consultant_id", sa.String(length=25), nullable=False),
        sa.Column("topic", sa.String(length=30), nullable=False, index=True),
        sa.Column("consulted_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("client_id", sa.String(length=25), nullable=True, index=True),
        sa.Column(
            "triggered_referral_case_id",
            sa.String(length=25),
            nullable=True,
            index=True,
        ),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "work_life_providers",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "service_types",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("contact_name", sa.String(length=255), nullable=True),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("contact_phone", sa.String(length=50), nullable=True),
        sa.Column("coverage_notes", sa.Text(), nullable=True),
        sa.Column("rate_card_notes", sa.Text(), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "work_life_referrals",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column(
            "clinical_subject_id",
            sa.String(length=25),
            nullable=False,
            index=True,
        ),
        sa.Column("service_type", sa.String(length=30), nullable=False, index=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column(
            "outcome",
            sa.String(length=20),
            nullable=False,
            server_default="Requested",
            index=True,
        ),
        sa.Column(
            "referred_provider_id",
            sa.String(length=25),
            nullable=True,
            index=True,
        ),
        sa.Column("case_id", sa.String(length=25), nullable=True, index=True),
        sa.Column("requested_by", sa.String(length=25), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "training_enrolments",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("trainee_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("document_id", sa.String(length=25), nullable=False, index=True),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="Enrolled",
            index=True,
        ),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_on", sa.Date(), nullable=True, index=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("training_enrolments")
    op.drop_table("work_life_referrals")
    op.drop_table("work_life_providers")
    op.drop_table("manager_consults")
