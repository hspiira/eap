"""Carry the resolved subject and normalised values on staged session rows

Staging previously quarantined every row as UnresolvedMember because nothing
resolved a member, a client or a service. Rows now store what resolution and
normalisation produce, so an Accepted row carries everything the historical
write path needs.

Revision ID: f0y3a5c7e9g1
Revises: e9x2z4b6d8f0
Create Date: 2026-09-07

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f0y3a5c7e9g1"
down_revision: str | Sequence[str] | None = "e9x2z4b6d8f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COLUMNS = (
    ("client_id", sa.String(length=25)),
    ("attendance", sa.String(length=32)),
    ("member_id", sa.String(length=25)),
    ("service_id", sa.String(length=25)),
    ("session_type", sa.String(length=32)),
    ("category", sa.String(length=32)),
    ("clinical_outcome", sa.String(length=32)),
    ("session_status", sa.String(length=32)),
    ("client_type", sa.String(length=32)),
    ("rate_ugx", sa.Integer()),
    ("session_number", sa.Integer()),
)


def upgrade() -> None:
    for name, kind in _COLUMNS:
        op.add_column("session_import_rows", sa.Column(name, kind, nullable=True))
    op.create_index("ix_session_import_rows_client_id", "session_import_rows", ["client_id"])
    op.create_index("ix_session_import_rows_member_id", "session_import_rows", ["member_id"])


def downgrade() -> None:
    op.drop_index("ix_session_import_rows_member_id", table_name="session_import_rows")
    op.drop_index("ix_session_import_rows_client_id", table_name="session_import_rows")
    for name, _ in reversed(_COLUMNS):
        op.drop_column("session_import_rows", name)
