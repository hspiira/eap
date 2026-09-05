"""Default diagnosis taxonomy.

The shared clinical vocabulary, seeded once and global rather than per tenant so
prevalence stays comparable across tenants. Tenant-level preference lives in
`tenant_diagnosis_settings`; see apps/api/docs/SERVICES_MODULE.md.

Codes are stable identifiers used by application code; names are display labels.
"""

DiagnosisSeed = tuple[str, str]
DiagnosisTypeSeed = tuple[str, str, list[DiagnosisSeed]]

# (type_code, type_name, [(diagnosis_code, diagnosis_name), ...])
TAXONOMY: list[DiagnosisTypeSeed] = [
    (
        "MENTAL_ILL_HEALTH",
        "Mental Ill Health",
        [
            ("DEPRESSION", "Depression"),
            ("ANXIETY", "Anxiety"),
            ("PTSD", "PTSD"),
            ("HALLUCINATIONS", "Hallucinations"),
            ("SUICIDAL_IDEATION", "Suicidal Ideation"),
        ],
    ),
    (
        "FAMILY_RELATIONSHIP",
        "Family & Relationship",
        [
            ("MARITAL_CONFLICT", "Marital conflict"),
            ("PARENTING_STRESS", "Parenting stress"),
            ("MARRIAGE_DIVORCE", "Marriage divorce"),
            ("RELATIONSHIP_CHEATING", "Relationship cheating"),
            ("INTERGENERATIONAL_CONFLICT", "Intergenerational conflict"),
        ],
    ),
    (
        "WORK_STRESS_ANXIETY",
        "Work Stress / Anxiety",
        [
            ("WORKPLACE_CONFLICT", "Workplace conflict"),
            ("BURNOUT", "Burnout"),
            ("CAREER_FATIGUE", "Career fatigue"),
            ("DIFFICULT_LEADER", "Difficult leader"),
            ("CHARACTER_ETHICS_MISALIGNMENT", "Character/ethics misalignment"),
        ],
    ),
    (
        "CAREER_CHALLENGES",
        "Career Challenges",
        [
            ("STAGNATION", "Stagnation"),
            ("DEMOTION", "Demotion"),
            ("CAREER_ASSESSMENT", "Career assessment / alignment / improvement"),
        ],
    ),
    (
        "TRAUMA",
        "Trauma",
        [
            ("TRAUMA_PTSD", "PTSD"),
            ("TRAUMA_ASSAULT", "Trauma-Assault"),
            ("TRAUMA_WORK_INCIDENT", "Trauma-Work-incidents (Fraud/disciplinary/environment)"),
            ("EMDR_INDICATED", "EMDR-indicated"),
        ],
    ),
    (
        "LOSS_GRIEF",
        "Loss & Grief",
        [
            ("LOSS_OF_LOVED_ONES", "Loss of loved ones"),
            ("LOSS_OF_MONEY_PROPERTY", "Loss of money/property"),
            ("DISAPPEARANCE_OF_LOVED_ONES", "Disappearance of loved ones"),
        ],
    ),
    (
        "ADDICTIONS",
        "Addictions",
        [
            ("ALCOHOL_AUD", "Alcohol (AUD)"),
            ("SUBSTANCE_SUD", "Substance (SUD)"),
            ("SEX_ABUSE", "Sex abuse"),
            ("BEHAVIOURAL_ADDICTION", "Behavioural addictions"),
        ],
    ),
    (
        "MEDICAL_DISEASE_MGMT",
        "Medical Disease Mgmt",
        [
            ("CHRONIC_DISEASE", "Chronic disease management"),
            ("TERMINALLY_ILL_FAMILY", "Terminally ill family member"),
        ],
    ),
    (
        "HEALTH_PROMOTION",
        "Health Promotion",
        [
            ("LIFESTYLE", "Lifestyle interventions"),
            ("PHYSICAL_FITNESS", "Physical fitness counselling"),
        ],
    ),
    (
        "CHILD_TEENAGE",
        "Child & Teenage",
        [
            ("CHILD_SEX_ABUSE", "Sex abuse"),
            ("EMOTIONAL_ABUSE", "Emotional abuse"),
            ("SCHOOL_ISSUES", "School issues"),
            ("BEHAVIOURAL_ISSUES", "Behavioural issues"),
        ],
    ),
    (
        "GBV",
        "GBV (Gender-Based Violence)",
        [
            ("DOMESTIC_VIOLENCE", "Domestic Violence"),
            ("SEXUAL_HARASSMENT", "Sexual harassment"),
            ("COERCIVE_CONTROL", "Coercive control"),
        ],
    ),
    (
        "FINANCIAL_WELLNESS",
        "Financial Wellness",
        [
            ("DEBT_STRESS", "Debt stress"),
            ("FINANCIAL_LITERACY", "Financial literacy"),
            ("FAMILY_FINANCE_DISPUTE", "Family finance disputes"),
        ],
    ),
    (
        "BEHAVIOURAL_PERSONALITY",
        "Behavioural / Personality",
        [
            ("BEHAVIOURAL_PROBLEM", "Behavioural problem"),
            ("PERSONALITY_ISSUES", "Personality issues"),
            ("ADJUSTMENT_ISSUES", "Adjustment issues"),
        ],
    ),
    (
        "ADHD",
        "ADHD",
        [
            ("ADHD_ASSESSMENT", "Assessment"),
            ("ADHD_COACHING", "Coaching"),
        ],
    ),
    (
        "CHANGE_MANAGEMENT",
        "Change Management",
        [
            ("TRANSITION_STRESS", "Transition stress"),
            ("REORG_ADJUSTMENT", "Re-org adjustment"),
        ],
    ),
    (
        "PERSONAL_GROWTH",
        "Personal Growth",
        [
            ("DAILY_HABITS", "Daily habits"),
            ("EMOTIONAL_RESILIENCE", "Emotional resilience"),
        ],
    ),
]


def type_id_for(code: str) -> str:
    """Deterministic id for a seeded diagnosis type."""
    return f"dt_{code.lower()[:22]}"


def diagnosis_id_for(code: str) -> str:
    """Deterministic id for a seeded diagnosis."""
    return f"dx_{code.lower()[:22]}"
