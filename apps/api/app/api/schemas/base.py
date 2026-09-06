"""
Base API Schemas

Sanitized string annotations for API request schemas.
Free-text fields use SanitizedStr so stored values are sanitized at the API boundary.
"""

from typing import Annotated

from pydantic import AfterValidator, BeforeValidator, Field

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


def _require_non_blank(value: str) -> str:
    """Reject whitespace-only input, and store the stripped value.

    `min_length` is checked before stripping, so "   " satisfies it and reaches
    the domain, which rejects it as a 400 with nothing a form can attach to a
    field. Stripping here gives every blank variant the same 422 field error.
    The domain check stays: it is the invariant, this is only what makes the
    response usable.
    """
    stripped = value.strip()
    if not stripped:
        raise ValueError("must not be blank")
    return stripped


def non_blank(max_length: int):
    """A required text field that rejects whitespace-only input with a 422."""
    return Annotated[SanitizedStr, Field(max_length=max_length), AfterValidator(_require_non_blank)]


NonBlankReason = non_blank(500)
