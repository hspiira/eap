"""Clinical-data classifier tests for the special-category audit flag."""

from app.shared.utils.clinical_data_classification import (
    CLINICAL_RESOURCE_TYPES,
    is_clinical_event,
    is_clinical_resource,
    is_special_category,
)


class TestIsClinicalResource:
    def test_known_clinical_resource(self):
        assert is_clinical_resource("ClinicalSubject")
        assert is_clinical_resource("CrisisContact")
        assert is_clinical_resource("OutreachRecord")

    def test_unknown_resource_is_not_clinical(self):
        assert not is_clinical_resource("Tenant")
        assert not is_clinical_resource("Contract")
        assert not is_clinical_resource("EligibleMember")

    def test_none_is_not_clinical(self):
        assert not is_clinical_resource(None)
        assert not is_clinical_resource("")


class TestIsClinicalEvent:
    def test_substring_match(self):
        assert is_clinical_event("CrisisFlagRaised")
        assert is_clinical_event("TriageRecorded")
        assert is_clinical_event("ClinicalNoteSigned")
        assert is_clinical_event("MandatoryReportSubmitted")

    def test_unrelated_events_skipped(self):
        assert not is_clinical_event("ContractSigned")
        assert not is_clinical_event("UserCreated")

    def test_none_is_not_clinical(self):
        assert not is_clinical_event(None)
        assert not is_clinical_event("")


class TestIsSpecialCategory:
    def test_either_signal_triggers_flag(self):
        assert is_special_category(resource_type="Case")
        assert is_special_category(event_type="CrisisFlagRaised")
        assert is_special_category(
            resource_type="Tenant", event_type="TriageRecorded"
        )

    def test_neither_signal_means_ordinary(self):
        assert not is_special_category(
            resource_type="Tenant", event_type="UserActivated"
        )

    def test_registry_complete_for_listed_aggregates(self):
        for required in {"Case", "ClinicalSubject", "OutreachRecord"}:
            assert required in CLINICAL_RESOURCE_TYPES
