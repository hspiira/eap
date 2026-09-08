"""Add document_types table, replacing the DocumentType enum

Revision ID: b8a183a81c8a
Revises: 7af2412c8b90
Create Date: 2026-09-08

``DocumentType`` carried an explicit ``OTHER`` member, itself evidence the
fixed list was already insufficient. Mirrors ``service_categories``
(migration 7af2412c8b90): a real table, seeded with the seven values in use,
so a new document type is a row an operator adds through the API rather than
a code deploy and a migration to widen a CHECK constraint.

``documents.document_type``'s CHECK constraint (migration
32b395f52e9f_add_missing_service_tables) is dropped in favour of a foreign
key to this table.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b8a183a81c8a"
down_revision: Union[str, Sequence[str], None] = "7af2412c8b90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (id, code, name). code and name start identical: the enum's values were
# already good display strings.
_TYPES: list[tuple[str, str, str]] = [
    ("doctype_contract", "Contract", "Contract"),
    ("doctype_certification", "Certification", "Certification"),
    ("doctype_kpi_report", "KPI Report", "KPI Report"),
    ("doctype_feedback_summary", "Feedback Summary", "Feedback Summary"),
    ("doctype_billing_report", "Billing Report", "Billing Report"),
    ("doctype_util_report", "Utilization Report", "Utilization Report"),
    ("doctype_other", "Other", "Other"),
]

_FK_DOCUMENTS = "fk_documents_document_type_document_types"

_ORIGINAL_ALLOWED = (
    "'Contract', 'Certification', 'KPI Report', 'Feedback Summary', "
    "'Billing Report', 'Utilization Report', 'Other'"
)


def upgrade() -> None:
    document_types = op.create_table(
        "document_types",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    op.bulk_insert(
        document_types,
        [
            {
                "id": row_id,
                "code": code,
                "name": name,
                "description": None,
                "sort_order": order,
                "is_active": True,
                "version": 1,
                "effective_until": None,
            }
            for order, (row_id, code, name) in enumerate(_TYPES)
        ],
    )

    op.drop_constraint("document_type_check", "documents", type_="check")
    op.create_foreign_key(
        _FK_DOCUMENTS, "documents", "document_types", ["document_type"], ["code"]
    )


def downgrade() -> None:
    op.drop_constraint(_FK_DOCUMENTS, "documents", type_="foreignkey")
    op.create_check_constraint(
        "document_type_check",
        "documents",
        f"document_type IN ({_ORIGINAL_ALLOWED})",
    )
    op.drop_table("document_types")
