"""Use Members as service-session subjects on a clean installation."""

import sqlalchemy as sa

from alembic import op

revision = "a7c9e1f3b5d7"
down_revision = "f2c4a6b8d0e1"
branch_labels = None
depends_on = None


def _require_empty_sessions() -> None:
    if op.get_bind().execute(sa.text("SELECT EXISTS (SELECT 1 FROM service_sessions)")).scalar():
        raise RuntimeError(
            "Service-session subject migration requires an empty service_sessions table"
        )


def upgrade() -> None:
    _require_empty_sessions()
    op.drop_constraint("service_sessions_person_id_fkey", "service_sessions", type_="foreignkey")
    op.drop_index("ix_service_sessions_person_id", table_name="service_sessions")
    op.alter_column("service_sessions", "person_id", new_column_name="member_id")
    op.create_foreign_key(
        "service_sessions_member_id_fkey",
        "service_sessions",
        "eligible_members",
        ["member_id"],
        ["id"],
    )
    op.create_index("ix_service_sessions_member_id", "service_sessions", ["member_id"])


def downgrade() -> None:
    _require_empty_sessions()
    op.drop_constraint("service_sessions_member_id_fkey", "service_sessions", type_="foreignkey")
    op.drop_index("ix_service_sessions_member_id", table_name="service_sessions")
    op.alter_column("service_sessions", "member_id", new_column_name="person_id")
    op.create_foreign_key(
        "service_sessions_person_id_fkey", "service_sessions", "persons", ["person_id"], ["id"]
    )
    op.create_index("ix_service_sessions_person_id", "service_sessions", ["person_id"])
