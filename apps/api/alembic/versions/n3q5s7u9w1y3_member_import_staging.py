"""Member roster import staging batch and rows

Persists what a roster upload already decides in memory, so an import attempt
is auditable and a batch's rows can be reviewed and applied without the
browser holding the parsed file between preview and commit. See
docs/migrations/MEMBERS_MIGRATION.md, "Design: member import staging batch".

Only a batch still awaiting a decision holds its file hash: this starts with
the partial unique index directly, rather than the plain per-tenant unique
constraint session import shipped first and needed two follow-up migrations
to correct (see h3b5d7f9j1l3 and j5d7f9h1k3m5).

Revision ID: n3q5s7u9w1y3
Revises: d8x1y3z5a7c9
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "n3q5s7u9w1y3"
down_revision: str | Sequence[str] | None = "d8x1y3z5a7c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> tuple[sa.Column, sa.Column]:
    return (
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )


def upgrade() -> None:
    op.create_table(
        "member_import_batches",
        sa.Column("id", sa.String(25), primary_key=True),
        sa.Column("tenant_id", sa.String(25), nullable=False),
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
        sa.UniqueConstraint("tenant_id", "id", name="uq_member_import_batches_tenant"),
    )
    for column in ("tenant_id", "file_hash", "status"):
        op.create_index(f"ix_member_import_batches_{column}", "member_import_batches", [column])
    op.create_index(
        "uq_member_import_batches_tenant_file_hash",
        "member_import_batches",
        ["tenant_id", "file_hash"],
        unique=True,
        postgresql_where=sa.text("status = 'Staged'"),
    )

    op.create_table(
        "member_import_rows",
        sa.Column("id", sa.String(25), primary_key=True),
        sa.Column("tenant_id", sa.String(25), nullable=False),
        sa.Column("batch_id", sa.String(25), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("replay_key", sa.String(500), nullable=False),
        sa.Column("client_code", sa.String(100), nullable=True),
        sa.Column("client_id", sa.String(25), nullable=True),
        sa.Column("import_source_id", sa.String(255), nullable=True),
        sa.Column("staff_number", sa.String(100), nullable=True),
        sa.Column("display_label", sa.String(255), nullable=True),
        sa.Column("work_email", sa.String(255), nullable=True),
        sa.Column("personal_email", sa.String(255), nullable=True),
        sa.Column("gender", sa.String(50), nullable=True),
        sa.Column("date_of_birth", sa.String(20), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("national_id", sa.String(100), nullable=True),
        sa.Column("passport_number", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("relation", sa.String(50), nullable=True),
        sa.Column("primary_import_source_id", sa.String(255), nullable=True),
        sa.Column("outcome", sa.String(20), nullable=False),
        sa.Column("decision", sa.String(10), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("imported_member_id", sa.String(25), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "batch_id"],
            ["member_import_batches.tenant_id", "member_import_batches.id"],
            name="fk_member_import_rows_tenant_batch",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["imported_member_id"], ["eligible_members.id"], ondelete="SET NULL"
        ),
        sa.UniqueConstraint("batch_id", "row_number", name="uq_member_import_rows_batch_row"),
        sa.UniqueConstraint("tenant_id", "replay_key", name="uq_member_import_rows_tenant_replay"),
    )
    for column in ("tenant_id", "batch_id", "replay_key", "outcome", "client_id"):
        op.create_index(f"ix_member_import_rows_{column}", "member_import_rows", [column])


def downgrade() -> None:
    op.drop_table("member_import_rows")
    op.drop_index("uq_member_import_batches_tenant_file_hash", table_name="member_import_batches")
    op.drop_table("member_import_batches")
