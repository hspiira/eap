"""Move client aliases from the transitional JSON column to client_aliases."""

import json
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.shared.utils.client_alias import normalize_client_alias
from app.shared.utils.generators import generate_cuid

revision = "b6c8d0e2f4a6"
down_revision = ("a5b7c9d1e3f4", "e1a5b8c3d7f2", "e1a5c7b9d3f2")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _create_alias_table() -> None:
    op.create_table(
        "client_aliases",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("tenant_id", sa.String(length=25), nullable=False),
        sa.Column(
            "client_id",
            sa.String(length=25),
            sa.ForeignKey("clients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("alias", sa.String(length=255), nullable=False),
        sa.Column("normalized_alias", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_client_aliases_tenant_id", "client_aliases", ["tenant_id"])
    op.create_index("ix_client_aliases_client_id", "client_aliases", ["client_id"])
    op.create_index(
        "uq_client_aliases_tenant_normalized",
        "client_aliases",
        ["tenant_id", "normalized_alias"],
        unique=True,
    )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "client_aliases" not in tables:
        _create_alias_table()

    client_columns = {column["name"] for column in inspector.get_columns("clients")}
    if "aliases" not in client_columns:
        return

    seen: set[tuple[str, str]] = set()
    rows = bind.execute(sa.text("SELECT id, tenant_id, aliases FROM clients")).mappings()
    for row in rows:
        raw_aliases = row["aliases"] or []
        if isinstance(raw_aliases, str):
            raw_aliases = json.loads(raw_aliases)
        for raw_alias in raw_aliases:
            alias = " ".join(str(raw_alias).split())
            normalized = normalize_client_alias(alias)
            key = (row["tenant_id"], normalized)
            if not alias or not normalized or key in seen:
                continue
            seen.add(key)
            bind.execute(
                sa.text(
                    "INSERT INTO client_aliases "
                    "(id, tenant_id, client_id, alias, normalized_alias, created_at, updated_at) "
                    "VALUES (:id, :tenant_id, :client_id, :alias, :normalized_alias, "
                    "CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                ),
                {
                    "id": generate_cuid(),
                    "tenant_id": row["tenant_id"],
                    "client_id": row["id"],
                    "alias": alias,
                    "normalized_alias": normalized,
                },
            )
    op.drop_column("clients", "aliases")


def downgrade() -> None:
    op.add_column(
        "clients",
        sa.Column("aliases", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )
    op.drop_index("uq_client_aliases_tenant_normalized", table_name="client_aliases")
    op.drop_index("ix_client_aliases_client_id", table_name="client_aliases")
    op.drop_index("ix_client_aliases_tenant_id", table_name="client_aliases")
    op.drop_table("client_aliases")
