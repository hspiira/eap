from enum import Enum


class ReportQueryType(str, Enum):
    """Library of canned report queries (SAD §5.2.10).

    Each value maps to a single :class:`~app.application.services.report_query_runner.QueryRunner`
    method. New queries are added by extending the enum and adding a runner;
    templates reference them by enum value.
    """

    SESSIONS_BY_MONTH = "sessions_by_month"
    DIAGNOSIS_PREVALENCE = "diagnosis_prevalence"
    CONTRACT_UTILISATION = "contract_utilisation"
    CARE_CALLBACK_OUTCOMES = "care_callback_outcomes"
    SATISFACTION_DISTRIBUTION = "satisfaction_distribution"


class ReportRunStatus(str, Enum):
    """Lifecycle of a single report execution."""

    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"


class AuditActionType(str, Enum):
    """Types of actions that can be audited.

    Note: LIST and VIEW actions are subject to configurable filtering/sampling
    to prevent audit log bloat. Critical actions (CREATE, UPDATE, DELETE, etc.)
    are always logged. See AUDIT_SAMPLE_RATE, AUDIT_ALWAYS_LOG_RESOURCES, and
    AUDIT_SKIP_RESOURCES environment variables for configuration.
    """

    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    LIST = "LIST"  # Subject to filtering/sampling
    VIEW = "VIEW"  # Subject to filtering/sampling
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"
