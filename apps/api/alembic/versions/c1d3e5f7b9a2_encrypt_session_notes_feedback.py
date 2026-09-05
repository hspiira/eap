"""Encrypt service_sessions.notes / feedback (Phase 1 #C8)

Revision ID: c1d3e5f7b9a2
Revises: b2c4e6f8a1d3
Create Date: 2026-05-08

Widens the columns to TEXT to hold base64 ciphertext (which is ~33% larger
than plaintext plus a 13-byte version/nonce/tag prefix). Existing rows are
left unchanged; the application encrypts on the next write. A separate
data-migration job is recommended if the table contains plaintext rows in
production; for v1 the table is empty.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "c1d3e5f7b9a2"
down_revision: Union[str, Sequence[str], None] = "b2c4e6f8a1d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        # SQLite has no ALTER COLUMN; VARCHAR and TEXT are the same storage class.
        return
    op.alter_column(
        "service_sessions",
        "notes",
        existing_type=sa.String(length=2000),
        type_=sa.Text(),
        existing_nullable=True,
    )
    op.alter_column(
        "service_sessions",
        "feedback",
        existing_type=sa.String(length=2000),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return
    op.alter_column(
        "service_sessions",
        "feedback",
        existing_type=sa.Text(),
        type_=sa.String(length=2000),
        existing_nullable=True,
    )
    op.alter_column(
        "service_sessions",
        "notes",
        existing_type=sa.Text(),
        type_=sa.String(length=2000),
        existing_nullable=True,
    )
