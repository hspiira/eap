"""Session import row activity-log fields

Adds issue_topic, diagnosis_type_id, diagnosis_id and approved_by to
session_import_rows, so a staged row carries the same enrichment fields
`ServiceSessionEntity` already has (see docs/migrations/PROVIDERS_MIGRATION.md,
"Session import: activity-log fields"). All four are optional and never gate
whether a row is importable. No `feedback` column: CLIENT FEEDBACK is free
text that PRIV-01 forbids reaching an employer aggregate
(app/shared/utils/session_import_normalisation.py), so it is not imported.

Revision ID: f2h4j6l8n0p2
Revises: d6f8h0j2l4n6
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f2h4j6l8n0p2"
down_revision: str | Sequence[str] | None = "d6f8h0j2l4n6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("session_import_rows", sa.Column("issue_topic", sa.Text(), nullable=True))
    op.add_column(
        "session_import_rows", sa.Column("diagnosis_type_id", sa.String(25), nullable=True)
    )
    op.add_column("session_import_rows", sa.Column("diagnosis_id", sa.String(25), nullable=True))
    op.add_column("session_import_rows", sa.Column("approved_by", sa.String(25), nullable=True))


def downgrade() -> None:
    op.drop_column("session_import_rows", "approved_by")
    op.drop_column("session_import_rows", "diagnosis_id")
    op.drop_column("session_import_rows", "diagnosis_type_id")
    op.drop_column("session_import_rows", "issue_topic")
