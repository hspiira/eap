"""Version-controlled role normalisation for the practitioners workbook (P-01).

One explicit mapping per source column, applied at staging. A value with no
entry returns Unmapped; nothing here uses .title() or fuzzy matching. Lookup
keys are deterministic: strip, collapse internal whitespace, casefold. Every
entry was enumerated from the reference workbook
(sha256 ec690c205cbe9172538a6908100cde63353a1cc18652941ffe07c157117e48e9).

The tables collapse spelling and orthography variants of one role only.
Compound values ("Engineer/Family life Coach/Counsellor"), parenthetical
qualifiers ("Clinical Psychologist (Trauma)") and topic or memo entries
("Schools/Teenage Mental Health", "Minet Media") stay unmapped: dropping a
qualifier is a content decision, not a spelling one. Which canonical role
names become specialty catalogue entries is a product decision, not an
engineering one; these tables create no catalogue entries.
"""

from app.shared.utils.session_import_normalisation import Unmapped

PROFESSION_COLUMN = "PROFESSION"
SPECIALITY_COLUMN = "Speciality"


def _key(value: str) -> str:
    return " ".join(value.split()).casefold()


def _lookup(column: str, table: dict[str, str], raw: str | None) -> str | Unmapped | None:
    """Blank stays blank; an unlisted value is Unmapped, never defaulted."""
    if raw is None or not raw.strip():
        return None
    return table.get(_key(raw), Unmapped(column=column, value=raw.strip()))


# 21 of the 57 distinct PROFESSION spellings map; the rest are compounds,
# qualified variants or non-role entries and stay unmapped for review.
_PROFESSION: dict[str, str] = {
    "addiction counselor": "Addiction Counsellor",
    "child and adoloscent psychologist": "Child and Adolescent Psychologist",
    "child psychologist": "Child Psychologist",
    "clincal psychologist": "Clinical Psychologist",
    "clinical psychologist": "Clinical Psychologist",
    "clinical psychology": "Clinical Psychologist",
    "communication specialist": "Communication Specialist",
    "counseling psychologist": "Counselling Psychologist",
    "counselling psychologist": "Counselling Psychologist",
    "counselling psycholoogist": "Counselling Psychologist",
    "counsellor": "Counsellor",
    "counselor": "Counsellor",
    "financial coach": "Financial Coach",
    "marriage and relationship counsellor": "Marriage and Relationship Counsellor",
    "occupational therapist": "Occupational Therapist",
    "psychiatric nurse": "Psychiatric Nurse",
    "psychiatrist": "Psychiatrist",
    "psychologist": "Psychologist",
    "registered nurse": "Registered Nurse",
    "training consultant": "Training Consultant",
    "wellness coach": "Wellness Coach",
}

# 7 of the 50 distinct Speciality spellings map. Most of that column holds
# topics and delivery notes rather than roles, so it maps sparsely; those
# values stay unmapped rather than being promoted to roles by engineering.
_SPECIALITY: dict[str, str] = {
    "child psychologist": "Child Psychologist",
    "counseling": "Counselling",
    "counselling": "Counselling",
    "financial coach": "Financial Coach",
    "marriage counselling": "Marriage Counselling",
    "psychiatrist": "Psychiatrist",
    "training consultant": "Training Consultant",
}

_TABLES: dict[str, dict[str, str]] = {
    PROFESSION_COLUMN: _PROFESSION,
    SPECIALITY_COLUMN: _SPECIALITY,
}


def map_profession(raw: str | None) -> str | Unmapped | None:
    """Map a partner-list PROFESSION value to its canonical role name."""
    return _lookup(PROFESSION_COLUMN, _PROFESSION, raw)


def map_speciality(raw: str | None) -> str | Unmapped | None:
    """Map a consultants-sheet Speciality value to its canonical role name."""
    return _lookup(SPECIALITY_COLUMN, _SPECIALITY, raw)


def map_role(column: str, raw: str | None) -> str | Unmapped | None:
    """Map a value from whichever role column a sheet carries."""
    table = _TABLES.get(column)
    if table is None:
        raise ValueError(f"No normalisation table for column {column!r}")
    return _lookup(column, table, raw)


def table_keys(column: str) -> frozenset[str]:
    """The lookup keys of one column's table, for drift tests."""
    return frozenset(_TABLES[column])
