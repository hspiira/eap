"""Drop the tables behind the three unwired feature verticals.

The crisis layer, manager workspace and consent/DPO register were built out to
entity -> repository -> mapper -> model -> DI factory, but never got routes or
use cases wired up, so nothing could read or write these tables. The Python side
was removed ahead of the monorepo move; this drops the schema to match.

Drop order matters: risk_assessments/safety_plans reference crisis_contacts, and
data_sharing_register references consents, so children go first.

The downgrade deliberately does NOT recreate these tables. Their original
CREATE statements still live in the migrations that introduced them
(v0q3r5s7m9o2, w1r4s6t8n0p3, x2s5t7u9o1q4, y3t6u8v0p2r5, z4u7v9w1q3s6);
reviving the feature means reviving those definitions alongside the code, not
copying them here where they would immediately drift.

Revision ID: d1f4a7c2e9b5
Revises: c9e3a5b7d1f4
Create Date: 2026-09-03

"""

from collections.abc import Sequence

from alembic import op

revision: str = "d1f4a7c2e9b5"
down_revision: str | Sequence[str] | None = "c9e3a5b7d1f4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Children before parents.
TABLES = (
    # consent / DPO register
    "data_sharing_register",
    "dpo_contacts",
    "consents",
    # manager workspace
    "training_enrolments",
    "work_life_referrals",
    "work_life_providers",
    "manager_consults",
    # outcomes / return-to-work
    "return_to_work_plans",
    "fitness_for_duty",
    "outcome_measures",
    # crisis layer
    "caring_contacts",
    "mandatory_reports",
    "safety_plans",
    "risk_assessments",
    "crisis_contacts",
)


def upgrade() -> None:
    for table in TABLES:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")


def downgrade() -> None:
    # Irreversible by design — see the module docstring.
    pass
