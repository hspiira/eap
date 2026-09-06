"""Record how each session was delivered, and by whose arrangement.

Revision ID: a1p3d0d2e4f6
Revises: a2n1o0r2k4s6

Existing rows become Unknown. Decision 2 forbids inferring direct contracting
from an absent organisation, so a row whose source says nothing says Unknown.

The affiliation reference is composite on (tenant_id, provider_affiliation_id,
provider_id), so a session can only cite an affiliation belonging to its own
tenant and its own practitioner. A check constraint keeps the context and the
reference consistent in both directions: organisation delivery has one, direct
and unknown delivery do not.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a1p3d0d2e4f6"
down_revision: str | Sequence[str] | None = "a2n1o0r2k4s6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "service_sessions",
        sa.Column("delivery_context", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "service_sessions",
        sa.Column("provider_affiliation_id", sa.String(length=25), nullable=True),
    )
    op.execute("UPDATE service_sessions SET delivery_context = 'Unknown'")
    op.alter_column("service_sessions", "delivery_context", nullable=False)

    op.create_check_constraint(
        "session_delivery_context_check",
        "service_sessions",
        "delivery_context IN ('Direct', 'Organisation', 'Unknown')",
    )
    op.create_check_constraint(
        "session_affiliation_matches_context_check",
        "service_sessions",
        "(delivery_context = 'Organisation') = (provider_affiliation_id IS NOT NULL)",
    )
    op.create_foreign_key(
        "fk_service_sessions_affiliation_tenant_provider",
        "service_sessions",
        "provider_affiliations",
        ["tenant_id", "provider_affiliation_id", "provider_id"],
        ["tenant_id", "id", "provider_id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_service_sessions_affiliation",
        "service_sessions",
        ["provider_affiliation_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_service_sessions_affiliation", table_name="service_sessions")
    op.drop_constraint(
        "fk_service_sessions_affiliation_tenant_provider",
        "service_sessions",
        type_="foreignkey",
    )
    op.drop_constraint(
        "session_affiliation_matches_context_check", "service_sessions", type_="check"
    )
    op.drop_constraint("session_delivery_context_check", "service_sessions", type_="check")
    op.drop_column("service_sessions", "provider_affiliation_id")
    op.drop_column("service_sessions", "delivery_context")
