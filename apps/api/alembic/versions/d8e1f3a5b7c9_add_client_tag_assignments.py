"""Add persisted client tag assignments."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision = "d8e1f3a5b7c9"
down_revision = "c7d9e1f3a5b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "client_tag_assignments",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False),
        sa.Column("client_id", sa.String(length=25), nullable=False),
        sa.Column("tag_id", sa.String(length=25), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["client_tags.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_client_tag_assignments_tenant_id", "client_tag_assignments", ["tenant_id"])
    op.create_index("ix_client_tag_assignments_client_id", "client_tag_assignments", ["client_id"])
    op.create_index("ix_client_tag_assignments_tag_id", "client_tag_assignments", ["tag_id"])
    op.create_index(
        "uq_client_tag_assignments_client_tag",
        "client_tag_assignments",
        ["tenant_id", "client_id", "tag_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_client_tag_assignments_client_tag", table_name="client_tag_assignments")
    op.drop_index("ix_client_tag_assignments_tag_id", table_name="client_tag_assignments")
    op.drop_index("ix_client_tag_assignments_client_id", table_name="client_tag_assignments")
    op.drop_index("ix_client_tag_assignments_tenant_id", table_name="client_tag_assignments")
    op.drop_table("client_tag_assignments")
