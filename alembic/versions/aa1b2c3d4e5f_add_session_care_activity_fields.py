"""Add Care Activity Log fields to service_sessions

Revision ID: aa1b2c3d4e5f
Revises: z4u7v9w1q3s6
Create Date: 2026-05-11

Adds 13 columns required to capture the full Care Activity Log xlsx data model:
session_type, category, rate_ugx, issue_topic, diagnosis_type_id, diagnosis_id,
approved_by, session_number, partner_name, partner_relationship, headcount,
client_type, clinical_outcome.

issue_topic and partner_name are encrypted at the application layer before
being written, consistent with notes/feedback.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "aa1b2c3d4e5f"
down_revision: Union[str, Sequence[str], None] = "z4u7v9w1q3s6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "service_sessions",
        sa.Column("session_type", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "service_sessions",
        sa.Column("category", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "service_sessions",
        sa.Column("rate_ugx", sa.Integer(), nullable=True),
    )
    op.add_column(
        "service_sessions",
        sa.Column("issue_topic", sa.Text(), nullable=True),
    )
    op.add_column(
        "service_sessions",
        sa.Column("diagnosis_type_id", sa.String(length=25), nullable=True),
    )
    op.add_column(
        "service_sessions",
        sa.Column("diagnosis_id", sa.String(length=25), nullable=True),
    )
    op.add_column(
        "service_sessions",
        sa.Column("approved_by", sa.String(length=25), nullable=True),
    )
    op.add_column(
        "service_sessions",
        sa.Column("session_number", sa.Integer(), nullable=True),
    )
    op.add_column(
        "service_sessions",
        sa.Column("partner_name", sa.Text(), nullable=True),
    )
    op.add_column(
        "service_sessions",
        sa.Column("partner_relationship", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "service_sessions",
        sa.Column("headcount", sa.Integer(), nullable=True),
    )
    op.add_column(
        "service_sessions",
        sa.Column("client_type", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "service_sessions",
        sa.Column("clinical_outcome", sa.String(length=50), nullable=True),
    )

    # Indexes for commonly filtered columns
    op.create_index("ix_service_sessions_session_type", "service_sessions", ["session_type"])
    op.create_index("ix_service_sessions_category", "service_sessions", ["category"])
    op.create_index("ix_service_sessions_diagnosis_type_id", "service_sessions", ["diagnosis_type_id"])
    op.create_index("ix_service_sessions_diagnosis_id", "service_sessions", ["diagnosis_id"])
    op.create_index("ix_service_sessions_approved_by", "service_sessions", ["approved_by"])
    op.create_index("ix_service_sessions_client_type", "service_sessions", ["client_type"])
    op.create_index("ix_service_sessions_clinical_outcome", "service_sessions", ["clinical_outcome"])

    # Check constraints
    op.create_check_constraint(
        "session_type_check",
        "service_sessions",
        "session_type IS NULL OR session_type IN ('Physical', 'Online')",
    )
    op.create_check_constraint(
        "session_category_check",
        "service_sessions",
        "category IS NULL OR category IN ('Individual', 'Group', 'Family', 'Couples')",
    )
    op.create_check_constraint(
        "session_client_type_check",
        "service_sessions",
        "client_type IS NULL OR client_type IN ('New', 'Repeat')",
    )
    op.create_check_constraint(
        "session_clinical_outcome_check",
        "service_sessions",
        "clinical_outcome IS NULL OR clinical_outcome IN ('ToBeContinued', 'Referred', 'Completed')",
    )


def downgrade() -> None:
    op.drop_constraint("session_clinical_outcome_check", "service_sessions", type_="check")
    op.drop_constraint("session_client_type_check", "service_sessions", type_="check")
    op.drop_constraint("session_category_check", "service_sessions", type_="check")
    op.drop_constraint("session_type_check", "service_sessions", type_="check")

    op.drop_index("ix_service_sessions_clinical_outcome", table_name="service_sessions")
    op.drop_index("ix_service_sessions_client_type", table_name="service_sessions")
    op.drop_index("ix_service_sessions_approved_by", table_name="service_sessions")
    op.drop_index("ix_service_sessions_diagnosis_id", table_name="service_sessions")
    op.drop_index("ix_service_sessions_diagnosis_type_id", table_name="service_sessions")
    op.drop_index("ix_service_sessions_category", table_name="service_sessions")
    op.drop_index("ix_service_sessions_session_type", table_name="service_sessions")

    op.drop_column("service_sessions", "clinical_outcome")
    op.drop_column("service_sessions", "client_type")
    op.drop_column("service_sessions", "headcount")
    op.drop_column("service_sessions", "partner_relationship")
    op.drop_column("service_sessions", "partner_name")
    op.drop_column("service_sessions", "session_number")
    op.drop_column("service_sessions", "approved_by")
    op.drop_column("service_sessions", "diagnosis_id")
    op.drop_column("service_sessions", "diagnosis_type_id")
    op.drop_column("service_sessions", "issue_topic")
    op.drop_column("service_sessions", "rate_ugx")
    op.drop_column("service_sessions", "category")
    op.drop_column("service_sessions", "session_type")
