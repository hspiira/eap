"""Persist the reason for a client suspension."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision = "e1a5c7b9d3f2"
down_revision = "d0f4a6b8c2e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("clients", sa.Column("suspension_reason", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("clients", "suspension_reason")
