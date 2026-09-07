"""Abandoned session import batches no longer hold their file hash

An abandoned batch is one somebody superseded on purpose, usually because it
was staged before the review data its rows needed had been loaded. Holding its
hash against the extract meant that extract could never be staged again, so the
uniqueness now skips abandoned rows.

Revision ID: h3b5d7f9j1l3
Revises: g1z4b6d8f0h2
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "h3b5d7f9j1l3"
down_revision: str | None = "g1z4b6d8f0h2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NAME = "uq_session_import_batches_tenant_file_hash"
TABLE = "session_import_batches"


def upgrade() -> None:
    op.drop_constraint(NAME, TABLE, type_="unique")
    op.create_index(
        NAME,
        TABLE,
        ["tenant_id", "file_hash"],
        unique=True,
        postgresql_where=sa.text("status <> 'Abandoned'"),
    )


def downgrade() -> None:
    """Fails if two live rows share a hash, which is the point of the constraint."""
    op.drop_index(NAME, table_name=TABLE)
    op.create_unique_constraint(NAME, TABLE, ["tenant_id", "file_hash"])
