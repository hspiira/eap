"""Add explicit member to user account links."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c9e1a3b5d7f9"
down_revision: str | Sequence[str] | None = "b8d0f2a4c6e8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("eligible_members", sa.Column("user_id", sa.String(length=25), nullable=True))
    op.create_foreign_key(
        "fk_eligible_members_user_id_users",
        "eligible_members",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_eligible_members_user_id", "eligible_members", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_eligible_members_user_id", table_name="eligible_members")
    op.drop_constraint("fk_eligible_members_user_id_users", "eligible_members", type_="foreignkey")
    op.drop_column("eligible_members", "user_id")
