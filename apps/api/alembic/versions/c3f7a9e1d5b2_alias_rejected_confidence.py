"""Allow a reviewer to reject a legacy alias mapping.

The confidence check admitted only 'confirmed' and 'inferred', so a reviewer
who read an inferred mapping and judged it wrong had nowhere to record that.
Deleting the row instead would lose the decision: the next import would infer
the same reading again, because a deleted alias and one nobody has reviewed
look identical.

Revision ID: c3f7a9e1d5b2
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c3f7a9e1d5b2"
down_revision: str | Sequence[str] | None = "fc5d8bb02d9a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CONSTRAINT = "diagnosis_alias_confidence_check"


def upgrade() -> None:
    op.drop_constraint(_CONSTRAINT, "diagnosis_aliases", type_="check")
    op.create_check_constraint(
        _CONSTRAINT,
        "diagnosis_aliases",
        "confidence IN ('confirmed', 'inferred', 'rejected')",
    )


def downgrade() -> None:
    # A rejected mapping has no pre-rejection reading to fall back to, and
    # leaving it as confirmed would assert the opposite of the decision.
    op.execute("DELETE FROM diagnosis_aliases WHERE confidence = 'rejected'")
    op.drop_constraint(_CONSTRAINT, "diagnosis_aliases", type_="check")
    op.create_check_constraint(
        _CONSTRAINT,
        "diagnosis_aliases",
        "confidence IN ('confirmed', 'inferred')",
    )
