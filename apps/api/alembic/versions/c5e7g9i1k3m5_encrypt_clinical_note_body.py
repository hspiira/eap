"""Encrypt clinical_notes.body and .amendments

Revision ID: c5e7g9i1k3m5
Revises: b4d6f8h0j2l4
Create Date: 2026-09-11

Widens body/amendments from JSON to TEXT to hold base64 ciphertext of the
JSON-serialised value, then encrypts every existing row in place under the
owning tenant's DEK. See b4d6f8h0j2l4 for why the backfill is required
rather than optional: this table's model docstring already claimed "body
fields are encrypted at rest" before any code implemented that, and this
migration is what makes the claim true for rows written before this
release, not only ones written after it.

No SQL ever queries into these JSON columns by path (confirmed before
writing this migration), so nothing downstream depends on the column
staying JSON-queryable.
"""

import sqlalchemy as sa

from alembic import op

revision = "c5e7g9i1k3m5"
down_revision = "b4d6f8h0j2l4"
branch_labels = None
depends_on = None

_SELECT_ROWS = sa.text("SELECT id, tenant_id, body, amendments FROM clinical_notes")
_UPDATE_ROW = sa.text(
    "UPDATE clinical_notes SET body = :body, amendments = :amendments WHERE id = :id"
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
        return

    import json

    from app.core.encryption import encrypt

    _configure_key_provider()
    rows = list(bind.execute(_SELECT_ROWS).mappings())

    op.alter_column(
        "clinical_notes",
        "body",
        existing_type=sa.JSON(),
        type_=sa.Text(),
        existing_nullable=False,
        postgresql_using="body::text",
    )
    op.alter_column(
        "clinical_notes",
        "amendments",
        existing_type=sa.JSON(),
        type_=sa.Text(),
        existing_nullable=False,
        server_default=None,
        postgresql_using="amendments::text",
    )

    for row in rows:
        # asyncpg/psycopg already deserialise a JSON column into a Python
        # object; re-serialise it exactly as the mapper would before
        # encrypting, so a row written before or after this migration reads
        # back identically.
        body = row["body"] if isinstance(row["body"], str) else json.dumps(row["body"])
        amendments = row["amendments"] if row["amendments"] is not None else []
        amendments_json = amendments if isinstance(amendments, str) else json.dumps(amendments)
        bind.execute(
            _UPDATE_ROW,
            {
                "id": row["id"],
                "body": encrypt(body, tenant_id=row["tenant_id"]),
                "amendments": encrypt(amendments_json, tenant_id=row["tenant_id"]),
            },
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return

    from app.core.encryption import decrypt

    _configure_key_provider()
    rows = list(bind.execute(_SELECT_ROWS).mappings())
    for row in rows:
        bind.execute(
            _UPDATE_ROW,
            {
                "id": row["id"],
                "body": decrypt(row["body"], tenant_id=row["tenant_id"]),
                "amendments": decrypt(row["amendments"], tenant_id=row["tenant_id"]),
            },
        )

    op.alter_column(
        "clinical_notes",
        "body",
        existing_type=sa.Text(),
        type_=sa.JSON(),
        existing_nullable=False,
        postgresql_using="body::json",
    )
    op.alter_column(
        "clinical_notes",
        "amendments",
        existing_type=sa.Text(),
        type_=sa.JSON(),
        existing_nullable=False,
        server_default=sa.text("'[]'"),
        postgresql_using="amendments::json",
    )
