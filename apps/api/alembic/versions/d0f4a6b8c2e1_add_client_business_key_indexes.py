"""Add tenant-scoped active client business key indexes."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision = "d0f4a6b8c2e1"
down_revision = "c9e3a5b7d1f4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "uq_clients_tenant_name_active",
        "clients",
        ["tenant_id", sa.text("lower(name)")],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "uq_clients_tenant_code_active",
        "clients",
        ["tenant_id", sa.text("upper(code)")],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_clients_tenant_code_active", table_name="clients")
    op.drop_index("uq_clients_tenant_name_active", table_name="clients")
