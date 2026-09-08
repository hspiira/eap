"""Add survey_campaigns.approved_questions

Employer-facing aggregates count only the questions listed here, so a free-text
answer never reaches a report (MODULES_REPAIR_PLAN PRIV-01). Existing campaigns
start with an empty list: their aggregates report no approved questions rather
than republishing whatever the form collected.

Revision ID: b2q4s6u8w0y2
Revises: a1p3d0d2e4f6
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b2q4s6u8w0y2"
down_revision: str | Sequence[str] | None = "a1p3d0d2e4f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "survey_campaigns",
        sa.Column(
            "approved_questions",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )


def downgrade() -> None:
    op.drop_column("survey_campaigns", "approved_questions")
