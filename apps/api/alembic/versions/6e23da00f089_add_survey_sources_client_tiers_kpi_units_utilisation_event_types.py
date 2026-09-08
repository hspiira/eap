"""Add survey_sources, client_tiers, kpi_measurement_units, utilisation_event_types

Revision ID: 6e23da00f089
Revises: d1d7ce4bf753
Create Date: 2026-09-08

Replaces four enums with reference tables, mirroring service_categories
(migration 7af2412c8b90):

- ``SurveySource``: its docstring already called it "extensible".
- ``ClientTier``: a business classification with no code branching on it.
- ``KPIMeasurementUnit``: had a CHECK constraint (``kpi_measurement_unit_check``,
  migration 32b395f52e9f_add_missing_service_tables), dropped here.
- ``UtilisationEventType``: no CHECK constraint, ``EnumValueType`` only.

None of the four had any code branching on individual values (verified by
searching the whole codebase for a member-by-member comparison before
converting), so none of this changes behaviour.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "6e23da00f089"
down_revision: Union[str, Sequence[str], None] = "d1d7ce4bf753"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SURVEY_SOURCES: list[tuple[str, str, str]] = [
    ("survsrc_google_forms", "GoogleForms", "Google Forms"),
    ("survsrc_typeform", "Typeform", "Typeform"),
    ("survsrc_microsoft_forms", "MicrosoftForms", "Microsoft Forms"),
]

_CLIENT_TIERS: list[tuple[str, str, str]] = [
    ("cliertier_a", "A", "A: strategic / large account, full service mix"),
    ("cliertier_b", "B", "B: mid-tier, consultancy-extension candidate"),
    ("cliertier_c", "C", "C: long-tail / small account, lower-touch service model"),
]

_KPI_MEASUREMENT_UNITS: list[tuple[str, str, str]] = [
    ("kpiunit_percentage", "Percentage", "Percentage"),
    ("kpiunit_count", "Count", "Count"),
    ("kpiunit_rate", "Rate", "Rate"),
    ("kpiunit_score", "Score", "Score"),
    ("kpiunit_time", "Time", "Time"),
    ("kpiunit_currency", "Currency", "Currency"),
]

_UTILISATION_EVENT_TYPES: list[tuple[str, str, str]] = [
    ("utilevt_session_delivered", "SessionDelivered", "Session Delivered"),
    ("utilevt_care_callback", "CareCallback", "Care Callback"),
    ("utilevt_survey", "Survey", "Survey"),
    ("utilevt_incident_response", "IncidentResponse", "Incident Response"),
    ("utilevt_consultancy_hours", "ConsultancyHours", "Consultancy Hours"),
]

_FK_SURVEY_CAMPAIGNS = "fk_survey_campaigns_source_survey_sources"
_FK_CLIENTS_TIER = "fk_clients_tier_client_tiers"
_FK_KPIS_MEASUREMENT_UNIT = "fk_kpis_measurement_unit_kpi_measurement_units"
_FK_UTILISATION_EVENTS = "fk_utilisation_events_event_type_utilisation_event_types"

_ORIGINAL_KPI_UNIT_ALLOWED = (
    "'Percentage', 'Count', 'Rate', 'Score', 'Time', 'Currency'"
)


def _taxonomy_table(name: str):
    return op.create_table(
        name,
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


def _seed(table, rows: list[tuple[str, str, str]]) -> None:
    op.bulk_insert(
        table,
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
            for order, (row_id, code, name) in enumerate(rows)
        ],
    )


def upgrade() -> None:
    survey_sources = _taxonomy_table("survey_sources")
    client_tiers = _taxonomy_table("client_tiers")
    kpi_measurement_units = _taxonomy_table("kpi_measurement_units")
    utilisation_event_types = _taxonomy_table("utilisation_event_types")

    _seed(survey_sources, _SURVEY_SOURCES)
    _seed(client_tiers, _CLIENT_TIERS)
    _seed(kpi_measurement_units, _KPI_MEASUREMENT_UNITS)
    _seed(utilisation_event_types, _UTILISATION_EVENT_TYPES)

    op.create_foreign_key(
        _FK_SURVEY_CAMPAIGNS, "survey_campaigns", "survey_sources", ["source"], ["code"]
    )
    op.create_foreign_key(_FK_CLIENTS_TIER, "clients", "client_tiers", ["tier"], ["code"])
    op.drop_constraint("kpi_measurement_unit_check", "kpis", type_="check")
    op.create_foreign_key(
        _FK_KPIS_MEASUREMENT_UNIT,
        "kpis",
        "kpi_measurement_units",
        ["measurement_unit"],
        ["code"],
    )
    op.create_foreign_key(
        _FK_UTILISATION_EVENTS,
        "utilisation_events",
        "utilisation_event_types",
        ["event_type"],
        ["code"],
    )


def downgrade() -> None:
    op.drop_constraint(_FK_UTILISATION_EVENTS, "utilisation_events", type_="foreignkey")
    op.drop_constraint(_FK_KPIS_MEASUREMENT_UNIT, "kpis", type_="foreignkey")
    op.create_check_constraint(
        "kpi_measurement_unit_check",
        "kpis",
        f"measurement_unit IN ({_ORIGINAL_KPI_UNIT_ALLOWED})",
    )
    op.drop_constraint(_FK_CLIENTS_TIER, "clients", type_="foreignkey")
    op.drop_constraint(_FK_SURVEY_CAMPAIGNS, "survey_campaigns", type_="foreignkey")

    op.drop_table("utilisation_event_types")
    op.drop_table("kpi_measurement_units")
    op.drop_table("client_tiers")
    op.drop_table("survey_sources")
