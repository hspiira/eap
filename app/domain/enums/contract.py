from enum import Enum


class ContractStatus(str, Enum):
    ACTIVE = "Active"
    EXPIRED = "Expired"
    TERMINATED = "Terminated"
    RENEWED = "Renewed"
    PENDING = "Pending"
    DRAFT = "Draft"


class PaymentStatus(str, Enum):
    PENDING = "Pending"
    PAID = "Paid"
    OVERDUE = "Overdue"
    CANCELLED = "Cancelled"
    REFUNDED = "Refunded"


class PaymentFrequency(str, Enum):
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    ANNUALLY = "Annually"


class PricingModel(str, Enum):
    """Joseph's five contract pricing strategies (SAD §5.2.3 / Meeting §3).

    RETAINER — fixed periodic fee (e.g. monthly).
    FRAMEWORK — pre-paid deposit drawn down per session.
    FEE_FOR_SERVICE — pay per session at a rate card.
    ADMIN_UTILISATION — admin-fee floor + per-session usage charges above the floor.
    VALUE_ADD — bundled into a broader Minet relationship (no per-EAP invoice).
    """

    RETAINER = "Retainer"
    FRAMEWORK = "Framework"
    FEE_FOR_SERVICE = "FeeForService"
    ADMIN_UTILISATION = "AdminUtilisation"
    VALUE_ADD = "ValueAdd"


class BenchmarkScope(str, Enum):
    """Metric families a tenant can opt into for cross-tenant benchmarking."""

    SESSION_VOLUME = "SessionVolume"
    UTILISATION_RATES = "UtilisationRates"
    SATISFACTION = "Satisfaction"
    CARE_CALLBACK_OUTCOMES = "CareCallbackOutcomes"
