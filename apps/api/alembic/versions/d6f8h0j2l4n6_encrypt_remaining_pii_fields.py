"""Encrypt case referral notes, clinical subject continuity notes,
outreach notes/triage payloads, and next-of-kin contact details

Revision ID: d6f8h0j2l4n6
Revises: c5e7g9i1k3m5
Create Date: 2026-09-11

Extends the b4d6f8h0j2l4/c5e7g9i1k3m5 field-encryption work to the rest of
the plaintext clinical/PII fields found during the same review:

- cases.referral_notes (already TEXT, backfill only)
- clinical_subjects.notes_for_continuity (already TEXT, backfill only)
- outreach_records.notes (already TEXT, backfill only)
- outreach_records.triage_responses / .triage_scores (JSON to TEXT, like
  clinical_notes.body/.amendments)
- member_next_of_kin.name / .phone / .email (VARCHAR to TEXT, like
  eligible_members.national_id/.passport_number)

Same backfill requirement as before: these tables already hold real rows
in some environments, so a schema-only change would break decrypt() on the
first read after this release deploys.
"""

import json

import sqlalchemy as sa

from alembic import op

revision = "d6f8h0j2l4n6"
down_revision = "c5e7g9i1k3m5"
branch_labels = None
depends_on = None

_SELECT_CASES = sa.text(
    "SELECT id, tenant_id, referral_notes FROM cases WHERE referral_notes IS NOT NULL"
)
_UPDATE_CASE = sa.text("UPDATE cases SET referral_notes = :referral_notes WHERE id = :id")

_SELECT_SUBJECTS = sa.text(
    "SELECT id, tenant_id, notes_for_continuity FROM clinical_subjects"
    " WHERE notes_for_continuity IS NOT NULL"
)
_UPDATE_SUBJECT = sa.text(
    "UPDATE clinical_subjects SET notes_for_continuity = :notes_for_continuity WHERE id = :id"
)

_SELECT_OUTREACH = sa.text(
    "SELECT id, tenant_id, notes, triage_responses, triage_scores FROM outreach_records"
    " WHERE notes IS NOT NULL OR triage_responses IS NOT NULL OR triage_scores IS NOT NULL"
)
_UPDATE_OUTREACH = sa.text(
    "UPDATE outreach_records SET notes = :notes, triage_responses = :triage_responses,"
    " triage_scores = :triage_scores WHERE id = :id"
)

_SELECT_NOK = sa.text("SELECT id, tenant_id, name, phone, email FROM member_next_of_kin")
_UPDATE_NOK = sa.text(
    "UPDATE member_next_of_kin SET name = :name, phone = :phone, email = :email WHERE id = :id"
)


def _configure_key_provider() -> None:
    from app.core.config import settings
    from app.core.encryption import get_key_provider, set_key_provider

    set_key_provider(
        get_key_provider(
            settings.ENCRYPTION_KEY_PROVIDER,
            kms_key_id=settings.ENCRYPTION_KMS_KEY_ID,
            kek_ciphertext=settings.ENCRYPTION_KEK_CIPHERTEXT,
        )
    )


def _json_text(value) -> str | None:
    if value is None:
        return None
    return value if isinstance(value, str) else json.dumps(value)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return

    outreach_rows = list(bind.execute(_SELECT_OUTREACH).mappings())

    op.alter_column(
        "member_next_of_kin",
        "name",
        existing_type=sa.String(length=255),
        type_=sa.Text(),
        existing_nullable=False,
    )
    op.alter_column(
        "member_next_of_kin",
        "phone",
        existing_type=sa.String(length=50),
        type_=sa.Text(),
        existing_nullable=True,
    )
    op.alter_column(
        "member_next_of_kin",
        "email",
        existing_type=sa.String(length=255),
        type_=sa.Text(),
        existing_nullable=True,
    )
    op.alter_column(
        "outreach_records",
        "triage_responses",
        existing_type=sa.JSON(),
        type_=sa.Text(),
        existing_nullable=True,
        postgresql_using="triage_responses::text",
    )
    op.alter_column(
        "outreach_records",
        "triage_scores",
        existing_type=sa.JSON(),
        type_=sa.Text(),
        existing_nullable=True,
        postgresql_using="triage_scores::text",
    )

    from app.core.encryption import encrypt

    _configure_key_provider()

    for row in bind.execute(_SELECT_CASES).mappings():
        bind.execute(
            _UPDATE_CASE,
            {
                "id": row["id"],
                "referral_notes": encrypt(row["referral_notes"], tenant_id=row["tenant_id"]),
            },
        )

    for row in bind.execute(_SELECT_SUBJECTS).mappings():
        bind.execute(
            _UPDATE_SUBJECT,
            {
                "id": row["id"],
                "notes_for_continuity": encrypt(
                    row["notes_for_continuity"], tenant_id=row["tenant_id"]
                ),
            },
        )

    for row in outreach_rows:
        tenant_id = row["tenant_id"]
        bind.execute(
            _UPDATE_OUTREACH,
            {
                "id": row["id"],
                "notes": encrypt(row["notes"], tenant_id=tenant_id),
                "triage_responses": encrypt(
                    _json_text(row["triage_responses"]), tenant_id=tenant_id
                ),
                "triage_scores": encrypt(_json_text(row["triage_scores"]), tenant_id=tenant_id),
            },
        )

    for row in bind.execute(_SELECT_NOK).mappings():
        tenant_id = row["tenant_id"]
        bind.execute(
            _UPDATE_NOK,
            {
                "id": row["id"],
                "name": encrypt(row["name"], tenant_id=tenant_id),
                "phone": encrypt(row["phone"], tenant_id=tenant_id),
                "email": encrypt(row["email"], tenant_id=tenant_id),
            },
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return

    from app.core.encryption import decrypt

    _configure_key_provider()

    for row in bind.execute(_SELECT_CASES).mappings():
        bind.execute(
            _UPDATE_CASE,
            {
                "id": row["id"],
                "referral_notes": decrypt(row["referral_notes"], tenant_id=row["tenant_id"]),
            },
        )

    for row in bind.execute(_SELECT_SUBJECTS).mappings():
        bind.execute(
            _UPDATE_SUBJECT,
            {
                "id": row["id"],
                "notes_for_continuity": decrypt(
                    row["notes_for_continuity"], tenant_id=row["tenant_id"]
                ),
            },
        )

    for row in bind.execute(_SELECT_OUTREACH).mappings():
        tenant_id = row["tenant_id"]
        bind.execute(
            _UPDATE_OUTREACH,
            {
                "id": row["id"],
                "notes": decrypt(row["notes"], tenant_id=tenant_id),
                "triage_responses": decrypt(row["triage_responses"], tenant_id=tenant_id),
                "triage_scores": decrypt(row["triage_scores"], tenant_id=tenant_id),
            },
        )

    for row in bind.execute(_SELECT_NOK).mappings():
        tenant_id = row["tenant_id"]
        bind.execute(
            _UPDATE_NOK,
            {
                "id": row["id"],
                "name": decrypt(row["name"], tenant_id=tenant_id),
                "phone": decrypt(row["phone"], tenant_id=tenant_id),
                "email": decrypt(row["email"], tenant_id=tenant_id),
            },
        )

    op.alter_column(
        "outreach_records",
        "triage_scores",
        existing_type=sa.Text(),
        type_=sa.JSON(),
        existing_nullable=True,
        postgresql_using="triage_scores::json",
    )
    op.alter_column(
        "outreach_records",
        "triage_responses",
        existing_type=sa.Text(),
        type_=sa.JSON(),
        existing_nullable=True,
        postgresql_using="triage_responses::json",
    )
    op.alter_column(
        "member_next_of_kin",
        "email",
        existing_type=sa.Text(),
        type_=sa.String(length=255),
        existing_nullable=True,
    )
    op.alter_column(
        "member_next_of_kin",
        "phone",
        existing_type=sa.Text(),
        type_=sa.String(length=50),
        existing_nullable=True,
    )
    op.alter_column(
        "member_next_of_kin",
        "name",
        existing_type=sa.Text(),
        type_=sa.String(length=255),
        existing_nullable=False,
    )
