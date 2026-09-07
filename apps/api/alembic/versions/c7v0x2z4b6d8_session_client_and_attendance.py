"""Attribute a session to a client, and allow it to have no member

Company-wide sessions, health talks and site visits, are delivered to a client
with nobody individual to name. `member_id` was NOT NULL, so they could not be
recorded at all. The client becomes what a session is always attributed to and
the member becomes what it sometimes has, with `attendance` stating which kind
a session is rather than leaving it to be inferred from a null member.

Backfilling the client is safe because `member_id` is NOT NULL when this runs,
so every existing row resolves one.

Revision ID: c7v0x2z4b6d8
Revises: a1p3d0d2e4f6
Create Date: 2026-09-07

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c7v0x2z4b6d8"
down_revision: str | Sequence[str] | None = "a1p3d0d2e4f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("service_sessions", sa.Column("client_id", sa.String(length=25), nullable=True))
    op.add_column("service_sessions", sa.Column("attendance", sa.String(length=32), nullable=True))

    op.execute(
        """
        UPDATE service_sessions AS s
        SET client_id = m.client_id
        FROM eligible_members AS m
        WHERE m.id = s.member_id AND m.tenant_id = s.tenant_id
        """
    )
    op.execute("UPDATE service_sessions SET attendance = 'Individual'")

    op.alter_column("service_sessions", "client_id", nullable=False)
    op.alter_column("service_sessions", "attendance", nullable=False)
    op.alter_column("service_sessions", "member_id", nullable=True)

    op.create_index("ix_service_sessions_client_id", "service_sessions", ["client_id"])
    op.create_index("ix_service_sessions_attendance", "service_sessions", ["attendance"])

    # Supersets of each primary key, so they add no constraint of their own.
    # They exist so the composite foreign keys below can be declared, the way
    # uq_providers_tenant_id already lets a session point at a provider.
    op.create_unique_constraint("uq_clients_tenant_id", "clients", ["tenant_id", "id"])
    op.create_unique_constraint(
        "uq_eligible_member_tenant_client_id",
        "eligible_members",
        ["tenant_id", "client_id", "id"],
    )

    op.create_foreign_key(
        "fk_service_sessions_client_tenant",
        "service_sessions",
        "clients",
        ["tenant_id", "client_id"],
        ["tenant_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_service_sessions_member_client_tenant",
        "service_sessions",
        "eligible_members",
        ["tenant_id", "client_id", "member_id"],
        ["tenant_id", "client_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_check_constraint(
        "session_attendance_check",
        "service_sessions",
        "attendance IN ('Individual', 'CompanyWide')",
    )
    op.create_check_constraint(
        "session_attendance_matches_member_check",
        "service_sessions",
        "(attendance = 'CompanyWide') = (member_id IS NULL)",
    )

    op.drop_constraint("session_clinical_outcome_check", "service_sessions", type_="check")
    op.create_check_constraint(
        "session_clinical_outcome_check",
        "service_sessions",
        "clinical_outcome IS NULL OR clinical_outcome IN "
        "('ToBeContinued', 'Referred', 'Completed', 'Terminated')",
    )


def downgrade() -> None:
    # The old schema cannot hold a company-wide session: member_id was NOT NULL
    # and there is no other column recording the client. Dropping these columns
    # would destroy the only record of those sessions, so refuse instead.
    count = (
        op.get_bind()
        .execute(sa.text("SELECT count(*) FROM service_sessions WHERE member_id IS NULL"))
        .scalar()
    )
    if count:
        raise RuntimeError(
            f"{count} company-wide sessions have no member and cannot be represented "
            "by the previous schema. Reassign or delete them before downgrading."
        )
    terminated = (
        op.get_bind()
        .execute(
            sa.text("SELECT count(*) FROM service_sessions WHERE clinical_outcome = 'Terminated'")
        )
        .scalar()
    )
    if terminated:
        raise RuntimeError(
            f"{terminated} sessions record the Terminated outcome, which the previous "
            "check constraint rejects. Change them before downgrading."
        )

    op.drop_constraint("session_clinical_outcome_check", "service_sessions", type_="check")
    op.create_check_constraint(
        "session_clinical_outcome_check",
        "service_sessions",
        "clinical_outcome IS NULL OR clinical_outcome IN ('ToBeContinued', 'Referred', 'Completed')",
    )
    op.drop_constraint("session_attendance_matches_member_check", "service_sessions", type_="check")
    op.drop_constraint("session_attendance_check", "service_sessions", type_="check")
    op.drop_constraint(
        "fk_service_sessions_member_client_tenant", "service_sessions", type_="foreignkey"
    )
    op.drop_constraint("fk_service_sessions_client_tenant", "service_sessions", type_="foreignkey")
    op.drop_constraint("uq_eligible_member_tenant_client_id", "eligible_members", type_="unique")
    op.drop_constraint("uq_clients_tenant_id", "clients", type_="unique")
    op.drop_index("ix_service_sessions_attendance", table_name="service_sessions")
    op.drop_index("ix_service_sessions_client_id", table_name="service_sessions")
    op.alter_column("service_sessions", "member_id", nullable=False)
    op.drop_column("service_sessions", "attendance")
    op.drop_column("service_sessions", "client_id")
