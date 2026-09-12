"""Drop the practitioner and diagnosis alias tables

Revision ID: g3i5k7m9o1q3
Revises: f2h4j6l8n0p2
Create Date: 2026-09-12

Both tables existed to absorb one Excel export's spellings, and both are now
resolved against the canonical record instead: a practitioner by the normalised
display name, a diagnosis by the normalised taxonomy name. Nothing reads either
table.

`client_aliases` is deliberately untouched. A client genuinely trades under
more than one name, a person maintains that list on the client page, and it is
a fact about the client rather than an artefact of a spreadsheet.

Downgrade recreates both tables empty. The decisions they held are not
recoverable from here, which is why the upgrade refuses to run silently: it
reports the row counts it is about to destroy.
"""

import sqlalchemy as sa

from alembic import op

revision = "g3i5k7m9o1q3"
down_revision = "f2h4j6l8n0p2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    for table in ("provider_aliases", "diagnosis_aliases"):
        if not _exists(connection, table):
            continue
        count = connection.execute(sa.text(f"SELECT count(*) FROM {table}")).scalar_one()
        print(f"dropping {table} with {count} row(s)")
        op.drop_table(table)


def downgrade() -> None:
    """Recreate both shapes exactly, empty. The decisions themselves are gone.

    Faithful to the last state before the drop, constraint names included: a
    later downgrade in the chain drops `diagnosis_alias_confidence_check` by
    name and fails if this leaves it out.
    """
    op.create_table(
        "provider_aliases",
        sa.Column("id", sa.String(25), primary_key=True),
        sa.Column("tenant_id", sa.String(25), nullable=False),
        sa.Column("source_system", sa.String(100), nullable=False),
        sa.Column("source_value", sa.String(500), nullable=False),
        sa.Column("normalized_value", sa.String(500), nullable=False),
        sa.Column("state", sa.String(50), nullable=False, server_default="Unmapped"),
        sa.Column("provider_id", sa.String(25), nullable=True),
        sa.Column("candidate_provider_ids", sa.JSON(), nullable=True),
        sa.Column("resolved_by", sa.String(25), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "provider_id"],
            ["providers.tenant_id", "providers.id"],
            name="fk_provider_aliases_tenant_provider",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "source_system",
            "normalized_value",
            name="uq_provider_aliases_tenant_source_normalized",
        ),
    )
    for column in ("tenant_id", "source_system", "normalized_value", "state", "provider_id"):
        op.create_index(f"ix_provider_aliases_{column}", "provider_aliases", [column])

    op.create_table(
        "diagnosis_aliases",
        sa.Column("id", sa.String(25), primary_key=True),
        sa.Column("raw_value", sa.Text(), nullable=False),
        sa.Column("normalised_key", sa.String(255), nullable=False),
        sa.Column(
            "diagnosis_type_id",
            sa.String(25),
            sa.ForeignKey("diagnosis_types.id"),
            nullable=False,
        ),
        sa.Column("diagnosis_id", sa.String(25), sa.ForeignKey("diagnoses.id"), nullable=True),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("confidence", sa.String(20), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "confidence IN ('confirmed', 'inferred', 'rejected')",
            name="diagnosis_alias_confidence_check",
        ),
    )
    op.create_index(
        "ix_diagnosis_aliases_normalised_key",
        "diagnosis_aliases",
        ["normalised_key"],
        unique=True,
    )
    op.create_index(
        "ix_diagnosis_aliases_diagnosis_type_id", "diagnosis_aliases", ["diagnosis_type_id"]
    )
    op.create_index("ix_diagnosis_aliases_diagnosis_id", "diagnosis_aliases", ["diagnosis_id"])


def _exists(connection, table: str) -> bool:
    return sa.inspect(connection).has_table(table)
