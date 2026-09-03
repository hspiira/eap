"""Add eap_programmes + authorizations

Revision ID: t8o1p3q5k7m0
Revises: s7n0o2p4j6l9
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op



revision: str = "t8o1p3q5k7m0"
down_revision: Union[str, Sequence[str], None] = "s7n0o2p4j6l9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "eap_programmes",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("contract_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_until", sa.Date(), nullable=True),
        sa.Column("geographic_scope", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("caps", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column(
            "eligible_dependent_relations",
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
        sa.Column("created_by", sa.String(length=25), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "authorizations",
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
        sa.Column(
            "programme_id",
            sa.String(length=25),
            sa.ForeignKey("eap_programmes.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("service_category", sa.String(length=30), nullable=False, index=True),
        sa.Column("sessions_granted", sa.Integer(), nullable=False),
        sa.Column(
            "sessions_used", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default="Active",
            index=True,
        ),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_on", sa.Date(), nullable=True),
        sa.Column("extension_requested_sessions", sa.Integer(), nullable=True),
        sa.Column("extension_requested_by", sa.String(length=25), nullable=True),
        sa.Column(
            "extension_requested_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "extension_clinician_signoff", sa.String(length=25), nullable=True
        ),
        sa.Column(
            "extension_admin_signoff", sa.String(length=25), nullable=True
        ),
        sa.Column("extended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("authorizations")
    op.drop_table("eap_programmes")
