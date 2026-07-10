"""Add outbox_events table (Phase 1 #C10)

Revision ID: d2e4f6a8b1c3
Revises: c1d3e5f7b9a2
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "d2e4f6a8b1c3"
down_revision: Union[str, Sequence[str], None] = "c1d3e5f7b9a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "outbox_events",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("event_type", sa.String(length=100), nullable=False, index=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("aggregate_type", sa.String(length=100), nullable=True),
        sa.Column("aggregate_id", sa.String(length=25), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column(
            "delivery_attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True, index=True),
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
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.create_index(
            "ix_outbox_events_undelivered",
            "outbox_events",
            ["delivered_at", "created_at"],
            postgresql_where=sa.text("delivered_at IS NULL"),
        )
    else:
        op.create_index(
            "ix_outbox_events_undelivered",
            "outbox_events",
            ["delivered_at", "created_at"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.drop_index("ix_outbox_events_undelivered", table_name="outbox_events")
    else:
        op.drop_index("ix_outbox_events_undelivered", table_name="outbox_events")
    op.drop_table("outbox_events")
