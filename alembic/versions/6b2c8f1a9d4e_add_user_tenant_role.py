"""Add user tenant role (RBAC)

Revision ID: 6b2c8f1a9d4e
Revises: 51a3ca5e6e38
Create Date: 2026-02-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6b2c8f1a9d4e"
down_revision: Union[str, Sequence[str], None] = "51a3ca5e6e38"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add role column to users for tenant RBAC (Admin, User, Viewer)."""
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=20), nullable=False, server_default="User"),
    )
    op.create_check_constraint(
        "user_role_check",
        "users",
        "role IN ('Admin', 'User', 'Viewer')",
    )


def downgrade() -> None:
    """Remove role column from users."""
    op.drop_constraint("user_role_check", "users", type_="check")
    op.drop_column("users", "role")
