"""Encrypt eligible_members.national_id, passport_number, date_of_birth

Revision ID: b4d6f8h0j2l4
Revises: s8u0w2y4a6c8
Create Date: 2026-09-11

Widens the columns to TEXT to hold base64 ciphertext, then encrypts every
existing plaintext value in place under the owning tenant's DEK.

Unlike the original service_sessions encryption migration
(c1d3e5f7b9a2), which could skip a backfill because that table was empty,
`eligible_members` already holds real rows in every environment this has
been tested against. The backfill below is required, not optional: without
it, the application's decrypt() call raises on the first read of any
existing member the moment the mapper change in this same release deploys.

Alembic runs outside the FastAPI lifespan, so nothing has called
set_key_provider() yet when this migration runs. It wires up the same
provider main.py would, from the same settings, so a KMS-backed
ENCRYPTION_KEY_PROVIDER is honoured here exactly as it would be at runtime.
"""

import sqlalchemy as sa

from alembic import op

revision = "b4d6f8h0j2l4"
down_revision = "s8u0w2y4a6c8"
branch_labels = None
depends_on = None

_SELECT_NON_NULL = sa.text(
    "SELECT id, tenant_id, national_id, passport_number, date_of_birth "
    "FROM eligible_members "
    "WHERE national_id IS NOT NULL OR passport_number IS NOT NULL OR date_of_birth IS NOT NULL"
)
_UPDATE_ROW = sa.text(
    "UPDATE eligible_members SET national_id = :national_id, "
    "passport_number = :passport_number, date_of_birth = :date_of_birth WHERE id = :id"
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


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        # SQLite has no ALTER COLUMN; VARCHAR/TEXT/DATE share the same
        # storage class, and this codebase's sqlite test path (if any) does
        # not exercise field-level encryption. Matches c1d3e5f7b9a2.
        return

    op.alter_column(
        "eligible_members",
        "national_id",
        existing_type=sa.String(length=100),
        type_=sa.Text(),
        existing_nullable=True,
    )
    op.alter_column(
        "eligible_members",
        "passport_number",
        existing_type=sa.String(length=100),
        type_=sa.Text(),
        existing_nullable=True,
    )
    op.alter_column(
        "eligible_members",
        "date_of_birth",
        existing_type=sa.Date(),
        type_=sa.Text(),
        existing_nullable=True,
        postgresql_using="date_of_birth::text",
    )

    from app.core.encryption import encrypt

    _configure_key_provider()
    for row in bind.execute(_SELECT_NON_NULL).mappings():
        bind.execute(
            _UPDATE_ROW,
            {
                "id": row["id"],
                "national_id": encrypt(row["national_id"], tenant_id=row["tenant_id"]),
                "passport_number": encrypt(row["passport_number"], tenant_id=row["tenant_id"]),
                "date_of_birth": encrypt(row["date_of_birth"], tenant_id=row["tenant_id"]),
            },
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return

    from app.core.encryption import decrypt

    _configure_key_provider()
    for row in bind.execute(_SELECT_NON_NULL).mappings():
        bind.execute(
            _UPDATE_ROW,
            {
                "id": row["id"],
                "national_id": decrypt(row["national_id"], tenant_id=row["tenant_id"]),
                "passport_number": decrypt(row["passport_number"], tenant_id=row["tenant_id"]),
                "date_of_birth": decrypt(row["date_of_birth"], tenant_id=row["tenant_id"]),
            },
        )

    op.alter_column(
        "eligible_members",
        "date_of_birth",
        existing_type=sa.Text(),
        type_=sa.Date(),
        existing_nullable=True,
        postgresql_using="date_of_birth::date",
    )
    op.alter_column(
        "eligible_members",
        "passport_number",
        existing_type=sa.Text(),
        type_=sa.String(length=100),
        existing_nullable=True,
    )
    op.alter_column(
        "eligible_members",
        "national_id",
        existing_type=sa.Text(),
        type_=sa.String(length=100),
        existing_nullable=True,
    )
