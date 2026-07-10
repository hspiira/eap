"""Add contract pricing + utilisation_events (Phase 2 #D-Pricing)

Revision ID: j8e1f3a5c7d9
Revises: i7d9e3f5a8b2
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "j8e1f3a5c7d9"
down_revision: Union[str, Sequence[str], None] = "i7d9e3f5a8b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "contracts",
        sa.Column("pricing_model", sa.String(length=40), nullable=True, index=True),
    )
    op.add_column(
        "contracts",
        sa.Column("pricing_config", sa.JSON(), nullable=True),
    )

    op.create_table(
        "utilisation_events",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("contract_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("event_type", sa.String(length=40), nullable=False, index=True),
        sa.Column("occurred_on", sa.Date(), nullable=False, index=True),
        sa.Column("units", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("service_code", sa.String(length=50), nullable=True, index=True),
        sa.Column("source_id", sa.String(length=25), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("utilisation_events")
    op.drop_column("contracts", "pricing_config")
    op.drop_column("contracts", "pricing_model")
