"""Attach a delivered session to the contract it was delivered under

Revision ID: c7x0y2z4t6v9
Revises: b6w9x1y3s5u8
Create Date: 2026-09-08

A session carried a client and a date and no contract, so every question of
the form "what did this term cost" was answered by a date window. The column
is nullable because most sessions cannot be placed: 308 of the 369 in the
development database fall outside any term, mostly for clients with no
contract on file at all.

Backfilling is safe now that one client holds one term at a time: every
session that falls inside a term falls inside exactly one.

See docs/CONTRACTS_REVIEW_2026_09_08.md section 2.7.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c7x0y2z4t6v9"
down_revision: str | Sequence[str] | None = "b6w9x1y3s5u8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("service_sessions", sa.Column("contract_id", sa.String(length=25), nullable=True))
    op.create_index("ix_service_sessions_contract_id", "service_sessions", ["contract_id"])
    op.create_foreign_key(
        "service_sessions_contract_id_fkey",
        "service_sessions",
        "contracts",
        ["contract_id"],
        ["id"],
    )
    op.execute(
        sa.text(
            """
            UPDATE service_sessions s
               SET contract_id = c.id
              FROM contracts c
             WHERE c.tenant_id = s.tenant_id
               AND c.client_id = s.client_id
               AND c.deleted_at IS NULL
               AND (s.scheduled_at AT TIME ZONE 'UTC')::date
                   BETWEEN c.start_date AND c.end_date
               AND s.contract_id IS NULL
            """
        )
    )


def downgrade() -> None:
    op.drop_constraint("service_sessions_contract_id_fkey", "service_sessions", type_="foreignkey")
    op.drop_index("ix_service_sessions_contract_id", table_name="service_sessions")
    op.drop_column("service_sessions", "contract_id")
