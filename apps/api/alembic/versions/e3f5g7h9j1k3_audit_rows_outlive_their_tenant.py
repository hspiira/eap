"""Audit rows outlive their tenant

An audit trail that a tenant deletion takes with it is not a trail. The
foreign key on ``audit_logs.tenant_id`` carried ON DELETE CASCADE, so
removing a tenant removed every record of what was done inside it, which is
precisely the history a deletion should be answerable to.

Dropping the constraint also lets the column carry the ``platform`` sentinel
for the shared reference vocabularies, which belong to no single tenant and
so could never satisfy the key.

Revision ID: e3f5g7h9j1k3
Revises: d8x1y3z5a7c9
Create Date: 2026-09-10
"""

from alembic import op

revision = "e3f5g7h9j1k3"
down_revision = "d8x1y3z5a7c9"
branch_labels = None
depends_on = None

_FK = "audit_logs_tenant_id_fkey"


def upgrade() -> None:
    op.drop_constraint(_FK, "audit_logs", type_="foreignkey")


def downgrade() -> None:
    op.create_foreign_key(
        _FK,
        "audit_logs",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
    )
