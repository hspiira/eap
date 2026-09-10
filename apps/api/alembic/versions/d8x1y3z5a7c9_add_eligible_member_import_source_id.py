"""Add eligible_members.import_source_id

Revision ID: d8x1y3z5a7c9
Revises: c3f7a9e1d5b2
Create Date: 2026-09-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "d8x1y3z5a7c9"
down_revision: Union[str, Sequence[str], None] = "c3f7a9e1d5b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "eligible_members",
        sa.Column("import_source_id", sa.String(length=255), nullable=True),
    )
    op.create_index(
        "ix_eligible_members_import_source_id",
        "eligible_members",
        ["import_source_id"],
    )
    op.create_unique_constraint(
        "uq_eligible_member_import_source_per_client",
        "eligible_members",
        ["tenant_id", "client_id", "import_source_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_eligible_member_import_source_per_client",
        "eligible_members",
        type_="unique",
    )
    op.drop_index("ix_eligible_members_import_source_id", table_name="eligible_members")
    op.drop_column("eligible_members", "import_source_id")
