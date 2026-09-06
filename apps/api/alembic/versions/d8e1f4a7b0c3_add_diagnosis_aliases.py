"""Add diagnosis aliases

Revision ID: d8e1f4a7b0c3
Revises: c7d0e3f6a9b2
Create Date: 2026-09-05

Resolves a legacy free-text diagnosis string to a canonical taxonomy row. The
reference extract holds 53 spellings for 29 concepts, and new spellings keep
arriving, so this is a table rather than a constant.

`diagnosis_id` is nullable on purpose: eleven of the source classifications name
a type with no specific diagnosis under it, and inventing a leaf for them would
be worse than recording what the data actually says. `service_sessions` already
allows the same shape.

`confidence` separates aliases confirmed against the taxonomy from ones inferred
by reading the label, so a reviewer can filter to what still needs sign-off.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "d8e1f4a7b0c3"
down_revision: Union[str, Sequence[str], None] = "c7d0e3f6a9b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "diagnosis_aliases",
        sa.Column("id", sa.String(length=25), primary_key=True),
        sa.Column("raw_value", sa.Text(), nullable=False),
        sa.Column("normalised_key", sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column(
            "diagnosis_type_id",
            sa.String(length=25),
            sa.ForeignKey("diagnosis_types.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "diagnosis_id",
            sa.String(length=25),
            sa.ForeignKey("diagnoses.id"),
            nullable=True,
            index=True,
        ),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("confidence", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "confidence IN ('confirmed', 'inferred')", name="diagnosis_alias_confidence_check"
        ),
    )


def downgrade() -> None:
    op.drop_table("diagnosis_aliases")
