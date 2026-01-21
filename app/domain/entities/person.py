"""
Person Entity (Aggregate Root)

Represents a uniquely identifiable person within the EAP domain.
Identity and lifecycle define the entity, not role-specific attributes.

Supports multiple person types via a discriminator:
- PLATFORM_STAFF
- CLIENT_EMPLOYEE
- DEPENDENT
- SERVICE_PROVIDER

Responsibilities:
- Enforce type-specific business rules and invariants
- Manage lifecycle (activation, deactivation)
- Determine service eligibility
- Handle dual roles where permitted
- Maintain dependent → employee relationships

Key Invariants:
- Dependents must have a primary employee and no dual roles
- Service providers must have valid licenses
- Client employees must have valid employment details
- Eligibility depends on status, type, and relationships

Design Notes:
- Aggregate root for all person-related rules
- Identity-based equality (PersonId)
- Pure domain entity (no persistence or framework concerns)
"""
