"""Add critical_incidents table (Phase 2 #D-CISM)

Revision ID: g5b7c9d2e4f6
Revises: f4a6b8c1d3e5
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op



revision: str = "g5b7c9d2e4f6"
down_revision: Union[str, Sequence[str], None] = "f4a6b8c1d3e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "critical_incidents",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("client_id", sa.String(length=25), nullable=False, index=True),
        sa.Column("event_description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False, index=True),
        sa.Column("affected_population_size", sa.Integer(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("logged_by", sa.String(length=25), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="Open", index=True),
        sa.Column("phases", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("after_action_summary", sa.Text(), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
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

    op.add_column(
        "service_sessions",
        sa.Column("incident_id", sa.String(length=25), nullable=True, index=True),
    )
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        op.create_foreign_key(
            "fk_service_sessions_incident",
            "service_sessions",
            "critical_incidents",
            ["incident_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        op.drop_constraint(
            "fk_service_sessions_incident", "service_sessions", type_="foreignkey"
        )
    op.drop_column("service_sessions", "incident_id")
    op.drop_table("critical_incidents")
