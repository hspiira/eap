"""Renewal-pack v1 template seeder tests (Phase 3 #D-Reports v1)."""

import pytest

from app.application.use_cases.report_use_cases import (
    CreateRenewalPackTemplateUseCase,
    RENEWAL_PACK_CODE,
    build_renewal_pack_sections,
)
from app.domain.entities.report import ReportTemplate
from app.domain.enums import ReportQueryType
from app.domain.value_objects.core import TenantId


class _FakeTemplateRepo:
    def __init__(self):
        self.templates: dict[str, ReportTemplate] = {}
        self.by_code: dict[tuple[str, str], ReportTemplate] = {}

    async def get_by_id(self, template_id):
        return self.templates.get(template_id.value)

    async def get_by_code(self, tenant_id, code):
        return self.by_code.get((tenant_id.value, code))

    async def save(self, entity):
        self.templates[entity.id.value] = entity
        self.by_code[(entity.tenant_id.value, entity.code)] = entity

    async def delete(self, entity_id):
        self.templates.pop(entity_id.value, None)

    async def exists(self, entity_id):
        return entity_id.value in self.templates


class TestBuildRenewalPackSections:
    def test_default_has_five_sections(self):
        sections = build_renewal_pack_sections()
        assert len(sections) == 5
        assert {s.query_type for s in sections} == {
            ReportQueryType.SESSIONS_BY_MONTH,
            ReportQueryType.DIAGNOSIS_PREVALENCE,
            ReportQueryType.CARE_CALLBACK_OUTCOMES,
            ReportQueryType.SATISFACTION_DISTRIBUTION,
            ReportQueryType.CONTRACT_UTILISATION,
        }

    def test_client_id_propagates_to_scoped_sections_only(self):
        sections = build_renewal_pack_sections(client_id="client-1")
        by_query = {s.query_type: s for s in sections}
        # Client-scoped sections carry the filter:
        assert by_query[ReportQueryType.CARE_CALLBACK_OUTCOMES].parameters == {
            "client_id": "client-1"
        }
        assert by_query[ReportQueryType.CONTRACT_UTILISATION].parameters == {
            "client_id": "client-1"
        }
        assert by_query[ReportQueryType.SATISFACTION_DISTRIBUTION].parameters == {
            "client_id": "client-1"
        }
        # Sessions stays tenant-wide in v1:
        assert (
            by_query[ReportQueryType.SESSIONS_BY_MONTH].parameters == {}
        )

    def test_every_section_has_a_narrative(self):
        for s in build_renewal_pack_sections():
            assert s.narrative
            assert s.title


class TestRenewalPackSeeder:
    @pytest.mark.asyncio
    async def test_creates_tenant_wide_template(self):
        repo = _FakeTemplateRepo()
        out = await CreateRenewalPackTemplateUseCase(repo).execute(
            tenant_id=TenantId("t-1")
        )
        assert out.code == RENEWAL_PACK_CODE
        assert out.is_active is True
        assert len(out.sections) == 5

    @pytest.mark.asyncio
    async def test_idempotent_when_called_twice(self):
        repo = _FakeTemplateRepo()
        first = await CreateRenewalPackTemplateUseCase(repo).execute(
            tenant_id=TenantId("t-1")
        )
        second = await CreateRenewalPackTemplateUseCase(repo).execute(
            tenant_id=TenantId("t-1")
        )
        assert first.id.value == second.id.value
        assert len(repo.templates) == 1

    @pytest.mark.asyncio
    async def test_per_client_variant_distinct_from_default(self):
        repo = _FakeTemplateRepo()
        default = await CreateRenewalPackTemplateUseCase(repo).execute(
            tenant_id=TenantId("t-1")
        )
        scoped = await CreateRenewalPackTemplateUseCase(repo).execute(
            tenant_id=TenantId("t-1"), client_id="client-1"
        )
        assert default.code != scoped.code
        assert scoped.code.endswith(":client-1")
        assert len(repo.templates) == 2

    @pytest.mark.asyncio
    async def test_per_client_variant_idempotent(self):
        repo = _FakeTemplateRepo()
        a = await CreateRenewalPackTemplateUseCase(repo).execute(
            tenant_id=TenantId("t-1"), client_id="client-1"
        )
        b = await CreateRenewalPackTemplateUseCase(repo).execute(
            tenant_id=TenantId("t-1"), client_id="client-1"
        )
        assert a.id.value == b.id.value
        assert len(repo.templates) == 1
