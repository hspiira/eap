"""Add password_set_tokens table for set-initial-password flow

Revision ID: a1b2c3d4e5f6
Revises: 7c8d9e0b1f2a
Create Date: 2026-02-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "7c8d9e0b1f2a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "password_set_tokens",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=25), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_password_set_tokens_token_hash",
        "password_set_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "ix_password_set_tokens_user_id",
        "password_set_tokens",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_password_set_tokens_user_id",
        table_name="password_set_tokens",
    )
    op.drop_index(
        "ix_password_set_tokens_token_hash",
        table_name="password_set_tokens",
    )
    op.drop_table("password_set_tokens")
