"""Provider network: organisations, affiliations, vocabulary, aliases, imports.

Revision ID: a2n1o0r2k4s6
Revises: a1p2i0d2e4f6

Every tenant-scoped reference is a composite foreign key carrying the tenant
into the parent, so the database rejects a cross-tenant row without relying on
application checks (decision 3). This requires uq_providers_tenant_id, added by
a1p1c0d2e4f6.

All seven tables are new, so there is nothing to backfill and no preflight.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a2n1o0r2k4s6"
down_revision: str | Sequence[str] | None = "a1p2i0d2e4f6"
branch_labels = None
depends_on = None


def _timestamps() -> tuple[sa.Column, sa.Column]:
    """Fresh Column objects per table; a Column cannot be reused across tables."""
    return (
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def upgrade() -> None:
    op.create_table(
        "provider_specialties",
        sa.Column("id", sa.String(25), primary_key=True),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_timestamps(),
        sa.UniqueConstraint("code", name="uq_provider_specialties_code"),
    )
    op.create_index("ix_provider_specialties_is_active", "provider_specialties", ["is_active"])

    op.create_table(
        "provider_organisations",
        sa.Column("id", sa.String(25), primary_key=True),
        sa.Column("tenant_id", sa.String(25), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("registration_number", sa.String(100), nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("contact_phone", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("approval_status", sa.String(50), nullable=False, server_default="Pending"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_provider_organisations_tenant"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_provider_organisations_tenant_name"),
    )
    for column in ("tenant_id", "name", "is_active", "approval_status", "deleted_at"):
        op.create_index(f"ix_provider_organisations_{column}", "provider_organisations", [column])

    op.create_table(
        "provider_affiliations",
        sa.Column("id", sa.String(25), primary_key=True),
        sa.Column("tenant_id", sa.String(25), nullable=False),
        sa.Column("provider_id", sa.String(25), nullable=False),
        sa.Column("organisation_id", sa.String(25), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "provider_id"],
            ["providers.tenant_id", "providers.id"],
            name="fk_provider_affiliations_tenant_provider",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "organisation_id"],
            ["provider_organisations.tenant_id", "provider_organisations.id"],
            name="fk_provider_affiliations_tenant_organisation",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "tenant_id", "id", "provider_id", name="uq_provider_affiliations_tenant_provider"
        ),
    )
    for column in ("tenant_id", "provider_id", "organisation_id", "valid_from", "valid_until"):
        op.create_index(f"ix_provider_affiliations_{column}", "provider_affiliations", [column])

    op.create_table(
        "provider_specialty_links",
        sa.Column("id", sa.String(25), primary_key=True),
        sa.Column("tenant_id", sa.String(25), nullable=False),
        sa.Column("provider_id", sa.String(25), nullable=False),
        sa.Column("specialty_id", sa.String(25), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "provider_id"],
            ["providers.tenant_id", "providers.id"],
            name="fk_provider_specialty_links_tenant_provider",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["specialty_id"], ["provider_specialties.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint(
            "tenant_id",
            "provider_id",
            "specialty_id",
            name="uq_provider_specialty_links_tenant_provider_specialty",
        ),
    )
    for column in ("tenant_id", "provider_id", "specialty_id"):
        op.create_index(
            f"ix_provider_specialty_links_{column}", "provider_specialty_links", [column]
        )

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
        *_timestamps(),
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
        "session_import_batches",
        sa.Column("id", sa.String(25), primary_key=True),
        sa.Column("tenant_id", sa.String(25), nullable=False),
        sa.Column("source_system", sa.String(100), nullable=False),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("file_hash", sa.String(128), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_record_key_field", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="Staged"),
        sa.Column("staged_by", sa.String(25), nullable=False),
        sa.Column("applied_by", sa.String(25), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_session_import_batches_tenant"),
        sa.UniqueConstraint(
            "tenant_id", "file_hash", name="uq_session_import_batches_tenant_file_hash"
        ),
    )
    for column in ("tenant_id", "source_system", "file_hash", "status"):
        op.create_index(f"ix_session_import_batches_{column}", "session_import_batches", [column])

    op.create_table(
        "session_import_rows",
        sa.Column("id", sa.String(25), primary_key=True),
        sa.Column("tenant_id", sa.String(25), nullable=False),
        sa.Column("batch_id", sa.String(25), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("replay_key", sa.String(500), nullable=False),
        sa.Column("source_record_key", sa.String(255), nullable=True),
        sa.Column("raw_practitioner_name", sa.String(500), nullable=True),
        sa.Column("session_date", sa.Date(), nullable=True),
        sa.Column("outcome", sa.String(50), nullable=False),
        sa.Column("delivery_context", sa.String(50), nullable=False, server_default="Unknown"),
        sa.Column("provider_id", sa.String(25), nullable=True),
        sa.Column("provider_affiliation_id", sa.String(25), nullable=True),
        sa.Column("reasons", sa.JSON(), nullable=True),
        sa.Column("imported_session_id", sa.String(25), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "batch_id"],
            ["session_import_batches.tenant_id", "session_import_batches.id"],
            name="fk_session_import_rows_tenant_batch",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "provider_id"],
            ["providers.tenant_id", "providers.id"],
            name="fk_session_import_rows_tenant_provider",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "provider_affiliation_id", "provider_id"],
            [
                "provider_affiliations.tenant_id",
                "provider_affiliations.id",
                "provider_affiliations.provider_id",
            ],
            name="fk_session_import_rows_tenant_affiliation_provider",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["imported_session_id"], ["service_sessions.id"], ondelete="SET NULL"
        ),
        sa.UniqueConstraint(
            "batch_id", "row_number", name="uq_session_import_rows_batch_row_number"
        ),
        sa.UniqueConstraint("tenant_id", "replay_key", name="uq_session_import_rows_tenant_replay"),
    )
    for column in (
        "tenant_id",
        "batch_id",
        "replay_key",
        "outcome",
        "delivery_context",
        "provider_id",
    ):
        op.create_index(f"ix_session_import_rows_{column}", "session_import_rows", [column])


def downgrade() -> None:
    for table in (
        "session_import_rows",
        "session_import_batches",
        "provider_aliases",
        "provider_specialty_links",
        "provider_affiliations",
        "provider_organisations",
        "provider_specialties",
    ):
        op.drop_table(table)
