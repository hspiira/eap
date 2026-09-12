"""Link a session to the one it follows

Revision ID: t0v2x4z6b8d0
Revises: g3i5k7m9o1q3
Create Date: 2026-09-12

Decision 7 in docs/design/REALTIME_SESSION_CAPTURE.md.

`follow_up_of_session_id` carries the scheduling fact that one booking was made
off the back of another. It is a self-reference and not a link to a case on
purpose: a session holds an employer-side member id and a case is keyed on a
pseudonymous subject, so joining them would build the bridge
`docs/migrations/SERVICES_MIGRATION.md:289` rejects. Both ends of this link are
employer-side, so it creates no such bridge and a scheduler without clinical
scope can still follow the chain.

`ON DELETE SET NULL`, matching the other optional references on this table: a
deleted session must not take its successor with it, only the pointer.

Reversing this drops the link. It is not recoverable from the remaining data:
nothing else records which booking was made off the back of which.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "t0v2x4z6b8d0"
down_revision: str | Sequence[str] | None = "g3i5k7m9o1q3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "service_sessions",
        sa.Column("follow_up_of_session_id", sa.String(25), nullable=True),
    )
    op.create_foreign_key(
        "fk_service_sessions_follow_up_of",
        "service_sessions",
        "service_sessions",
        ["follow_up_of_session_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_service_sessions_follow_up_of",
        "service_sessions",
        ["follow_up_of_session_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_service_sessions_follow_up_of", table_name="service_sessions")
    op.drop_constraint(
        "fk_service_sessions_follow_up_of", "service_sessions", type_="foreignkey"
    )
    op.drop_column("service_sessions", "follow_up_of_session_id")
