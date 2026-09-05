"""Add the transitional client aliases JSON column."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision = "a5b7c9d1e3f4"
down_revision = "z4u7v9w1q3s6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "clients",
        sa.Column("aliases", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )


def downgrade() -> None:
    op.drop_column("clients", "aliases")
