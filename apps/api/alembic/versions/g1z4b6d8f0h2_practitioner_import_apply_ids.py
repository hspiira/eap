"""Record the ids created when a practitioner import row is applied

Applying an Accepted row creates a practitioner, and possibly an organisation
and an affiliation. The created ids live on the staged row so provenance runs
from workbook cell to live record, and so a replayed apply can skip the row.

Revision ID: g1z4b6d8f0h2
Revises: f0y3a5c7e9g1
Create Date: 2026-09-07

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "g1z4b6d8f0h2"
down_revision: str | Sequence[str] | None = "f0y3a5c7e9g1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COLUMNS = ("imported_provider_id", "imported_organisation_id", "imported_affiliation_id")


def upgrade() -> None:
    for column in _COLUMNS:
        op.add_column(
            "practitioner_import_rows", sa.Column(column, sa.String(25), nullable=True)
        )


def downgrade() -> None:
    for column in reversed(_COLUMNS):
        op.drop_column("practitioner_import_rows", column)
