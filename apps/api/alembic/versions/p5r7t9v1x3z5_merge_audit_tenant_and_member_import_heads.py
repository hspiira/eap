"""Merge the audit-tenant and member-import-staging branches

Revision ID: p5r7t9v1x3z5
Revises: e3f5g7h9j1k3, n3q5s7u9w1y3
Create Date: 2026-09-10

Two independent branches landed on the same day from d8x1y3z5a7c9 with no
overlapping tables:

- e3f5g7h9j1k3: drops the cascading tenant foreign key on audit_logs.
- n3q5s7u9w1y3: member roster import staging batch and rows.

Pure merge point: nothing to reconcile between them.
"""

from collections.abc import Sequence

revision: str = "p5r7t9v1x3z5"
down_revision: str | Sequence[str] | None = ("e3f5g7h9j1k3", "n3q5s7u9w1y3")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
