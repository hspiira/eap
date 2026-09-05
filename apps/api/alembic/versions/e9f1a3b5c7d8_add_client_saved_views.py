"""Add shareable client saved views."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision = "e9f1a3b5c7d8"
down_revision = "d8e1f3a5b7c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "client_saved_views",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("filters", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(length=25), nullable=False),
        sa.Column("is_shared", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_client_saved_views_tenant_created_by",
        "client_saved_views",
        ["tenant_id", "created_by"],
    )
    op.create_index(
        "ix_client_saved_views_tenant_shared",
        "client_saved_views",
        ["tenant_id", "is_shared"],
    )
    op.create_index(
        "ix_client_saved_views_created_by", "client_saved_views", ["created_by"]
    )
    op.create_index("ix_client_saved_views_is_shared", "client_saved_views", ["is_shared"])


def downgrade() -> None:
    op.drop_index("ix_client_saved_views_is_shared", table_name="client_saved_views")
    op.drop_index("ix_client_saved_views_created_by", table_name="client_saved_views")
    op.drop_index("ix_client_saved_views_tenant_shared", table_name="client_saved_views")
    op.drop_index("ix_client_saved_views_tenant_created_by", table_name="client_saved_views")
    op.drop_table("client_saved_views")
