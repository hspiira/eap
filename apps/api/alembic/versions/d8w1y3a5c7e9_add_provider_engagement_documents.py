"""Add the per-provider engagement-document checklist (P-02).

One row per (tenant, provider, document kind), holding a state of Present,
Missing or Open and an optional validity note. The composite foreign key to
providers (tenant_id, id) keeps every row inside its provider's tenant.

Revision ID: d8w1y3a5c7e9
Revises: c7v0x2z4b6d8
Create Date: 2026-09-07

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision = "d8w1y3a5c7e9"
down_revision: str | Sequence[str] | None = "c7v0x2z4b6d8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "provider_engagement_documents",
        sa.Column("id", sa.String(length=25), nullable=False),
        sa.Column("tenant_id", sa.String(length=25), nullable=False),
        sa.Column("provider_id", sa.String(length=25), nullable=False),
        sa.Column("document_kind", sa.String(length=40), nullable=False),
        sa.Column("state", sa.String(length=20), nullable=False),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "provider_id"],
            ["providers.tenant_id", "providers.id"],
            name="fk_provider_engagement_documents_provider_tenant",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "provider_id",
            "document_kind",
            name="uq_provider_engagement_documents_kind",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_provider_engagement_documents_tenant_id",
        "provider_engagement_documents",
        ["tenant_id"],
    )
    op.create_index(
        "ix_provider_engagement_documents_provider_id",
        "provider_engagement_documents",
        ["provider_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_provider_engagement_documents_provider_id", table_name="provider_engagement_documents"
    )
    op.drop_index(
        "ix_provider_engagement_documents_tenant_id", table_name="provider_engagement_documents"
    )
    op.drop_table("provider_engagement_documents")
