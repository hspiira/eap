"""Add display_name to users

Revision ID: f9e8d7c6b5a4
Revises: z4u7v9w1q3s6
Create Date: 2026-07-10

users:
  display_name  VARCHAR(255) NULLABLE — display name sourced from the identity
                provider (Azure AD 'name' claim). Null for password-only users.
                Refreshed on every SSO login so it stays in sync with the IdP.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f9e8d7c6b5a4"
down_revision: Union[str, Sequence[str], None] = "cc3d4e5f6g7h"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("display_name", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "display_name")
