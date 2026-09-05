"""Add restricted one-to-many member next-of-kin contacts.

Revision ID: g1h3j5l7n9p1
Revises: f0g2i4k6m8o0
Create Date: 2026-09-05

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision = "g1h3j5l7n9p1"
down_revision: str | Sequence[str] | None = "f0g2i4k6m8o0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "member_next_of_kin",
        sa.Column("id", sa.String(length=25), nullable=False),
        sa.Column("tenant_id", sa.String(length=25), nullable=False),
        sa.Column("member_id", sa.String(length=25), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("relationship", sa.String(length=20), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["member_id"], ["eligible_members.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_member_next_of_kin_tenant_id", "member_next_of_kin", ["tenant_id"]
    )
    op.create_index(
        "ix_member_next_of_kin_member_id", "member_next_of_kin", ["member_id"]
    )
    op.create_index(
        "ix_member_next_of_kin_is_primary", "member_next_of_kin", ["is_primary"]
    )


def downgrade() -> None:
    op.drop_index("ix_member_next_of_kin_is_primary", table_name="member_next_of_kin")
    op.drop_index("ix_member_next_of_kin_member_id", table_name="member_next_of_kin")
    op.drop_index("ix_member_next_of_kin_tenant_id", table_name="member_next_of_kin")
    op.drop_table("member_next_of_kin")
