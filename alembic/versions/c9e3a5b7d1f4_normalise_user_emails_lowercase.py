"""Normalise users.email to lowercase and enforce it going forward.

The Email value object now lowercases on construction, but rows written before
that change may hold mixed-case addresses. Those rows are unreachable via Azure
SSO (which lowercases the UPN claim) because `users.email` is compared with `=`,
which is case-sensitive on PostgreSQL — the user hits "account has not been
provisioned" with an address that looks correct to a human.

This backfills existing rows and adds a CHECK constraint so a stray mixed-case
insert from a path that bypasses the value object fails loudly instead of
creating another invisible login failure.

Collision safety: `users.email` is UNIQUE, so if two rows differ only by case
(e.g. 'Fred@x.com' and 'fred@x.com') the UPDATE would violate that constraint.
We detect this first and abort with an actionable message rather than letting
the migration die on an opaque IntegrityError — the operator must merge or
rename the duplicates by hand, since picking a winner is a business decision.

Revision ID: c9e3a5b7d1f4
Revises: b8d2f4a6c0e3
Create Date: 2026-08-04
"""

import sqlalchemy as sa

from alembic import op

revision = "c9e3a5b7d1f4"
down_revision = "b8d2f4a6c0e3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    collisions = conn.execute(
        sa.text(
            """
            SELECT lower(email) AS normalised, count(*) AS n
            FROM users
            WHERE deleted_at IS NULL
            GROUP BY lower(email)
            HAVING count(*) > 1
            """
        )
    ).fetchall()

    if collisions:
        detail = ", ".join(f"{row.normalised} ({row.n} rows)" for row in collisions)
        raise RuntimeError(
            "Cannot normalise users.email: these addresses collide once lowercased "
            f"and users.email is UNIQUE — {detail}. Merge or rename the duplicate "
            "accounts, then re-run this migration."
        )

    conn.execute(
        sa.text("UPDATE users SET email = lower(trim(email)) WHERE email <> lower(trim(email))")
    )

    op.create_check_constraint(
        "ck_users_email_lowercase",
        "users",
        "email = lower(email)",
    )


def downgrade() -> None:
    # The lowercasing itself is not reversible — the original casing is gone.
    # Dropping the constraint is all we can undo.
    op.drop_constraint("ck_users_email_lowercase", "users", type_="check")
