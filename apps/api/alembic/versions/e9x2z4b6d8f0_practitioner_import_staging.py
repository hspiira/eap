"""Practitioner workbook import staging tables

Review-first staging for the practitioners and organisations workbook. Rows
carry their sheet name because the two practitioner sheets share row numbers,
and the tenant/replay-key uniqueness makes replaying the same file safe.
Unmodelled source columns live verbatim in the provenance JSON.

Revision ID: e9x2z4b6d8f0
Revises: d8w1y3a5c7e9
Create Date: 2026-09-07

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e9x2z4b6d8f0"
down_revision: str | Sequence[str] | None = "d8w1y3a5c7e9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> tuple[sa.Column, sa.Column]:
    return (
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def upgrade() -> None:
    op.create_table(
        "practitioner_import_batches",
        sa.Column("id", sa.String(25), primary_key=True),
        sa.Column("tenant_id", sa.String(25), nullable=False),
        sa.Column("source_system", sa.String(100), nullable=False),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("file_hash", sa.String(128), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(50), nullable=False, server_default="Staged"),
        sa.Column("staged_by", sa.String(25), nullable=False),
        sa.Column("applied_by", sa.String(25), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_practitioner_import_batches_tenant"),
        sa.UniqueConstraint(
            "tenant_id", "file_hash", name="uq_practitioner_import_batches_tenant_file_hash"
        ),
    )
    for column in ("tenant_id", "source_system", "file_hash", "status"):
        op.create_index(
            f"ix_practitioner_import_batches_{column}", "practitioner_import_batches", [column]
        )

    op.create_table(
        "practitioner_import_rows",
        sa.Column("id", sa.String(25), primary_key=True),
        sa.Column("tenant_id", sa.String(25), nullable=False),
        sa.Column("batch_id", sa.String(25), nullable=False),
        sa.Column("sheet_name", sa.String(100), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("replay_key", sa.String(500), nullable=False),
        sa.Column("raw_name", sa.String(500), nullable=True),
        sa.Column("normalized_name", sa.String(500), nullable=True),
        sa.Column("organisation_name", sa.String(500), nullable=True),
        sa.Column("raw_profession", sa.String(500), nullable=True),
        sa.Column("mapped_profession", sa.String(255), nullable=True),
        sa.Column("contact_email", sa.String(500), nullable=True),
        sa.Column("outcome", sa.String(50), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=True),
        sa.Column("provenance", sa.JSON(), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "batch_id"],
            ["practitioner_import_batches.tenant_id", "practitioner_import_batches.id"],
            name="fk_practitioner_import_rows_tenant_batch",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "batch_id",
            "sheet_name",
            "row_number",
            name="uq_practitioner_import_rows_batch_sheet_row",
        ),
        sa.UniqueConstraint(
            "tenant_id", "replay_key", name="uq_practitioner_import_rows_tenant_replay"
        ),
    )
    for column in ("tenant_id", "batch_id", "replay_key", "normalized_name", "outcome"):
        op.create_index(
            f"ix_practitioner_import_rows_{column}", "practitioner_import_rows", [column]
        )


def downgrade() -> None:
    op.drop_table("practitioner_import_rows")
    op.drop_table("practitioner_import_batches")
