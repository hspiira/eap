"""
Audit Filter Service

Provides configurable filtering and sampling for audit logging to prevent
storage bloat from high-volume read operations (LIST, VIEW actions).

This service implements:
- Sampling: Log only a percentage of LIST/VIEW actions based on sample rate
- Allowlist: Always log specific resource types regardless of sample rate
- Denylist: Never log specific resource types for LIST/VIEW actions
- Full logging: Always log CREATE/UPDATE/DELETE and other critical actions
"""

import random
from typing import TYPE_CHECKING

from app.core.config import settings
from app.domain.enums import AuditActionType

if TYPE_CHECKING:
    pass


class AuditFilterService:
    """
    Service for determining whether an audit action should be logged.
    
    Implements configurable filtering to prevent audit log bloat from
    high-volume read operations while ensuring critical actions are always logged.
    """

    # High-volume action types that should be filtered/sampled
    HIGH_VOLUME_ACTIONS = {AuditActionType.LIST, AuditActionType.VIEW}

    # Critical action types that should always be logged
    CRITICAL_ACTIONS = {
        AuditActionType.CREATE,
        AuditActionType.UPDATE,
        AuditActionType.DELETE,
        AuditActionType.LOGIN,
        AuditActionType.LOGOUT,
        AuditActionType.APPROVE,
        AuditActionType.REJECT,
        AuditActionType.EXPORT,
        AuditActionType.IMPORT,
    }

    @classmethod
    def should_log_action(
        cls,
        action_type: AuditActionType,
        resource_type: str | None = None,
    ) -> bool:
        """
        Determine if an audit action should be logged.
        
        Rules:
        1. Critical actions (CREATE/UPDATE/DELETE/etc.) are always logged
        2. High-volume actions (LIST/VIEW) are subject to filtering:
           - Check if resource is in skip list -> don't log
           - Check if resource is in always-log list -> log
           - Otherwise, apply sampling based on AUDIT_SAMPLE_RATE
        
        Args:
            action_type: The audit action type
            resource_type: Optional resource type (e.g., "Person", "Client")
            
        Returns:
            True if action should be logged, False otherwise
        """
        # Always log critical actions
        if action_type in cls.CRITICAL_ACTIONS:
            return True

        # Only apply filtering to high-volume actions
        if action_type not in cls.HIGH_VOLUME_ACTIONS:
            # Unknown action type - log it to be safe
            return True

        # High-volume action - apply filtering rules
        resource_type_normalized = (resource_type or "").strip()

        # Check skip list first
        skip_list = settings.audit_skip_resources_list
        if resource_type_normalized in skip_list:
            return False

        # Check always-log list
        always_log_list = settings.audit_always_log_resources_list
        if resource_type_normalized in always_log_list:
            return True

        # Apply sampling
        sample_rate = settings.AUDIT_SAMPLE_RATE
        if sample_rate >= 1.0:
            # Log all (100% sample rate)
            return True
        if sample_rate <= 0.0:
            # Log none (0% sample rate)
            return False

        # Random sampling: return True with probability = sample_rate
        return random.random() < sample_rate
