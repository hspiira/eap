"""Constrain services.category to the ServiceCategory enum

Revision ID: a5b8c1d4e7f0
Revises: g1h3j5l7n9p1
Create Date: 2026-09-05

`services.category` was free text while the programme caps and authorizations
gate on the ServiceCategory enum, so a session could not be mapped to the cap it
draws down. See apps/api/docs/SERVICES_MODULE.md section 3.6.

The stored representation does not change: EnumValueType persists the enum's
value as a string, so this adds a CHECK constraint over the existing VARCHAR.

If an environment holds values outside the enum, the constraint will refuse to
apply and the deploy fails. That is deliberate; the values need a decision
rather than a default. Find them with:

    SELECT DISTINCT category FROM services
    WHERE category IS NOT NULL
      AND category NOT IN (
        'ShortTermCounselling','CrisisIntervention','SubstanceUse',
        'ManagerConsult','WorkLifeReferral','CISMResponse','WellnessCoaching'
      );
"""
from typing import Sequence, Union

from alembic import op

revision: str = "a5b8c1d4e7f0"
down_revision: Union[str, Sequence[str], None] = "g1h3j5l7n9p1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Inlined rather than imported: the ServiceCategory enum this migration once
# read no longer exists (superseded by the service_categories table in
# migration 7af2412c8b90), and a historical migration's emitted SQL must not
# change after the fact. These are exactly the seven values it always emitted.
_ALLOWED = ", ".join(
    f"'{v}'"
    for v in (
        "ShortTermCounselling",
        "CrisisIntervention",
        "SubstanceUse",
        "ManagerConsult",
        "WorkLifeReferral",
        "CISMResponse",
        "WellnessCoaching",
    )
)


def upgrade() -> None:
    op.create_check_constraint(
        "service_category_check",
        "services",
        f"category IS NULL OR category IN ({_ALLOWED})",
    )


def downgrade() -> None:
    op.drop_constraint("service_category_check", "services", type_="check")
