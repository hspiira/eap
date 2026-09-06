"""Use canonical Members as Care Callback outreach subjects."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d4f6a8b0c2e4"
down_revision: str | Sequence[str] | None = "c1e4a7b9d2f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    count = bind.execute(sa.text("SELECT count(*) FROM outreach_records")).scalar_one()
    if count:
        raise RuntimeError(
            "Care Callback subject migration requires an empty outreach_records table; "
            "review and map existing subjects to eligible_members first"
        )
    op.drop_index("ix_outreach_records_person_id", table_name="outreach_records")
    op.drop_column("outreach_records", "person_id")
    op.add_column(
        "outreach_records",
        sa.Column("member_id", sa.String(length=25), nullable=False),
    )
    op.create_foreign_key(
        "fk_outreach_records_member_id",
        "outreach_records",
        "eligible_members",
        ["member_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_outreach_records_member_id", "outreach_records", ["member_id"])


def downgrade() -> None:
    count = op.get_bind().execute(sa.text("SELECT count(*) FROM outreach_records")).scalar_one()
    if count:
        raise RuntimeError("Cannot downgrade care callback subjects while outreach records exist")
    op.drop_index("ix_outreach_records_member_id", table_name="outreach_records")
    op.drop_constraint("fk_outreach_records_member_id", "outreach_records", type_="foreignkey")
    op.drop_column("outreach_records", "member_id")
    op.add_column("outreach_records", sa.Column("person_id", sa.String(length=25), nullable=False))
    op.create_index("ix_outreach_records_person_id", "outreach_records", ["person_id"])
