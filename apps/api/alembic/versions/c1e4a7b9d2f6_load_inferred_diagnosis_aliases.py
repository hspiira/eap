"""Load the four unconfirmed aliases as inferred

Revision ID: c1e4a7b9d2f6
Revises: c9e1a3b5d7f9
Create Date: 2026-09-06

The four rows behind question 4 of apps/api/docs/SERVICES_MODULE.md carried no
alias, so any legacy row using them was rejected. That was the right default
while the whole taxonomy was unreviewed, but it blocks the import indefinitely
on five values out of 53, and a rejected row is not reviewable: it simply does
not land.

These load with ``confidence = 'inferred'`` rather than ``'confirmed'``, which
is what that column exists for. The mapping is my reading of the label, stated
in section 3.4, and a reviewer can list exactly these rows with
``GET /diagnoses/aliases?confidence=inferred`` and correct any of them through
``PUT /diagnoses/aliases`` without another migration.

Each mapping and why:

- ``Personality`` is filed under Family & Relationship in the source. It reads
  as BEHAVIOURAL_PERSONALITY / PERSONALITY_ISSUES.
- ``Change Magement Risks`` (typo in the source) is filed under Career
  Improvement. It reads as CHANGE_MANAGEMENT.
- ``Family Stress, fatigue, Burnout`` is filed under Family & Relationship
  while the near-identical work variant goes to Work stress & Anxiety. Burnout
  is the distinguishing symptom in both, so this follows the family reading the
  source gave it rather than reclassifying it.
- ``The client presented with symptoms of depression and fear about living
  without any parent`` is filed under Work stress & Anxiety. On its own text it
  reads as depression.

Deliberately still absent, because none is a diagnosis and mapping them would
corrupt prevalence rather than unblock it:

- ``No show``, which SessionStatus already models.
- ``Coaching & Mentorship``, an intervention for the service catalogue.
- ``Others`` and the two remaining narrative rows.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.domain.services.diagnosis_alias import normalise_diagnosis_value

revision: str = "c1e4a7b9d2f6"
down_revision: str | Sequence[str] | None = "c9e1a3b5d7f9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SOURCE = "inferred_review_2026_09"

# (raw_value, diagnosis_type_code, diagnosis_code or None)
_ALIASES: list[tuple[str, str, str | None]] = [
    ("Personality", "BEHAVIOURAL_PERSONALITY", "PERSONALITY_ISSUES"),
    ("Change Magement Risks", "CHANGE_MANAGEMENT", None),
    ("Family Stress, fatigue, Burnout", "FAMILY_RELATIONSHIP", None),
    (
        "The client presented with symptoms of depression and fear about living "
        "without any parent",
        "MENTAL_ILL_HEALTH",
        "DEPRESSION",
    ),
]


def upgrade() -> None:
    conn = op.get_bind()
    types = {
        code: row_id
        for row_id, code in conn.execute(sa.text("SELECT id, code FROM diagnosis_types"))
    }
    diagnoses = {
        code: row_id for row_id, code in conn.execute(sa.text("SELECT id, code FROM diagnoses"))
    }

    rows = []
    for index, (raw, type_code, diagnosis_code) in enumerate(_ALIASES):
        type_id = types.get(type_code)
        if type_id is None:
            raise RuntimeError(f"Unknown diagnosis type code {type_code!r} for alias {raw!r}")
        diagnosis_id = None
        if diagnosis_code is not None:
            diagnosis_id = diagnoses.get(diagnosis_code)
            if diagnosis_id is None:
                raise RuntimeError(f"Unknown diagnosis code {diagnosis_code!r} for alias {raw!r}")
        rows.append(
            {
                "id": f"dxa_inf_{index:04d}",
                "raw_value": raw,
                "normalised_key": normalise_diagnosis_value(raw),
                "diagnosis_type_id": type_id,
                "diagnosis_id": diagnosis_id,
                "source": _SOURCE,
                "confidence": "inferred",
            }
        )

    conn.execute(
        sa.text(
            "INSERT INTO diagnosis_aliases "
            "(id, raw_value, normalised_key, diagnosis_type_id, diagnosis_id, source, confidence) "
            "VALUES (:id, :raw_value, :normalised_key, :diagnosis_type_id, :diagnosis_id, "
            ":source, :confidence) "
            "ON CONFLICT (normalised_key) DO NOTHING"
        ),
        rows,
    )


def downgrade() -> None:
    op.execute(sa.text(f"DELETE FROM diagnosis_aliases WHERE source = '{_SOURCE}'"))
