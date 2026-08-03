from enum import Enum


class TenantStatus(str, Enum):
    ACTIVE = "Active"
    SUSPENDED = "Suspended"
    TERMINATED = "Terminated"
    ARCHIVED = "Archived"


class TenantRole(str, Enum):
    """Role within a tenant for RBAC. ADMIN can manage tenant and users."""

    ADMIN = "Admin"
    USER = "User"
    VIEWER = "Viewer"


class SubscriptionTier(str, Enum):
    FREE = "Free"
    BASIC = "Basic"
    PROFESSIONAL = "Professional"
    ENTERPRISE = "Enterprise"


class TenantConsentStatus(str, Enum):
    ACTIVE = "Active"
    WITHDRAWN = "Withdrawn"


class AccessScope(str, Enum):
    """Per-user grants that gate the clinical / employer bounded contexts.

    CLINICAL guards PHI surfaces (cases, clinical notes, EAP programmes).
    Nobody holds it by default; platform admins grant it to counsellors.
    Employer HR must never see clinical data — that is the product's core
    privacy promise, so clinical routes fail closed on a missing grant.
    Platform-admin status stays tenant-based and does NOT imply CLINICAL.
    """

    CLINICAL = "Clinical"
    EMPLOYER_PORTAL = "EmployerPortal"
