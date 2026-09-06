"""Create independent provider persistence and move session provider FK."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e5g7i9k1m3o5"
down_revision: str | Sequence[str] | None = "d4f6a8b0c2e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    sessions = bind.execute(sa.text("SELECT count(*) FROM service_sessions")).scalar_one()
    if sessions:
        raise RuntimeError(
            "Provider persistence cutover requires an empty service_sessions table; "
            "map provider IDs before retrying"
        )
    op.create_table(
        "providers",
        sa.Column("id", sa.String(length=25), nullable=False),
        sa.Column("tenant_id", sa.String(length=25), nullable=False),
        sa.Column("user_id", sa.String(length=25), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("license_info", sa.JSON(), nullable=True),
        sa.Column("provider_profile", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_providers_tenant_id", "providers", ["tenant_id"])
    op.create_index("ix_providers_user_id", "providers", ["user_id"])
    op.create_index("ix_providers_deleted_at", "providers", ["deleted_at"])
    op.drop_constraint("service_sessions_provider_id_fkey", "service_sessions", type_="foreignkey")
    op.create_foreign_key(
        "fk_service_sessions_provider_id_providers",
        "service_sessions",
        "providers",
        ["provider_id"],
        ["id"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT count(*) FROM service_sessions")).scalar_one():
        raise RuntimeError("Cannot downgrade provider persistence while service sessions exist")
    op.drop_constraint("fk_service_sessions_provider_id_providers", "service_sessions", type_="foreignkey")
    op.create_foreign_key("service_sessions_provider_id_fkey", "service_sessions", "persons", ["provider_id"], ["id"])
    op.drop_index("ix_providers_deleted_at", table_name="providers")
    op.drop_index("ix_providers_user_id", table_name="providers")
    op.drop_index("ix_providers_tenant_id", table_name="providers")
    op.drop_table("providers")
