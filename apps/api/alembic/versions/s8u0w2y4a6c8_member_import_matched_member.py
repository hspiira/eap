"""The member a staged roster row resolved to, so that row can update it

Revision ID: s8u0w2y4a6c8
Revises: r7t9v1x3z5b7
Create Date: 2026-09-10

A Duplicate row means "this Staff_ID already belongs to someone". Until now
that was the end of it: the row was inert and the member was never touched.
A reviewer can now choose Update on such a row, so the row has to record
which member it matched, and that has to be decided once at staging time
rather than re-derived wherever the decision is read.

Only the Duplicate raised by `_already_enrolled` carries a value. The other
Duplicate, a row whose Staff_ID is still claimed by an unresolved batch,
resolved to no member and stays inert; so does a row whose roster values
cannot be applied to the member it matched (a contradicting Relation, an
unparseable date). `matched_member_id IS NULL` is therefore the single test
for "update is not on offer for this row".

`ON DELETE SET NULL` matches `imported_member_id`: deleting a member must not
delete the provenance of the roster that named them, only the pointer.

Reversing this drops the match. It is recomputed by re-staging the roster;
no member data lives here, only a pointer.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "s8u0w2y4a6c8"
down_revision: str | Sequence[str] | None = "r7t9v1x3z5b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "member_import_rows", sa.Column("matched_member_id", sa.String(25), nullable=True)
    )
    op.create_foreign_key(
        "fk_member_import_rows_matched_member",
        "member_import_rows",
        "eligible_members",
        ["matched_member_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_member_import_rows_matched_member", "member_import_rows", type_="foreignkey"
    )
    op.drop_column("member_import_rows", "matched_member_id")
