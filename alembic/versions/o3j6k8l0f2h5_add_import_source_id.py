"""Add service_sessions.import_source_id (Phase 4 #D-Import)

Revision ID: o3j6k8l0f2h5
Revises: n2i5j7k9e1g4
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "o3j6k8l0f2h5"
down_revision: Union[str, Sequence[str], None] = "n2i5j7k9e1g4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "service_sessions",
        sa.Column("import_source_id", sa.String(length=255), nullable=True),
    )
    op.create_index(
        "ix_service_sessions_import_source_id",
        "service_sessions",
        ["import_source_id"],
    )
    # Partial unique index: enforce idempotency only for rows that came from import.
    op.create_index(
        "uq_service_sessions_tenant_import_source",
        "service_sessions",
        ["tenant_id", "import_source_id"],
        unique=True,
        postgresql_where=sa.text("import_source_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_service_sessions_tenant_import_source",
        table_name="service_sessions",
    )
    op.drop_index(
        "ix_service_sessions_import_source_id",
        table_name="service_sessions",
    )
    op.drop_column("service_sessions", "import_source_id")
