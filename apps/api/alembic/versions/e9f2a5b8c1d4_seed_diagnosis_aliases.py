"""Seed the confirmed diagnosis aliases

Revision ID: e9f2a5b8c1d4
Revises: d8e1f4a7b0c3
Create Date: 2026-09-05

Loads the alias rows the clinical owner confirmed on 2026-09-05, from the
supplied reference extract. See apps/api/docs/SERVICES_MODULE.md section 5.

Nine of the 51 normalised keys are deliberately absent:

- Four rows whose source classification is still open (question 4). Held back
  rather than guessed, because each changes what a session is counted as.
- Two rows holding clinical narrative rather than a taxonomy value. These
  belong in issue_topic, which the importer already preserves.
- "No show", a scheduling outcome that SessionStatus already covers.
- "Coaching & Mentorship", an intervention that belongs in the service
  catalogue.
- "Others", unsettled (question 5).

A row carrying any of those is rejected by the importer rather than bucketed,
which is the point: a missing alias should be noticed, not averaged in.

One entry corrects its source. "Nurturing mental wellness in the workplace" is
classified as Mental Ill Health in the extract; the clinical owner confirmed it
is a promotion, so it maps to HEALTH_PROMOTION.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.domain.services.diagnosis_alias import normalise_diagnosis_value

revision: str = "e9f2a5b8c1d4"
down_revision: str | Sequence[str] | None = "d8e1f4a7b0c3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SOURCE = "reference_extract_2026_09"

# (raw_value, diagnosis_type_code, diagnosis_code or None)
_ALIASES: list[tuple[str, str, str | None]] = [
    ("Addictions", "ADDICTIONS", None),
    ("ADHD Assessment", "ADHD", "ADHD_ASSESSMENT"),
    ("ADHD Coaching", "ADHD", "ADHD_COACHING"),
    ("Anxiety", "WORK_STRESS_ANXIETY", None),
    ("Behavioral", "BEHAVIOURAL_PERSONALITY", "BEHAVIOURAL_PROBLEM"),
    ("behavioral problem behavioral problem", "BEHAVIOURAL_PERSONALITY", "BEHAVIOURAL_PROBLEM"),
    ("Burnout", "WORK_STRESS_ANXIETY", "BURNOUT"),
    ("career", "CAREER_CHALLENGES", None),
    ("Career improvement", "CAREER_CHALLENGES", None),
    ("Career_Challenges", "CAREER_CHALLENGES", None),
    ("Change Management", "CHANGE_MANAGEMENT", None),
    ("Child_Teenage_Distress", "CHILD_TEENAGE", None),
    ("Daily habits to build emotional strength", "BEHAVIOURAL_PERSONALITY", "PERSONALITY_ISSUES"),
    ("depression", "MENTAL_ILL_HEALTH", "DEPRESSION"),
    ("Emotional_challenges", "MENTAL_ILL_HEALTH", None),
    ("Family &  Relationship discord", "FAMILY_RELATIONSHIP", None),
    ("Family- related", "FAMILY_RELATIONSHIP", None),
    ("Family___Relationship", "FAMILY_RELATIONSHIP", None),
    ("financial_issues", "FINANCIAL_WELLNESS", None),
    ("Gender_Based_Violence", "GBV", None),
    ("grief", "LOSS_GRIEF", None),
    ("Health_Promotion", "HEALTH_PROMOTION", None),
    ("Loss___Grief", "LOSS_GRIEF", None),
    ("Medical_Disease_Management_Alert", "MEDICAL_DISEASE_MGMT", None),
    ("Mental_Ill_Health", "MENTAL_ILL_HEALTH", None),
    ("Needed strengthening to cope with work", "PERSONAL_GROWTH", "EMOTIONAL_RESILIENCE"),
    ("Nurturing mental wellness in the workplace", "HEALTH_PROMOTION", None),
    ("personal growth", "PERSONAL_GROWTH", "DAILY_HABITS"),
    ("Physical_fitness", "HEALTH_PROMOTION", "PHYSICAL_FITNESS"),
    ("Relationship Issues", "FAMILY_RELATIONSHIP", None),
    ("School related concerns", "CHILD_TEENAGE", "SCHOOL_ISSUES"),
    ("Sexual Abuse", "CHILD_TEENAGE", "CHILD_SEX_ABUSE"),
    ("Sexual abuse (minor)", "CHILD_TEENAGE", "CHILD_SEX_ABUSE"),
    ("Stress", "WORK_STRESS_ANXIETY", None),
    ("Substance related", "ADDICTIONS", None),
    ("SUD", "ADDICTIONS", None),
    ("Thriving through Change/Change Management", "CHANGE_MANAGEMENT", None),
    ("Trauma", "TRAUMA", None),
    ("work related", "WORK_STRESS_ANXIETY", None),
    ("work related anxiety", "WORK_STRESS_ANXIETY", None),
    ("Work related stress", "WORK_STRESS_ANXIETY", None),
    ("Work Stress, Fatigue, Burnout", "WORK_STRESS_ANXIETY", None),
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
                "id": f"dxa_{index:04d}",
                "raw_value": raw,
                "normalised_key": normalise_diagnosis_value(raw),
                "diagnosis_type_id": type_id,
                "diagnosis_id": diagnosis_id,
                "source": _SOURCE,
                "confidence": "confirmed",
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
