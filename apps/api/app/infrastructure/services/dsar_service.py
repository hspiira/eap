"""DSAR collector + tombstoner (Phase 4 #DSAR / SAD §6.6).

Concrete SQL implementations of the protocols declared in
``app.application.services.dsar_service``. The collector produces a JSON-safe
bundle from every aggregate that may carry data tied to a subject; the
tombstoner overwrites the User PII fields and the Person emergency-contact /
service-history columns while preserving row identity (so audit-chain links
remain valid). Encrypted clinical fields keep their ciphertexts; without the
session key the data is already opaque, and the row identity is what audit
trails rely on.
"""

from __future__ import annotations

import hashlib
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.value_objects.core import PersonId, TenantId
from app.infrastructure.models.care_callback_model import OutreachRecordModel
from app.infrastructure.models.engagement_model import EngagementModel
from app.infrastructure.models.person_model import PersonModel
from app.infrastructure.models.service_session_model import ServiceSessionModel
from app.infrastructure.models.user_model import UserModel


class SqlDSARDataCollector:
    """Walks Person → User and the cross-aggregate references to that subject."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def collect(
        self,
        *,
        tenant_id: TenantId,
        subject_person_id: PersonId,
    ) -> dict[str, Any]:
        person = await self._session.get(PersonModel, subject_person_id.value)
        if person is None or person.tenant_id != tenant_id.value:
            return {
                "person": None,
                "user": None,
                "service_sessions": [],
                "outreach_records": [],
                "engagement_hours": [],
                "note": "Subject not found in this tenant",
            }
        user = await self._session.get(UserModel, person.user_id) if person.user_id else None
        sessions = (
            (
                await self._session.execute(
                    select(ServiceSessionModel).where(
                        ServiceSessionModel.tenant_id == tenant_id.value,
                        ServiceSessionModel.person_id == subject_person_id.value,
                    )
                )
            )
            .scalars()
            .all()
        )
        outreach = (
            (
                await self._session.execute(
                    select(OutreachRecordModel).where(
                        OutreachRecordModel.tenant_id == tenant_id.value,
                        OutreachRecordModel.person_id == subject_person_id.value,
                    )
                )
            )
            .scalars()
            .all()
        )
        engagements = (
            (
                await self._session.execute(
                    select(EngagementModel).where(
                        EngagementModel.tenant_id == tenant_id.value,
                    )
                )
            )
            .scalars()
            .all()
        )
        engagement_hours: list[dict[str, Any]] = []
        if user is not None:
            for eng in engagements:
                for entry in eng.hours_log or []:
                    if entry.get("user_id") == person.user_id:
                        engagement_hours.append({**entry, "engagement_id": eng.id})
        return {
            "person": {
                "id": person.id,
                "person_type": person.person_type,
                "status": person.status,
                "user_id": person.user_id,
                "emergency_contact": person.emergency_contact,
                "employment_info": person.employment_info,
                "license_info": person.license_info,
                "provider_profile": person.provider_profile,
                "dependent_info": person.dependent_info,
                "staff_info": person.staff_info,
                "created_at": person.created_at.isoformat() if person.created_at else None,
            },
            "user": {
                "id": user.id,
                "email": user.email,
                "status": user.status,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }
            if user is not None
            else None,
            "service_sessions": [
                {
                    "id": s.id,
                    "service_id": s.service_id,
                    "scheduled_at": s.scheduled_at.isoformat() if s.scheduled_at else None,
                    "status": s.status,
                    "reschedule_count": s.reschedule_count,
                }
                for s in sessions
            ],
            "outreach_records": [
                {
                    "id": o.id,
                    "campaign_id": o.campaign_id,
                    "status": o.status,
                    "contact_attempts": o.contact_attempts,
                    "triage_instrument_code": o.triage_instrument_code,
                    "triage_risk_level": o.triage_risk_level,
                    "crisis_flag": o.crisis_flag,
                    "created_at": o.created_at.isoformat() if o.created_at else None,
                }
                for o in outreach
            ],
            "engagement_hours": engagement_hours,
            "generated_for_subject": subject_person_id.value,
        }


def _make_tombstone_token(subject_person_id: str, salt: str = "evexia-dsar-v1") -> str:
    return hashlib.sha256(f"{salt}:{subject_person_id}".encode()).hexdigest()[:16]


class SqlDSARTombstoner:
    """Overwrites User PII and Person history fields; keeps row identity."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def tombstone(
        self,
        *,
        tenant_id: TenantId,
        subject_person_id: PersonId,
    ) -> str:
        person = await self._session.get(PersonModel, subject_person_id.value)
        if person is None or person.tenant_id != tenant_id.value:
            raise ValueError(
                f"Subject not found in tenant {tenant_id.value}: {subject_person_id.value}"
            )
        token = _make_tombstone_token(subject_person_id.value)
        synthetic_email = f"tombstone-{token}@erased.local"

        user = await self._session.get(UserModel, person.user_id) if person.user_id else None
        if user is not None:
            user.email = synthetic_email
            user.password_hash = None
            user.last_login_at = None

        person.emergency_contact = None
        person.last_service_date = None
        # employment_info / license_info / dependent_info contain PII; null them too.
        person.employment_info = None
        person.license_info = None
        person.dependent_info = None
        person.staff_info = None

        await self._session.flush()
        return token
