"""Add diagnosis taxonomy + seed data (Phase 2 #D-Tax)

Revision ID: f4a6b8c1d3e5
Revises: e3f5a7c9b2d4
Create Date: 2026-05-08

Seeds the SAD §B.1 reference taxonomy: 16 diagnosis types with curated
diagnoses per type. Codes are stable identifiers (UPPER_SNAKE_CASE) used
by application code; names are display labels.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "f4a6b8c1d3e5"
down_revision: Union[str, Sequence[str], None] = "e3f5a7c9b2d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (type_code, type_name, [(dx_code, dx_name), ...])
_TAXONOMY: list[tuple[str, str, list[tuple[str, str]]]] = [
    ("MENTAL_ILL_HEALTH", "Mental Ill Health", [
        ("DEPRESSION", "Depression"),
        ("ANXIETY", "Anxiety"),
        ("PTSD", "PTSD"),
        ("HALLUCINATIONS", "Hallucinations"),
        ("SUICIDAL_IDEATION", "Suicidal Ideation"),
    ]),
    ("FAMILY_RELATIONSHIP", "Family & Relationship", [
        ("MARITAL_CONFLICT", "Marital conflict"),
        ("PARENTING_STRESS", "Parenting stress"),
        ("MARRIAGE_DIVORCE", "Marriage divorce"),
        ("RELATIONSHIP_CHEATING", "Relationship cheating"),
        ("INTERGENERATIONAL_CONFLICT", "Intergenerational conflict"),
    ]),
    ("WORK_STRESS_ANXIETY", "Work Stress / Anxiety", [
        ("WORKPLACE_CONFLICT", "Workplace conflict"),
        ("BURNOUT", "Burnout"),
        ("CAREER_FATIGUE", "Career fatigue"),
        ("DIFFICULT_LEADER", "Difficult leader"),
        ("CHARACTER_ETHICS_MISALIGNMENT", "Character/ethics misalignment"),
    ]),
    ("CAREER_CHALLENGES", "Career Challenges", [
        ("STAGNATION", "Stagnation"),
        ("DEMOTION", "Demotion"),
        ("CAREER_ASSESSMENT", "Career assessment / alignment / improvement"),
    ]),
    ("TRAUMA", "Trauma", [
        ("TRAUMA_PTSD", "PTSD"),
        ("TRAUMA_ASSAULT", "Trauma-Assault"),
        ("TRAUMA_WORK_INCIDENT", "Trauma-Work-incidents (Fraud/disciplinary/environment)"),
        ("EMDR_INDICATED", "EMDR-indicated"),
    ]),
    ("LOSS_GRIEF", "Loss & Grief", [
        ("LOSS_OF_LOVED_ONES", "Loss of loved ones"),
        ("LOSS_OF_MONEY_PROPERTY", "Loss of money/property"),
        ("DISAPPEARANCE_OF_LOVED_ONES", "Disappearance of loved ones"),
    ]),
    ("ADDICTIONS", "Addictions", [
        ("ALCOHOL_AUD", "Alcohol (AUD)"),
        ("SUBSTANCE_SUD", "Substance (SUD)"),
        ("SEX_ABUSE", "Sex abuse"),
        ("BEHAVIOURAL_ADDICTION", "Behavioural addictions"),
    ]),
    ("MEDICAL_DISEASE_MGMT", "Medical Disease Mgmt", [
        ("CHRONIC_DISEASE", "Chronic disease management"),
        ("TERMINALLY_ILL_FAMILY", "Terminally ill family member"),
    ]),
    ("HEALTH_PROMOTION", "Health Promotion", [
        ("LIFESTYLE", "Lifestyle interventions"),
        ("PHYSICAL_FITNESS", "Physical fitness counselling"),
    ]),
    ("CHILD_TEENAGE", "Child & Teenage", [
        ("CHILD_SEX_ABUSE", "Sex abuse"),
        ("EMOTIONAL_ABUSE", "Emotional abuse"),
        ("SCHOOL_ISSUES", "School issues"),
        ("BEHAVIOURAL_ISSUES", "Behavioural issues"),
    ]),
    ("GBV", "GBV (Gender-Based Violence)", [
        ("DOMESTIC_VIOLENCE", "Domestic Violence"),
        ("SEXUAL_HARASSMENT", "Sexual harassment"),
        ("COERCIVE_CONTROL", "Coercive control"),
    ]),
    ("FINANCIAL_WELLNESS", "Financial Wellness", [
        ("DEBT_STRESS", "Debt stress"),
        ("FINANCIAL_LITERACY", "Financial literacy"),
        ("FAMILY_FINANCE_DISPUTE", "Family finance disputes"),
    ]),
    ("BEHAVIOURAL_PERSONALITY", "Behavioural / Personality", [
        ("BEHAVIOURAL_PROBLEM", "Behavioural problem"),
        ("PERSONALITY_ISSUES", "Personality issues"),
        ("ADJUSTMENT_ISSUES", "Adjustment issues"),
    ]),
    ("ADHD", "ADHD", [
        ("ADHD_ASSESSMENT", "Assessment"),
        ("ADHD_COACHING", "Coaching"),
    ]),
    ("CHANGE_MANAGEMENT", "Change Management", [
        ("TRANSITION_STRESS", "Transition stress"),
        ("REORG_ADJUSTMENT", "Re-org adjustment"),
    ]),
    ("PERSONAL_GROWTH", "Personal Growth", [
        ("DAILY_HABITS", "Daily habits"),
        ("EMOTIONAL_RESILIENCE", "Emotional resilience"),
    ]),
]


def upgrade() -> None:
    diagnosis_types = op.create_table(
        "diagnosis_types",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    diagnoses = op.create_table(
        "diagnoses",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("type_id", sa.String(length=25), sa.ForeignKey("diagnosis_types.id"), nullable=False, index=True),
        sa.Column("code", sa.String(length=50), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    type_rows = []
    diagnosis_rows = []
    for type_idx, (type_code, type_name, dx_list) in enumerate(_TAXONOMY):
        type_id = f"dt_{type_code.lower()[:22]}"
        type_rows.append({
            "id": type_id,
            "code": type_code,
            "name": type_name,
            "description": None,
            "sort_order": type_idx,
            "is_active": True,
            "version": 1,
            "effective_until": None,
        })
        for dx_idx, (dx_code, dx_name) in enumerate(dx_list):
            diagnosis_rows.append({
                "id": f"dx_{dx_code.lower()[:22]}",
                "type_id": type_id,
                "code": dx_code,
                "name": dx_name,
                "description": None,
                "sort_order": dx_idx,
                "is_active": True,
                "version": 1,
                "effective_until": None,
            })

    if type_rows:
        op.bulk_insert(diagnosis_types, type_rows)
    if diagnosis_rows:
        op.bulk_insert(diagnoses, diagnosis_rows)


def downgrade() -> None:
    op.drop_table("diagnoses")
    op.drop_table("diagnosis_types")
