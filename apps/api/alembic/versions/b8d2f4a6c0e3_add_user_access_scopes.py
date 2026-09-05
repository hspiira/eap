"""Add users.access_scopes for the clinical/employer privacy wall.

Per-user grants gating the clinical bounded context. Backfill is an empty
list for everyone: nobody holds Clinical until a platform admin grants it,
so the wall fails closed from the first deploy.

Revision ID: b8d2f4a6c0e3
Revises: a7c1e3f5b9d2
Create Date: 2026-07-18
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "b8d2f4a6c0e3"
down_revision = "a7c1e3f5b9d2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("access_scopes", JSONB, nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("users", "access_scopes")
