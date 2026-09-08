"""Merge the taxonomy, contracts/session-linking and survey-questions branches

Revision ID: fc5d8bb02d9a
Revises: 6e23da00f089, c7x0y2z4t6v9, b2q4s6u8w0y2
Create Date: 2026-09-08

Three independent branches landed concurrently with no overlapping tables:

- 6e23da00f089: enum-to-reference-table conversions (service_categories and
  eight siblings).
- c7x0y2z4t6v9: services_sessions.contract_id + the contract pricing work it
  builds on.
- b2q4s6u8w0y2: survey_campaigns.approved_questions.

Pure merge point: nothing to reconcile between them.
"""

from collections.abc import Sequence

revision: str = "fc5d8bb02d9a"
down_revision: str | Sequence[str] | None = ("6e23da00f089", "c7x0y2z4t6v9", "b2q4s6u8w0y2")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
