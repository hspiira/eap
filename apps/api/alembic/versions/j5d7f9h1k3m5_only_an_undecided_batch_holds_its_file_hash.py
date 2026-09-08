"""Only a still-staged batch holds its file hash

The hash uniqueness was written to stop an operator staging the same extract
twice by accident. It also stopped the one deliberate reason to stage it again:
reference data improves, and rows that could not be resolved before now can.
That is what the Duplicate row outcome is for, and under the old constraint
that outcome was unreachable for any file.

Uniqueness now covers only batches still awaiting a decision. Once a batch is
applied or abandoned the extract may be staged again, and the per-row replay
keys stop any source row being imported a second time.

Revision ID: j5d7f9h1k3m5
Revises: h3b5d7f9j1l3
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "j5d7f9h1k3m5"
down_revision: str | None = "h3b5d7f9j1l3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NAME = "uq_session_import_batches_tenant_file_hash"
TABLE = "session_import_batches"


def _reindex(where: str) -> None:
    op.drop_index(NAME, table_name=TABLE)
    op.create_index(
        NAME,
        TABLE,
        ["tenant_id", "file_hash"],
        unique=True,
        postgresql_where=sa.text(where),
    )


def upgrade() -> None:
    _reindex("status = 'Staged'")


def downgrade() -> None:
    _reindex("status <> 'Abandoned'")
