"""Add next_of_kin_relationships table, replacing the NextOfKinRelationship enum

Revision ID: d1d7ce4bf753
Revises: 3969757e8cd0
Create Date: 2026-09-08

Replaces the ``NextOfKinRelationship`` enum, whose explicit ``OTHER`` member
was already evidence the fixed list was insufficient. Mirrors
``service_categories`` (migration 7af2412c8b90): a real table, seeded with
the seven values in use, so a new relationship is a row an operator adds
through the API rather than a code deploy.

``member_next_of_kin.relationship`` carried no CHECK constraint
(``EnumValueType`` enforced it in Python only), so this only adds the
foreign key.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d1d7ce4bf753"
down_revision: Union[str, Sequence[str], None] = "3969757e8cd0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (id, code, name)
_RELATIONSHIPS: list[tuple[str, str, str]] = [
    ("nok_spouse", "Spouse", "Spouse"),
    ("nok_child", "Child", "Child"),
    ("nok_parent", "Parent", "Parent"),
    ("nok_sibling", "Sibling", "Sibling"),
    ("nok_guardian", "Guardian", "Guardian"),
    ("nok_partner", "Partner", "Partner"),
    ("nok_other", "Other", "Other"),
]

_FK_MEMBER_NEXT_OF_KIN = "fk_member_next_of_kin_relationship_next_of_kin_relationships"


def upgrade() -> None:
    next_of_kin_relationships = op.create_table(
        "next_of_kin_relationships",
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
        next_of_kin_relationships,
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
            for order, (row_id, code, name) in enumerate(_RELATIONSHIPS)
        ],
    )

    op.create_foreign_key(
        _FK_MEMBER_NEXT_OF_KIN,
        "member_next_of_kin",
        "next_of_kin_relationships",
        ["relationship"],
        ["code"],
    )


def downgrade() -> None:
    op.drop_constraint(_FK_MEMBER_NEXT_OF_KIN, "member_next_of_kin", type_="foreignkey")
    op.drop_table("next_of_kin_relationships")
