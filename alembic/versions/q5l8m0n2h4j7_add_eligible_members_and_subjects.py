"""Add eligible_members + clinical_subjects + audited link

Revision ID: q5l8m0n2h4j7
Revises: p4k7l9m1g3i6
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "q5l8m0n2h4j7"
down_revision: Union[str, Sequence[str], None] = "p4k7l9m1g3i6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "eligible_members",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("client_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("employer_member_id", sa.String(length=255), nullable=False),
        sa.Column("relation", sa.String(length=20), nullable=False, index=True),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="Pending",
            index=True,
        ),
        sa.Column(
            "primary_employee_member_id",
            sa.String(length=25),
            nullable=True,
            index=True,
        ),
        sa.Column("coverage_start", sa.Date(), nullable=True),
        sa.Column("coverage_end", sa.Date(), nullable=True),
        sa.Column("work_email", sa.String(length=255), nullable=True),
        sa.Column("personal_email", sa.String(length=255), nullable=True),
        sa.Column("display_label", sa.String(length=255), nullable=True),
        sa.Column("last_imported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("terminated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=25), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "tenant_id",
            "client_id",
            "employer_member_id",
            name="uq_eligible_member_employer_id_per_client",
        ),
    )

    op.create_table(
        "clinical_subjects",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("pseudonym", sa.String(length=64), nullable=False, index=True),
        sa.Column("preferred_language", sa.String(length=20), nullable=True),
        sa.Column("preferred_pronouns", sa.String(length=50), nullable=True),
        sa.Column("preferred_contact_method", sa.String(length=20), nullable=True),
        sa.Column("notes_for_continuity", sa.Text(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "tenant_id",
            "pseudonym",
            name="uq_clinical_subject_pseudonym_per_tenant",
        ),
    )

    op.create_table(
        "eligible_member_clinical_link",
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column(
            "member_id",
            sa.String(length=25),
            sa.ForeignKey("eligible_members.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "subject_id",
            sa.String(length=25),
            sa.ForeignKey("clinical_subjects.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "tenant_id", "member_id", name="uq_link_member_per_tenant"
        ),
        sa.UniqueConstraint(
            "tenant_id", "subject_id", name="uq_link_subject_per_tenant"
        ),
    )


def downgrade() -> None:
    op.drop_table("eligible_member_clinical_link")
    op.drop_table("clinical_subjects")
    op.drop_table("eligible_members")
