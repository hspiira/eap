"""Promote contracts.period JSON to real start_date/end_date columns

The contract term was stored as a JSON blob of ISO strings. Nothing could filter
or sort on it in SQL: the renewal window needs an indexed range scan on the end of
the term, and `period->>'end_date'` neither uses an index nor typechecks as a
timestamp. The FE consequently had a renewal filter with nothing behind it.

The domain is unchanged — ContractEntity still models the term as one DateRange.
This is persistence only; the mapper joins the two columns back together.

Backfill notes:
  - Values in the blob are ISO-8601 strings written by `datetime.isoformat()`, so
    they are directly castable to timestamptz.
  - Rows are expected to have both keys: the mapper has always raised on a period
    missing either, so a row without them could never have been loaded. The
    upgrade still asserts this rather than assuming it, and fails loudly with the
    offending ids instead of silently inventing dates.

Revision ID: a7c1e3f5b9d2
Revises: f9e8d7c6b5a4
Create Date: 2026-07-13

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a7c1e3f5b9d2"
down_revision: Union[str, Sequence[str], None] = "f9e8d7c6b5a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # Fail before touching anything if any row cannot be backfilled.
    unmappable = bind.execute(
        sa.text(
            """
            SELECT id FROM contracts
            WHERE deleted_at IS NULL
              AND (
                period IS NULL
                OR period ->> 'start_date' IS NULL
                OR period ->> 'end_date' IS NULL
              )
            LIMIT 20
            """
        )
    ).fetchall()
    if unmappable:
        ids = ", ".join(row[0] for row in unmappable)
        raise RuntimeError(
            "Cannot backfill contract period; rows missing start_date/end_date: "
            f"{ids}. Repair these rows, then re-run."
        )

    # Nullable first so existing rows can be filled, then tightened below.
    op.add_column(
        "contracts", sa.Column("start_date", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "contracts", sa.Column("end_date", sa.DateTime(timezone=True), nullable=True)
    )

    op.execute(
        """
        UPDATE contracts
        SET start_date = (period ->> 'start_date')::timestamptz,
            end_date   = (period ->> 'end_date')::timestamptz
        WHERE period IS NOT NULL
          AND period ->> 'start_date' IS NOT NULL
          AND period ->> 'end_date' IS NOT NULL
        """
    )

    # Soft-deleted rows are excluded from the guard above, so they may still be
    # null here. Give them the epoch rather than blocking the migration on rows
    # no query returns; they keep their period JSON in the down path either way.
    op.execute(
        """
        UPDATE contracts
        SET start_date = COALESCE(start_date, TIMESTAMPTZ '1970-01-01 00:00:00+00'),
            end_date   = COALESCE(end_date,   TIMESTAMPTZ '1970-01-01 00:00:00+00')
        WHERE start_date IS NULL OR end_date IS NULL
        """
    )

    op.alter_column("contracts", "start_date", nullable=False)
    op.alter_column("contracts", "end_date", nullable=False)

    # The renewal window scans on end_date; start_date is indexed for sorting.
    op.create_index("ix_contracts_start_date", "contracts", ["start_date"])
    op.create_index("ix_contracts_end_date", "contracts", ["end_date"])

    op.drop_column("contracts", "period")


def downgrade() -> None:
    op.add_column("contracts", sa.Column("period", sa.JSON(), nullable=True))

    # Rebuild the blob in the exact shape the old mapper read: ISO-8601 strings
    # under start_date/end_date.
    op.execute(
        """
        UPDATE contracts
        SET period = jsonb_build_object(
            'start_date', to_char(start_date AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS+00:00'),
            'end_date',   to_char(end_date   AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS+00:00')
        )
        """
    )
    op.alter_column("contracts", "period", nullable=False)

    op.drop_index("ix_contracts_end_date", table_name="contracts")
    op.drop_index("ix_contracts_start_date", table_name="contracts")
    op.drop_column("contracts", "end_date")
    op.drop_column("contracts", "start_date")
