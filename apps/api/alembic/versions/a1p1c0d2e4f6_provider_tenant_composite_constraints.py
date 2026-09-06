"""Enforce tenant equality on every provider reference with composite keys.

Revision ID: a1p1c0d2e4f6
Revises: f6a8c0e2b4d6
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a1p1c0d2e4f6"
down_revision: str | Sequence[str] | None = "f6a8c0e2b4d6"
branch_labels = None
depends_on = None

_SAMPLE_LIMIT = 20

_REFERENCES = (
    ("non_compete_clauses", "provider_id", "providers"),
    ("outreach_records", "counsellor_id", "providers"),
    ("service_sessions", "provider_id", "providers"),
    ("providers", "user_id", "users"),
)


def _cross_tenant_rows(table: str, column: str, target: str) -> list[tuple[str, str | None]]:
    """Rows whose reference is missing or belongs to another tenant."""
    result = op.get_bind().execute(
        sa.text(
            f"""
            SELECT dependent.id, dependent.{column}
            FROM {table} AS dependent
            LEFT JOIN {target} AS target
              ON target.id = dependent.{column}
             AND target.tenant_id = dependent.tenant_id
            WHERE dependent.{column} IS NOT NULL
              AND target.id IS NULL
            ORDER BY dependent.id
            LIMIT :limit
            """
        ),
        {"limit": _SAMPLE_LIMIT + 1},
    )
    return [(row[0], row[1]) for row in result]


def _reject_invalid_references() -> None:
    problems: list[str] = []
    for table, column, target in _REFERENCES:
        rows = _cross_tenant_rows(table, column, target)
        if not rows:
            continue
        shown = rows[:_SAMPLE_LIMIT]
        detail = ", ".join(f"{table}.id={row_id} {column}={ref}" for row_id, ref in shown)
        if len(rows) > _SAMPLE_LIMIT:
            detail += f", and further rows beyond the first {_SAMPLE_LIMIT}"
        problems.append(
            f"{table}.{column} must reference a {target} row in the same tenant; fix {detail}"
        )
    if problems:
        raise RuntimeError(
            "Provider tenant constraints refuse to apply. " + " | ".join(problems)
        )


def upgrade() -> None:
    _reject_invalid_references()

    op.create_unique_constraint("uq_users_tenant_id", "users", ["tenant_id", "id"])
    op.create_unique_constraint("uq_providers_tenant_id", "providers", ["tenant_id", "id"])

    op.drop_constraint("providers_user_id_fkey", "providers", type_="foreignkey")
    op.create_foreign_key(
        "fk_providers_user_tenant",
        "providers",
        "users",
        ["tenant_id", "user_id"],
        ["tenant_id", "id"],
        ondelete="RESTRICT",
    )

    op.drop_constraint(
        "fk_non_compete_clauses_provider_id_providers",
        "non_compete_clauses",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_non_compete_clauses_provider_tenant",
        "non_compete_clauses",
        "providers",
        ["tenant_id", "provider_id"],
        ["tenant_id", "id"],
        ondelete="RESTRICT",
    )

    op.drop_constraint(
        "fk_outreach_records_counsellor_id_providers", "outreach_records", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_outreach_records_counsellor_tenant",
        "outreach_records",
        "providers",
        ["tenant_id", "counsellor_id"],
        ["tenant_id", "id"],
        ondelete="RESTRICT",
    )

    op.drop_constraint(
        "fk_service_sessions_provider_id_providers", "service_sessions", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_service_sessions_provider_tenant",
        "service_sessions",
        "providers",
        ["tenant_id", "provider_id"],
        ["tenant_id", "id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_service_sessions_provider_tenant", "service_sessions", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_service_sessions_provider_id_providers",
        "service_sessions",
        "providers",
        ["provider_id"],
        ["id"],
    )

    op.drop_constraint(
        "fk_outreach_records_counsellor_tenant", "outreach_records", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_outreach_records_counsellor_id_providers",
        "outreach_records",
        "providers",
        ["counsellor_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.drop_constraint(
        "fk_non_compete_clauses_provider_tenant", "non_compete_clauses", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_non_compete_clauses_provider_id_providers",
        "non_compete_clauses",
        "providers",
        ["provider_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.drop_constraint("fk_providers_user_tenant", "providers", type_="foreignkey")
    op.create_foreign_key(
        "providers_user_id_fkey",
        "providers",
        "users",
        ["user_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.drop_constraint("uq_providers_tenant_id", "providers", type_="unique")
    op.drop_constraint("uq_users_tenant_id", "users", type_="unique")
