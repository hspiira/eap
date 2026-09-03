from enum import Enum


class DocumentType(str, Enum):
    """Types of documents in the system."""

    CONTRACT = "Contract"
    CERTIFICATION = "Certification"
    KPI_REPORT = "KPI Report"
    FEEDBACK_SUMMARY = "Feedback Summary"
    BILLING_REPORT = "Billing Report"
    UTILIZATION_REPORT = "Utilization Report"
    OTHER = "Other"


class DocumentStatus(str, Enum):
    """Status of a document."""

    DRAFT = "Draft"
    PUBLISHED = "Published"
    ARCHIVED = "Archived"
    EXPIRED = "Expired"
