"""Add durable background client import jobs."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision = "c7d9e1f3a5b7"
down_revision = "b6c8d0e2f4a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "client_import_jobs",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False),
        sa.Column("requested_by", sa.String(length=25), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("file_content", sa.LargeBinary(), nullable=False),
        sa.Column("decisions", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("imported", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("issues", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.String(length=1000), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_client_import_jobs_tenant_id", "client_import_jobs", ["tenant_id"])
    op.create_index("ix_client_import_jobs_requested_by", "client_import_jobs", ["requested_by"])
    op.create_index("ix_client_import_jobs_status", "client_import_jobs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_client_import_jobs_status", table_name="client_import_jobs")
    op.drop_index("ix_client_import_jobs_requested_by", table_name="client_import_jobs")
    op.drop_index("ix_client_import_jobs_tenant_id", table_name="client_import_jobs")
    op.drop_table("client_import_jobs")
