"""Give a contract a reference and a link to the term it renewed

Revision ID: a5v8w0x2r4t7
Revises: 7af2412c8b90
Create Date: 2026-09-08

A contract had no human identity and no link to its predecessor, so a renewed
agreement was either one row with a moving end date or several unrelated rows.
See docs/CONTRACTS_REVIEW_2026_09_08.md section 2.1.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a5v8w0x2r4t7"
down_revision: str | Sequence[str] | None = "7af2412c8b90"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("contracts", sa.Column("reference", sa.String(length=64), nullable=True))
    op.add_column("contracts", sa.Column("renewed_from_id", sa.String(length=25), nullable=True))
    op.create_index("ix_contracts_reference", "contracts", ["tenant_id", "reference"])
    op.create_index("ix_contracts_renewed_from_id", "contracts", ["renewed_from_id"])
    op.create_foreign_key(
        "contracts_renewed_from_id_fkey",
        "contracts",
        "contracts",
        ["renewed_from_id"],
        ["id"],
    )
    # One successor per term: a contract cannot be renewed twice into two
    # different terms without the chain becoming a tree nobody can read.
    op.create_index(
        "uq_contracts_renewed_from_id",
        "contracts",
        ["renewed_from_id"],
        unique=True,
        postgresql_where=sa.text("renewed_from_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_contracts_renewed_from_id", table_name="contracts")
    op.drop_constraint("contracts_renewed_from_id_fkey", "contracts", type_="foreignkey")
    op.drop_index("ix_contracts_renewed_from_id", table_name="contracts")
    op.drop_index("ix_contracts_reference", table_name="contracts")
    op.drop_column("contracts", "renewed_from_id")
    op.drop_column("contracts", "reference")
