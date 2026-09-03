"""
Base API Schemas

Sanitized string annotations for API request schemas.
Free-text fields use SanitizedStr so stored values are sanitized at the API boundary.
"""

from typing import Annotated

from pydantic import BeforeValidator

from app.shared.utils.sanitization import InputSanitizer


def _sanitize_html(v: str | None) -> str | None:
    """Sanitize string for storage; leave None unchanged."""
    if v is None:
        return None
    if isinstance(v, str):
        return InputSanitizer.sanitize_html(v)
    return v


# Use for free-text request fields (name, description, reason, notes, address, etc.)
SanitizedStr = Annotated[str, BeforeValidator(_sanitize_html)]
OptionalSanitizedStr = Annotated[str | None, BeforeValidator(_sanitize_html)]
