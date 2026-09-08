"""
Load seed data from data/seed_data.json into the database.

For testing and local development. Uses the app's async engine and session.
Run from project root with DATABASE_URL set (e.g. in .env):

    uv run python scripts/load_seed_data.py
    uv run python scripts/load_seed_data.py --clear   # truncate tables first

Uses seed IDs from the JSON as-is (e.g. t01, u01, c01) so references stay valid.
"""

from __future__ import annotations

import argparse
import json
import sys

# Ensure project root is on path when run as script
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.domain.enums import (
    AuditActionType,
    BaseStatus,
    ContactMethod,
    ContractStatus,
    DocumentStatus,
    Language,
    PaymentFrequency,
    PaymentStatus,
    PersonType,
    SessionStatus,
    SubscriptionTier,
    TenantRole,
    TenantStatus,
    UserStatus,
)
from app.infrastructure.models import (
    ActivityModel,
    AuditLogModel,
    ClientModel,
    ClientTagModel,
    ContactModel,
    ContractModel,
    DocumentModel,
    EntityChangeModel,
    IndustryModel,
    KPIAssignmentModel,
    KPIModel,
    PasswordSetTokenModel,
    PersonModel,
    ServiceAssignmentModel,
    ServiceModel,
    ServiceSessionModel,
    TenantModel,
    UserModel,
)
from app.infrastructure.models.refresh_token_model import RefreshTokenModel

# Path to seed data (relative to project root)
SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "seed_data.json"

# PostgreSQL native enum types (only for columns created as PG enums in initial migration)
# Tables added in later migrations (services, documents, kpis, etc.) use String for status/type.
_PG_ENUM_COLUMNS = {
    "tenants": {
        "status": (TenantStatus, "tenantstatus"),
        "subscription_tier": (SubscriptionTier, "subscriptiontier"),
    },
    "users": {"status": (UserStatus, "userstatus"), "preferred_language": (Language, "language")},
    "clients": {
        "status": (BaseStatus, "basestatus"),
        "preferred_contact_method": (ContactMethod, "contactmethod"),
    },
    "persons": {
        "person_type": (PersonType, "persontype"),
        "secondary_person_type": (PersonType, "persontype"),
        "status": (BaseStatus, "basestatus"),
    },
    "contracts": {
        "payment_frequency": (PaymentFrequency, "paymentfrequency"),
        "payment_status": (PaymentStatus, "paymentstatus"),
        "status": (ContractStatus, "contractstatus"),
    },
}

# Tables to truncate in reverse dependency order (--clear)
TRUNCATE_ORDER = [
    "entity_changes",
    "audit_logs",
    "password_set_tokens",
    "refresh_tokens",
    "activities",
    "kpi_assignments",
    "kpis",
    "documents",
    "service_sessions",
    "service_assignments",
    "contracts",
    "services",
    "contacts",
    "persons",
    "clients",
    "client_tags",
    "industries",
    "users",
    "tenants",
]


def parse_dt(s: str | None):
    if s is None:
        return None
    if s.endswith("Z"):
        s = s.replace("Z", "+00:00")
    return datetime.fromisoformat(s)


def parse_date(s: str | None):
    if s is None:
        return None
    return date.fromisoformat(s)


def parse_decimal(s: str | None):
    if s is None:
        return None
    return Decimal(s)


def load_json() -> dict:
    with open(SEED_PATH, encoding="utf-8") as f:
        return json.load(f)


async def clear_tables(session: AsyncSession) -> None:
    """Truncate all seed tables (reverse FK order). Uses CASCADE for PostgreSQL."""
    dialect = session.get_bind().dialect.name
    if dialect == "postgresql":
        tables = ", ".join(TRUNCATE_ORDER)
        await session.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))
    else:
        for table in TRUNCATE_ORDER:
            await session.execute(text(f"DELETE FROM {table}"))
    await session.commit()
    print("Cleared all seed tables.")


def build_tenants(rows: list[dict]) -> list[TenantModel]:
    return [
        TenantModel(
            id=r["id"],
            name=r["name"],
            code=r["code"],
            status=TenantStatus(r["status"]),
            settings=r["settings"],
            subscription_tier=SubscriptionTier(r["subscription_tier"]),
        )
        for r in rows
    ]


def build_users(rows: list[dict]) -> list[UserModel]:
    return [
        UserModel(
            id=r["id"],
            tenant_id=r["tenant_id"],
            email=r["email"],
            password_hash=r.get("password_hash"),
            status=UserStatus(r["status"]),
            preferred_language=Language(r["preferred_language"])
            if r.get("preferred_language")
            else None,
            timezone=r.get("timezone"),
            role=TenantRole(r["role"]),
            is_two_factor_enabled=r.get("is_two_factor_enabled", False),
        )
        for r in rows
    ]


def build_industries(rows: list[dict]) -> list[IndustryModel]:
    return [
        IndustryModel(
            id=r["id"],
            tenant_id=r["tenant_id"],
            name=r["name"],
            description=r.get("description"),
            code=r.get("code"),
            parent_industry_id=r.get("parent_industry_id"),
            is_active=r.get("is_active", True),
        )
        for r in rows
    ]


def build_client_tags(rows: list[dict]) -> list[ClientTagModel]:
    return [
        ClientTagModel(
            id=r["id"],
            tenant_id=r["tenant_id"],
            name=r["name"],
            description=r.get("description"),
            color=r.get("color"),
            is_active=r.get("is_active", True),
        )
        for r in rows
    ]


def build_clients(rows: list[dict]) -> list[ClientModel]:
    return [
        ClientModel(
            id=r["id"],
            tenant_id=r["tenant_id"],
            name=r["name"],
            code=r["code"],
            contact_info=r["contact_info"],
            billing_address=r.get("billing_address"),
            industry_id=r.get("industry_id"),
            parent_client_id=r.get("parent_client_id"),
            status=BaseStatus(r["status"]),
            is_verified=r.get("is_verified", False),
            preferred_contact_method=ContactMethod(r["preferred_contact_method"])
            if r.get("preferred_contact_method")
            else None,
        )
        for r in rows
    ]


def build_contacts(rows: list[dict]) -> list[ContactModel]:
    return [
        ContactModel(
            id=r["id"],
            tenant_id=r["tenant_id"],
            client_id=r["client_id"],
            name=r["name"],
            title=r.get("title"),
            email=r.get("email"),
            phone=r.get("phone"),
            department=r.get("department"),
            is_primary=r.get("is_primary", False),
            notes=r.get("notes"),
            is_active=r.get("is_active", True),
        )
        for r in rows
    ]


def build_persons(rows: list[dict]) -> list[PersonModel]:
    return [
        PersonModel(
            id=r["id"],
            tenant_id=r["tenant_id"],
            user_id=r["user_id"],
            person_type=PersonType(r["person_type"]),
            is_dual_role=r.get("is_dual_role", False),
            secondary_person_type=PersonType(r["secondary_person_type"])
            if r.get("secondary_person_type")
            else None,
            family_id=r.get("family_id"),
            employment_info=r.get("employment_info"),
            license_info=r.get("license_info"),
            staff_info=r.get("staff_info"),
            dependent_info=r.get("dependent_info"),
            status=BaseStatus(r["status"]),
            emergency_contact=r.get("emergency_contact"),
            last_service_date=parse_date(r.get("last_service_date")),
        )
        for r in rows
    ]


def build_contracts(rows: list[dict]) -> list[ContractModel]:
    return [
        ContractModel(
            id=r["id"],
            tenant_id=r["tenant_id"],
            client_id=r["client_id"],
            period=r["period"],
            billing_rate=r["billing_rate"],
            payment_frequency=PaymentFrequency(r["payment_frequency"]),
            payment_status=PaymentStatus(r["payment_status"]),
            status=ContractStatus(r["status"]),
            is_auto_renew=r.get("is_auto_renew", False),
            last_billing_date=parse_date(r.get("last_billing_date")),
            next_billing_date=parse_date(r.get("next_billing_date")),
            signed_by=r.get("signed_by"),
            signed_at=parse_dt(r.get("signed_at")),
            termination_reason=r.get("termination_reason"),
        )
        for r in rows
    ]


def build_services(rows: list[dict]) -> list[ServiceModel]:
    return [
        ServiceModel(
            id=r["id"],
            tenant_id=r["tenant_id"],
            name=r["name"],
            description=r.get("description"),
            category=r.get("category"),
            status=BaseStatus(r["status"]),
            duration_minutes=r.get("duration_minutes"),
            is_group_service=r.get("is_group_service", False),
            max_participants=r.get("max_participants"),
        )
        for r in rows
    ]


def build_service_assignments(rows: list[dict]) -> list[ServiceAssignmentModel]:
    return [
        ServiceAssignmentModel(
            id=r["id"],
            tenant_id=r["tenant_id"],
            service_id=r["service_id"],
            contract_id=r["contract_id"],
            status=BaseStatus(r["status"]),
            assigned_at=parse_dt(r.get("assigned_at")),
            assigned_by=r.get("assigned_by"),
            notes=r.get("notes"),
        )
        for r in rows
    ]


def build_service_sessions(rows: list[dict]) -> list[ServiceSessionModel]:
    return [
        ServiceSessionModel(
            id=r["id"],
            tenant_id=r["tenant_id"],
            service_id=r["service_id"],
            provider_id=r["provider_id"],
            member_id=r["member_id"],
            scheduled_at=parse_dt(r["scheduled_at"]) or datetime.now(UTC),
            status=SessionStatus(r["status"]),
            reschedule_count=r.get("reschedule_count", 0),
            completed_at=parse_dt(r.get("completed_at")),
            duration=r.get("duration"),
            location=r.get("location"),
            notes=r.get("notes"),
            feedback=r.get("feedback"),
            cancellation_reason=r.get("cancellation_reason"),
        )
        for r in rows
    ]


def build_documents(rows: list[dict]) -> list[DocumentModel]:
    return [
        DocumentModel(
            id=r["id"],
            tenant_id=r["tenant_id"],
            name=r["name"],
            description=r.get("description"),
            document_type=r["document_type"],
            status=DocumentStatus(r["status"]),
            file_path=r.get("file_path"),
            file_url=r.get("file_url"),
            file_size=r.get("file_size"),
            mime_type=r.get("mime_type"),
            version=r.get("version", 1),
            is_latest=r.get("is_latest", True),
            previous_version_id=r.get("previous_version_id"),
            uploaded_by=r.get("uploaded_by"),
            client_id=r.get("client_id"),
            contract_id=r.get("contract_id"),
            person_id=r.get("person_id"),
            expires_at=parse_dt(r.get("expires_at")),
            is_confidential=r.get("is_confidential", False),
            published_at=parse_dt(r.get("published_at")),
            archived_at=parse_dt(r.get("archived_at")),
        )
        for r in rows
    ]


def build_kpis(rows: list[dict]) -> list[KPIModel]:
    return [
        KPIModel(
            id=r["id"],
            tenant_id=r["tenant_id"],
            name=r["name"],
            description=r.get("description"),
            category=r["category"],
            measurement_unit=r["measurement_unit"],
            target_value=parse_decimal(r.get("target_value")),
            threshold_min=parse_decimal(r.get("threshold_min")),
            threshold_max=parse_decimal(r.get("threshold_max")),
            formula=r.get("formula"),
            is_active=r.get("is_active", True),
        )
        for r in rows
    ]


def build_kpi_assignments(rows: list[dict]) -> list[KPIAssignmentModel]:
    return [
        KPIAssignmentModel(
            id=r["id"],
            tenant_id=r["tenant_id"],
            kpi_id=r["kpi_id"],
            client_id=r.get("client_id"),
            contract_id=r.get("contract_id"),
            target_value=parse_decimal(r.get("target_value")),
            is_active=r.get("is_active", True),
        )
        for r in rows
    ]


def build_activities(rows: list[dict]) -> list[ActivityModel]:
    return [
        ActivityModel(
            id=r["id"],
            tenant_id=r["tenant_id"],
            client_id=r["client_id"],
            activity_type=r["activity_type"],
            subject=r.get("subject"),
            description=r["description"],
            outcome=r.get("outcome"),
            created_by=r["created_by"],
            occurred_at=parse_dt(r["occurred_at"]) or datetime.now(UTC),
            next_follow_up=parse_dt(r.get("next_follow_up")),
            is_important=r.get("is_important", False),
        )
        for r in rows
    ]


def _naive_utc(dt: datetime | None) -> datetime | None:
    """Convert to naive UTC (audit_logs.occurred_at is TIMESTAMP WITHOUT TIME ZONE)."""
    if dt is None:
        return None
    if dt.tzinfo:
        dt = dt.astimezone(UTC).replace(tzinfo=None)
    return dt


def build_audit_logs(rows: list[dict]) -> list[AuditLogModel]:
    return [
        AuditLogModel(
            id=r["id"],
            tenant_id=r["tenant_id"],
            user_id=r.get("user_id"),
            action_type=AuditActionType(r["action_type"]),
            resource_type=r["resource_type"],
            resource_id=r.get("resource_id"),
            description=r.get("description"),
            ip_address=r.get("ip_address"),
            user_agent=r.get("user_agent"),
            extra_metadata=r.get("extra_metadata"),
            occurred_at=_naive_utc(parse_dt(r["occurred_at"]) or datetime.now(UTC)),
        )
        for r in rows
    ]


def build_entity_changes(rows: list[dict]) -> list[EntityChangeModel]:
    return [
        EntityChangeModel(
            id=r["id"],
            audit_log_id=r["audit_log_id"],
            entity_type=r["entity_type"],
            entity_id=r["entity_id"],
            field_changes=r["field_changes"],
        )
        for r in rows
    ]


def build_password_set_tokens(rows: list[dict]) -> list[PasswordSetTokenModel]:
    return [
        PasswordSetTokenModel(
            id=r["id"],
            token_hash=(r["token_hash"])[:64],  # column is VARCHAR(64)
            user_id=r["user_id"],
            expires_at=parse_dt(r["expires_at"]) or datetime.now(UTC),
            used_at=parse_dt(r.get("used_at")),
        )
        for r in rows
    ]


def build_refresh_tokens(rows: list[dict]) -> list[RefreshTokenModel]:
    return [
        RefreshTokenModel(
            jti=r["jti"],
            user_id=r["user_id"],
            tenant_id=r["tenant_id"],
            created_at=parse_dt(r.get("created_at")) or datetime.now(UTC),
            revoked_at=parse_dt(r.get("revoked_at")),
        )
        for r in rows
    ]


async def run_load(clear: bool) -> None:
    data = load_json()
    async with AsyncSessionLocal() as session:
        if clear:
            await clear_tables(session)
        await insert_all(session, data)
    print("Seed data loaded successfully.")


def _apply_pg_enum_patch(session: AsyncSession) -> None:
    """Patch table column types to use PostgreSQL native enums so INSERT emits correct type."""
    dialect_name = session.get_bind().dialect.name
    if dialect_name != "postgresql":
        return
    table_to_model = {
        "tenants": TenantModel,
        "users": UserModel,
        "clients": ClientModel,
        "persons": PersonModel,
        "contracts": ContractModel,
    }
    for table_name, col_map in _PG_ENUM_COLUMNS.items():
        model = table_to_model.get(table_name)
        if not model:
            continue
        table = model.__table__
        for col_name, (enum_class, pg_name) in col_map.items():
            if col_name in table.c:
                pg_type = PG_ENUM(*[e.value for e in enum_class], name=pg_name, create_type=False)
                table.c[col_name].type = pg_type


async def insert_all(session: AsyncSession, data: dict) -> None:
    _apply_pg_enum_patch(session)
    builders = [
        ("tenants", build_tenants),
        ("users", build_users),
        ("industries", build_industries),
        ("client_tags", build_client_tags),
        ("clients", build_clients),
        ("contacts", build_contacts),
        ("persons", build_persons),
        ("contracts", build_contracts),
        ("services", build_services),
        ("service_assignments", build_service_assignments),
        ("service_sessions", build_service_sessions),
        ("documents", build_documents),
        ("kpis", build_kpis),
        ("kpi_assignments", build_kpi_assignments),
        ("activities", build_activities),
        ("audit_logs", build_audit_logs),
        ("entity_changes", build_entity_changes),
        ("password_set_tokens", build_password_set_tokens),
        ("refresh_tokens", build_refresh_tokens),
    ]
    for table_key, builder in builders:
        rows = data.get(table_key, [])
        if not rows:
            continue
        models = builder(rows)
        session.add_all(models)
        await session.flush()  # ensure FKs exist before dependent tables
        print(f"  {table_key}: {len(models)} rows")
    await session.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Load seed data from data/seed_data.json")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Truncate seed tables before loading (reverse FK order)",
    )
    args = parser.parse_args()

    if not SEED_PATH.exists():
        raise SystemExit(f"Seed file not found: {SEED_PATH}")

    import asyncio

    asyncio.run(run_load(clear=args.clear))


if __name__ == "__main__":
    main()
