"""Give every contract the pricing its billing rate already implied

Revision ID: b6w9x1y3s5u8
Revises: a5v8w0x2r4t7
Create Date: 2026-09-08

Price was represented twice: `billing_rate`, which the screens showed, and
`pricing`, which the invoice preview computed from and which no contract had.
A flat periodic charge is a retainer, so this says so, and `billing_rate`
becomes a reading of the pricing rather than a second source.

See docs/CONTRACTS_REVIEW_2026_09_08.md section 2.2.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b6w9x1y3s5u8"
down_revision: str | Sequence[str] | None = "a5v8w0x2r4t7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE contracts
               SET pricing_model = 'Retainer',
                   pricing_config = json_build_object(
                       'model', 'Retainer',
                       'retainer_amount', billing_rate
                   )
             WHERE pricing_model IS NULL
            """
        )
    )


def downgrade() -> None:
    # Only the rows this added: a contract configured by hand keeps its pricing.
    op.execute(
        sa.text(
            """
            UPDATE contracts
               SET pricing_model = NULL,
                   pricing_config = NULL
             WHERE pricing_model = 'Retainer'
               AND pricing_config::text = json_build_object(
                       'model', 'Retainer',
                       'retainer_amount', billing_rate
                   )::text
            """
        )
    )
