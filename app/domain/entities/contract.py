"""
Contract Entity

Represents a service agreement between a client and the EAP provider.

Responsibilities:
- Manage contract lifecycle (activate, renew, expire, terminate)
- Validate contract terms and dates
- Track billing state
- Determine service availability

Key Invariants:
- Contract dates must form a valid range
- Termination requires a valid reason
- Billing values must be non-negative
- Only active contracts permit service delivery

Design Notes:
- Aggregate root for all contract-related rules
- Identity-based equality (ContractId)
- Pure domain entity (no persistence or framework concerns)
"""
