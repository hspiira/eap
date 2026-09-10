"""Optional Date Joined column on staged member import rows

Revision ID: r7t9v1x3z5b7
Revises: q6s8u0w2y4a6
Create Date: 2026-09-10

A roster's own "Date Joined" (or "Member Since"), stored as raw text like the
existing `date_of_birth` column and parsed the same way (day-first, ISO
fallback) at check time. Feeds `eligible_members.coverage_start`, which
already exists and is read by `EligibleMember.is_currently_eligible`.

Left blank, a member's coverage is treated as starting when the record was
created here, which understates tenure for anyone imported after the fact
(e.g. importing someone today who has had sessions since 2024). Nullable and
optional: the sample roster does not carry this column at all today.

Reversing this drops the staged value. It is reproducible from the source
roster by re-importing; no domain rule reads the staged copy, only the
`eligible_members.coverage_start` it is copied into at apply time.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "r7t9v1x3z5b7"
down_revision: str | Sequence[str] | None = "q6s8u0w2y4a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("member_import_rows", sa.Column("date_joined", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("member_import_rows", "date_joined")
