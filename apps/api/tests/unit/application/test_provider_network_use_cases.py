"""Affiliation creation: overlap rejection, concurrent firms, tenant scoping."""

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.use_cases.provider_network_use_cases import (
    AffiliationOverlapError,
    ChangeAffiliationEndUseCase,
    CreateAffiliationUseCase,
    CreateOrganisationUseCase,
    OrganisationInput,
)
from app.domain.entities.provider_affiliation import ProviderAffiliationEntity
from app.domain.entities.provider_organisation import ProviderOrganisationEntity
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.value_objects.core import ProviderId, TenantId, UserId
from app.domain.value_objects.provider_network import (
    ProviderAffiliationId,
    ProviderOrganisationId,
)

TENANT = TenantId("t-1")
PROV = ProviderId("prov-1")
ORG = ProviderOrganisationId("org-1")
OTHER_ORG = ProviderOrganisationId("org-2")
ACTOR = UserId("u-1")
NOW = datetime(2026, 9, 6, tzinfo=UTC)


def _organisation(org_id=ORG) -> ProviderOrganisationEntity:
    return ProviderOrganisationEntity(
        id=org_id, tenant_id=TENANT, name="Firm", created_at=NOW, updated_at=NOW
    )


def _existing(valid_from=date(2026, 1, 1), valid_until=date(2026, 7, 1)):
    return ProviderAffiliationEntity(
        id=ProviderAffiliationId("aff-existing"),
        tenant_id=TENANT,
        provider_id=PROV,
        organisation_id=ORG,
        valid_from=valid_from,
        valid_until=valid_until,
        created_at=NOW,
        updated_at=NOW,
    )


def _repos(*, overlapping=(), organisation=None):
    affiliations = AsyncMock()
    affiliations.find_overlapping.return_value = list(overlapping)
    organisations = AsyncMock()
    organisations.get_organisation.return_value = (
        organisation if organisation is not None else _organisation()
    )
    return affiliations, organisations


class TestCreateAffiliation:
    async def test_a_non_overlapping_affiliation_is_created(self):
        affiliations, organisations = _repos()
        result = await CreateAffiliationUseCase(affiliations, organisations).execute(
            TENANT,
            provider_id=PROV,
            organisation_id=ORG,
            valid_from=date(2026, 8, 1),
            valid_until=None,
            actor=ACTOR,
        )
        assert result.provider_id == PROV
        affiliations.save_affiliation.assert_awaited_once()

    async def test_creation_emits_an_auditable_event(self):
        affiliations, organisations = _repos()
        result = await CreateAffiliationUseCase(affiliations, organisations).execute(
            TENANT,
            provider_id=PROV,
            organisation_id=ORG,
            valid_from=date(2026, 8, 1),
            valid_until=None,
            actor=ACTOR,
        )
        assert [type(e).__name__ for e in result.events] == ["ProviderAffiliationCreated"]

    async def test_an_overlap_is_rejected_and_nothing_is_saved(self):
        affiliations, organisations = _repos(overlapping=[_existing()])
        with pytest.raises(AffiliationOverlapError) as caught:
            await CreateAffiliationUseCase(affiliations, organisations).execute(
                TENANT,
                provider_id=PROV,
                organisation_id=ORG,
                valid_from=date(2026, 3, 1),
                valid_until=date(2026, 4, 1),
                actor=ACTOR,
            )
        affiliations.save_affiliation.assert_not_awaited()
        assert caught.value.http_status == 409
        assert caught.value.error_code == "AFFILIATION_OVERLAP"
        assert caught.value.conflict.id.value == "aff-existing"

    async def test_the_error_names_the_conflicting_affiliation_and_its_dates(self):
        affiliations, organisations = _repos(overlapping=[_existing()])
        with pytest.raises(AffiliationOverlapError) as caught:
            await CreateAffiliationUseCase(affiliations, organisations).execute(
                TENANT,
                provider_id=PROV,
                organisation_id=ORG,
                valid_from=date(2026, 3, 1),
                valid_until=None,
                actor=ACTOR,
            )
        assert "aff-existing" in str(caught.value)
        assert "2026-01-01" in str(caught.value)

    async def test_an_open_ended_conflict_is_described_as_open_ended(self):
        affiliations, organisations = _repos(overlapping=[_existing(valid_until=None)])
        with pytest.raises(AffiliationOverlapError) as caught:
            await CreateAffiliationUseCase(affiliations, organisations).execute(
                TENANT,
                provider_id=PROV,
                organisation_id=ORG,
                valid_from=date(2026, 3, 1),
                valid_until=None,
                actor=ACTOR,
            )
        assert "open-ended" in str(caught.value)

    async def test_the_error_points_at_valid_until_when_the_new_start_is_earlier(self):
        """A form should attach the message to the field the caller can move."""
        affiliations, organisations = _repos(overlapping=[_existing()])
        with pytest.raises(AffiliationOverlapError) as caught:
            await CreateAffiliationUseCase(affiliations, organisations).execute(
                TENANT,
                provider_id=PROV,
                organisation_id=ORG,
                valid_from=date(2025, 6, 1),
                valid_until=date(2026, 2, 1),
                actor=ACTOR,
            )
        assert caught.value.field == "valid_until"

    async def test_the_error_points_at_valid_from_when_the_new_start_is_inside(self):
        affiliations, organisations = _repos(overlapping=[_existing()])
        with pytest.raises(AffiliationOverlapError) as caught:
            await CreateAffiliationUseCase(affiliations, organisations).execute(
                TENANT,
                provider_id=PROV,
                organisation_id=ORG,
                valid_from=date(2026, 3, 1),
                valid_until=None,
                actor=ACTOR,
            )
        assert caught.value.field == "valid_from"

    async def test_concurrent_affiliations_with_different_firms_are_allowed(self):
        """Decision 1 allows a practitioner to work for two firms at once.

        The overlap query is scoped to one pair, so a second firm over the same
        dates finds no conflict.
        """
        affiliations, organisations = _repos()
        affiliations.find_overlapping.return_value = []
        await CreateAffiliationUseCase(affiliations, organisations).execute(
            TENANT,
            provider_id=PROV,
            organisation_id=OTHER_ORG,
            valid_from=date(2026, 1, 1),
            valid_until=date(2026, 7, 1),
            actor=ACTOR,
        )
        args, _ = affiliations.find_overlapping.call_args
        assert OTHER_ORG in args
        affiliations.save_affiliation.assert_awaited_once()

    async def test_an_unknown_organisation_is_rejected_before_any_write(self):
        affiliations, organisations = _repos(organisation=None)
        organisations.get_organisation.return_value = None
        with pytest.raises(NotFoundError):
            await CreateAffiliationUseCase(affiliations, organisations).execute(
                TENANT,
                provider_id=PROV,
                organisation_id=ORG,
                valid_from=date(2026, 1, 1),
                valid_until=None,
                actor=ACTOR,
            )
        affiliations.save_affiliation.assert_not_awaited()
        affiliations.find_overlapping.assert_not_awaited()


class TestChangeAffiliationEnd:
    async def test_moving_the_end_excludes_the_affiliation_from_its_own_check(self):
        affiliations = AsyncMock()
        affiliations.get_affiliation.return_value = _existing()
        affiliations.find_overlapping.return_value = []
        await ChangeAffiliationEndUseCase(affiliations).execute(
            TENANT,
            ProviderAffiliationId("aff-existing"),
            valid_until=date(2026, 9, 1),
            actor=ACTOR,
            reason="Contract extended",
        )
        _, kwargs = affiliations.find_overlapping.call_args
        assert kwargs["exclude_id"].value == "aff-existing"

    async def test_extending_into_a_later_affiliation_is_rejected(self):
        affiliations = AsyncMock()
        affiliations.get_affiliation.return_value = _existing()
        affiliations.find_overlapping.return_value = [
            _existing(valid_from=date(2026, 9, 1), valid_until=None)
        ]
        with pytest.raises(AffiliationOverlapError):
            await ChangeAffiliationEndUseCase(affiliations).execute(
                TENANT,
                ProviderAffiliationId("aff-existing"),
                valid_until=date(2026, 12, 1),
                actor=ACTOR,
                reason="Extend",
            )
        affiliations.save_affiliation.assert_not_awaited()

    async def test_a_missing_affiliation_is_a_not_found(self):
        affiliations = AsyncMock()
        affiliations.get_affiliation.return_value = None
        with pytest.raises(NotFoundError):
            await ChangeAffiliationEndUseCase(affiliations).execute(
                TENANT,
                ProviderAffiliationId("nope"),
                valid_until=None,
                actor=ACTOR,
                reason="x",
            )

    async def test_a_blank_reason_is_rejected(self):
        affiliations = AsyncMock()
        affiliations.get_affiliation.return_value = _existing()
        affiliations.find_overlapping.return_value = []
        with pytest.raises(DomainError):
            await ChangeAffiliationEndUseCase(affiliations).execute(
                TENANT,
                ProviderAffiliationId("aff-existing"),
                valid_until=date(2026, 9, 1),
                actor=ACTOR,
                reason="  ",
            )


class TestCreateOrganisation:
    async def test_a_duplicate_name_in_the_tenant_is_rejected(self):
        organisations = AsyncMock()
        organisations.name_exists.return_value = True
        with pytest.raises(DomainError):
            await CreateOrganisationUseCase(organisations).execute(
                TENANT, OrganisationInput(name="Firm"), ACTOR
            )
        organisations.save_organisation.assert_not_awaited()

    async def test_a_new_organisation_starts_pending_and_cannot_deliver(self):
        organisations = AsyncMock()
        organisations.name_exists.return_value = False
        result = await CreateOrganisationUseCase(organisations).execute(
            TENANT, OrganisationInput(name="  Firm  "), ACTOR
        )
        assert result.name == "Firm"
        assert result.can_deliver() is False
        assert [type(e).__name__ for e in result.events] == ["ProviderOrganisationCreated"]
