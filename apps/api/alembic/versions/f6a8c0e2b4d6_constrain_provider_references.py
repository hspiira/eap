"""Constrain non-compete and outreach provider references.

Revision ID: f6a8c0e2b4d6
Revises: e5g7i9k1m3o5
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f6a8c0e2b4d6"
down_revision: str | Sequence[str] | None = "e5g7i9k1m3o5"
branch_labels = None
depends_on = None


def _invalid_reference_count(table: str, column: str) -> int:
    return int(
        op.get_bind()
        .execute(
            sa.text(
                f"""
                SELECT count(*)
                FROM {table} AS dependent
                LEFT JOIN providers AS provider ON provider.id = dependent.{column}
                WHERE dependent.{column} IS NOT NULL
                  AND (provider.id IS NULL OR provider.tenant_id != dependent.tenant_id)
                """
            )
        )
        .scalar_one()
    )


def upgrade() -> None:
    invalid_non_competes = _invalid_reference_count("non_compete_clauses", "provider_id")
    invalid_outreach = _invalid_reference_count("outreach_records", "counsellor_id")
    if invalid_non_competes or invalid_outreach:
        raise RuntimeError(
            "Provider reference constraints require every non-compete clause and outreach "
            "counsellor to reference a provider in the same tenant; resolve "
            f"{invalid_non_competes} non-compete and {invalid_outreach} outreach records first"
        )
    op.create_foreign_key(
        "fk_non_compete_clauses_provider_id_providers",
        "non_compete_clauses",
        "providers",
        ["provider_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_outreach_records_counsellor_id_providers",
        "outreach_records",
        "providers",
        ["counsellor_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_outreach_records_counsellor_id_providers", "outreach_records", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_non_compete_clauses_provider_id_providers",
        "non_compete_clauses",
        type_="foreignkey",
    )
