"""Add consents + data_sharing_register + dpo_contacts

Revision ID: z4u7v9w1q3s6
Revises: y3t6u8v0p2r5
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "z4u7v9w1q3s6"
down_revision: Union[str, Sequence[str], None] = "y3t6u8v0p2r5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "consents",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column(
            "subject_clinical_subject_id",
            sa.String(length=25),
            nullable=False,
            index=True,
        ),
        sa.Column("case_id", sa.String(length=25), nullable=True, index=True),
        sa.Column("scope", sa.String(length=30), nullable=False, index=True),
        sa.Column("purpose", sa.String(length=40), nullable=False, index=True),
        sa.Column("purpose_other_detail", sa.Text(), nullable=True),
        sa.Column("disclosure_to", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="Pending",
            index=True,
        ),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("requested_by", sa.String(length=25), nullable=False),
        sa.Column("expires_on", sa.Date(), nullable=True, index=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "granted_by_subject_reference", sa.String(length=255), nullable=True
        ),
        sa.Column(
            "signed_artifact_document_id",
            sa.String(length=25),
            nullable=True,
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "data_sharing_register",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column(
            "subject_clinical_subject_id",
            sa.String(length=25),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "consent_id",
            sa.String(length=25),
            sa.ForeignKey("consents.id", ondelete="RESTRICT"),
            nullable=True,
            index=True,
        ),
        sa.Column("case_id", sa.String(length=25), nullable=True, index=True),
        sa.Column("shared_with", sa.String(length=255), nullable=False),
        sa.Column("scope", sa.String(length=30), nullable=False),
        sa.Column("summary_of_data_shared", sa.Text(), nullable=False),
        sa.Column("legal_basis", sa.Text(), nullable=True),
        sa.Column("shared_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("shared_by", sa.String(length=25), nullable=False),
        sa.Column("delivery_channel", sa.String(length=50), nullable=True),
        sa.Column("delivery_reference", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "dpo_contacts",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("role_title", sa.String(length=255), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_until", sa.Date(), nullable=True, index=True),
        sa.Column("appointed_by", sa.String(length=25), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("dpo_contacts")
    op.drop_table("data_sharing_register")
    op.drop_table("consents")
