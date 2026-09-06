"""Give the practitioner an owned identity and make the account link optional.

Revision ID: a1p2i0d2e4f6
Revises: a1p1c0d2e4f6

Backfills display_name and contact_email from the linked user and records that
provenance. Refuses to apply when a linked user has no display name, because
neither the provider id nor an email local part is that person's name.

Downgrade restores user_id NOT NULL and drops the owned columns. It refuses to
run while any practitioner has no linked account, since there is no non-invented
value for user_id in that case. Restoring those rows needs a database restore.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a1p2i0d2e4f6"
down_revision: str | Sequence[str] | None = "a1p1c0d2e4f6"
branch_labels = None
depends_on = None

_SAMPLE_LIMIT = 20


def _sample(statement: str) -> list[tuple]:
    result = op.get_bind().execute(sa.text(statement), {"limit": _SAMPLE_LIMIT + 1})
    return list(result)


def _describe(rows: list[tuple], render) -> str:
    detail = ", ".join(render(row) for row in rows[:_SAMPLE_LIMIT])
    if len(rows) > _SAMPLE_LIMIT:
        detail += f", and further rows beyond the first {_SAMPLE_LIMIT}"
    return detail


def _reject_unnameable_providers() -> None:
    rows = _sample(
        """
        SELECT p.id, p.user_id
        FROM providers AS p
        JOIN users AS u ON u.id = p.user_id AND u.tenant_id = p.tenant_id
        WHERE p.deleted_at IS NULL
          AND (u.display_name IS NULL OR btrim(u.display_name) = '')
        ORDER BY p.id
        LIMIT :limit
        """
    )
    if rows:
        raise RuntimeError(
            "Practitioner identity requires an owned display name and the linked account "
            "supplies none. Reconcile these practitioners before retrying: "
            + _describe(rows, lambda row: f"providers.id={row[0]} user_id={row[1]}")
        )


def _reject_duplicate_account_links() -> None:
    rows = _sample(
        """
        SELECT tenant_id, user_id, count(*) AS links
        FROM providers
        WHERE user_id IS NOT NULL AND deleted_at IS NULL
        GROUP BY tenant_id, user_id
        HAVING count(*) > 1
        ORDER BY tenant_id, user_id
        LIMIT :limit
        """
    )
    if rows:
        raise RuntimeError(
            "One account may be linked to at most one practitioner per tenant. "
            "Resolve these duplicate links before retrying: "
            + _describe(
                rows, lambda row: f"tenant_id={row[0]} user_id={row[1]} links={row[2]}"
            )
        )


def upgrade() -> None:
    _reject_unnameable_providers()
    _reject_duplicate_account_links()

    op.add_column("providers", sa.Column("display_name", sa.String(length=200), nullable=True))
    op.add_column("providers", sa.Column("contact_email", sa.String(length=255), nullable=True))
    op.add_column("providers", sa.Column("contact_phone", sa.String(length=50), nullable=True))
    op.add_column(
        "providers", sa.Column("identity_provenance", sa.String(length=30), nullable=True)
    )

    op.execute(
        """
        UPDATE providers AS p
        SET display_name = btrim(u.display_name),
            contact_email = u.email,
            identity_provenance = 'BackfilledFromUser'
        FROM users AS u
        WHERE u.id = p.user_id
          AND u.tenant_id = p.tenant_id
          AND u.display_name IS NOT NULL
          AND btrim(u.display_name) <> ''
        """
    )
    op.execute(
        "UPDATE providers SET identity_provenance = 'Owned' WHERE identity_provenance IS NULL"
    )

    op.alter_column("providers", "identity_provenance", nullable=False)
    op.alter_column("providers", "display_name", nullable=False)
    op.alter_column("providers", "user_id", existing_type=sa.String(length=25), nullable=True)

    op.create_index(
        "uq_providers_tenant_user_link",
        "providers",
        ["tenant_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("user_id IS NOT NULL"),
    )


def downgrade() -> None:
    rows = _sample(
        """
        SELECT id FROM providers
        WHERE user_id IS NULL AND deleted_at IS NULL
        ORDER BY id
        LIMIT :limit
        """
    )
    if rows:
        raise RuntimeError(
            "Cannot restore providers.user_id NOT NULL while practitioners have no linked "
            "account. Restore from backup instead of inventing accounts for: "
            + _describe(rows, lambda row: f"providers.id={row[0]}")
        )

    op.drop_index("uq_providers_tenant_user_link", table_name="providers")
    op.alter_column("providers", "user_id", existing_type=sa.String(length=25), nullable=False)
    op.drop_column("providers", "identity_provenance")
    op.drop_column("providers", "contact_phone")
    op.drop_column("providers", "contact_email")
    op.drop_column("providers", "display_name")
