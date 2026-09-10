"""Optional employment details on the member roster and its import rows

Revision ID: q6s8u0w2y4a6
Revises: p5r7t9v1x3z5
Create Date: 2026-09-10

Job title, classification, skill, department, unit and employment type as
they arrive on an employer roster. All nullable: the sample roster populates
them for one client out of the file's rows, and no other employer supplies
them.

Free text rather than reference tables. The vocabularies are the employer's
own org chart, not shared platform taxonomy, so a per-tenant reference table
would hold one client's values and need script-only maintenance.

Reversing this drops the values. They are reproducible from the source
roster by re-importing, and no domain rule reads them.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "q6s8u0w2y4a6"
down_revision: str | Sequence[str] | None = "p5r7t9v1x3z5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COLUMNS = (
    "job_title",
    "job_classification",
    "skill",
    "department",
    "unit",
    "employment_type",
)
_TABLES = ("eligible_members", "member_import_rows")


def upgrade() -> None:
    for table in _TABLES:
        for column in _COLUMNS:
            op.add_column(table, sa.Column(column, sa.String(255), nullable=True))


def downgrade() -> None:
    for table in _TABLES:
        for column in _COLUMNS:
            op.drop_column(table, column)
