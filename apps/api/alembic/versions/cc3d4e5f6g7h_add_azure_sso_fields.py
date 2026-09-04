"""Add Azure AD SSO fields to tenants and users

Revision ID: cc3d4e5f6g7h
Revises: aa1b2c3d4e5f
Create Date: 2026-05-11

tenants:
  azure_tenant_id   VARCHAR(36) NULLABLE UNIQUE: employer's Azure AD directory ID (tid claim)
  azure_sso_enabled BOOLEAN NOT NULL DEFAULT FALSE

users:
  azure_oid       VARCHAR(36) NULLABLE: Azure Object ID (oid claim); unique per (oid, tenant_id)
  auth_provider   VARCHAR(20) NOT NULL DEFAULT 'password': 'password' | 'azure_ad'
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "cc3d4e5f6g7h"
down_revision: Union[str, Sequence[str], None] = "aa1b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # tenants: Azure SSO config
    op.add_column(
        "tenants",
        sa.Column("azure_tenant_id", sa.String(length=36), nullable=True),
    )
    op.add_column(
        "tenants",
        sa.Column(
            "azure_sso_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.create_index(
        "ix_tenants_azure_tenant_id",
        "tenants",
        ["azure_tenant_id"],
        unique=True,
    )

    # users: Azure identity linkage
    op.add_column(
        "users",
        sa.Column("azure_oid", sa.String(length=36), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "auth_provider",
            sa.String(length=20),
            nullable=False,
            server_default="password",
        ),
    )
    op.create_index("ix_users_azure_oid", "users", ["azure_oid"])
    op.create_check_constraint(
        "user_auth_provider_check",
        "users",
        "auth_provider IN ('password', 'azure_ad')",
    )


def downgrade() -> None:
    op.drop_constraint("user_auth_provider_check", "users", type_="check")
    op.drop_index("ix_users_azure_oid", table_name="users")
    op.drop_column("users", "auth_provider")
    op.drop_column("users", "azure_oid")

    op.drop_index("ix_tenants_azure_tenant_id", table_name="tenants")
    op.drop_column("tenants", "azure_sso_enabled")
    op.drop_column("tenants", "azure_tenant_id")
