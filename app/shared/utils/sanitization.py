"""Input sanitization utilities."""

import nh3
import re
from typing import Any, ClassVar


class InputSanitizer:
    """Sanitize user inputs to prevent XSS and injection attacks."""

    # Allowed HTML tags (empty for strict sanitization)
    ALLOWED_TAGS: ClassVar[list[str]] = []

    # Allowed HTML attributes
    ALLOWED_ATTRIBUTES: ClassVar[dict[str, list[str]]] = {}

    # Regex for validating identifiers
    IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

    # Regex for SQL-safe strings
    SQL_SAFE_PATTERN = re.compile(r"^[a-zA-Z0-9_\-\s]+$")

    @classmethod
    def sanitize_html(cls, value: str) -> str:
        """Remove all HTML tags and entities."""
        if not value:
            return value
        return nh3.clean(
            value,
            tags=set(cls.ALLOWED_TAGS),
            attributes=cls.ALLOWED_ATTRIBUTES,
        )

    @classmethod
    def sanitize_identifier(cls, value: str) -> str:
        """
        Sanitize identifiers (IDs, codes, etc.).

        Only allows alphanumeric characters, underscores, and hyphens.
        """
        if not value:
            return value

        if not cls.IDENTIFIER_PATTERN.match(value):
            raise ValueError("Invalid identifier format")

        return value

    @classmethod
    def sanitize_sql_string(cls, value: str) -> str:
        """
        Basic SQL injection prevention.

        Note: Always use parameterized queries as primary defense.
        """
        if not value:
            return value

        # Allowlist validation to avoid lossy transforms
        if not cls.SQL_SAFE_PATTERN.match(value):
            raise ValueError("Unsafe SQL string")
        return value

    @classmethod
    def sanitize_dict(cls, data: dict[str, Any], max_depth: int = 100) -> dict[str, Any]:
        """
        Recursively sanitize dictionary values.
        
        Args:
            data: Dictionary to sanitize
            max_depth: Maximum recursion depth (default 100)
            
        Returns:
            Sanitized dictionary
            
        Raises:
            ValueError: If max_depth <= 0
        """
        if max_depth <= 0:
            raise ValueError("Maximum recursion depth exceeded or invalid max_depth")
        
        sanitized = {}

        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = cls.sanitize_html(value)
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_dict(value, max_depth=max_depth - 1)
            elif isinstance(value, list):
                sanitized[key] = cls.sanitize_list(value, max_depth=max_depth - 1)
            else:
                sanitized[key] = value

        return sanitized

    @classmethod
    def sanitize_list(cls, data: list[Any], max_depth: int = 100) -> list[Any]:
        """
        Recursively sanitize list values.
        
        Args:
            data: List to sanitize
            max_depth: Maximum recursion depth (default 100)
            
        Returns:
            Sanitized list
            
        Raises:
            ValueError: If max_depth <= 0
        """
        if max_depth <= 0:
            raise ValueError("Maximum recursion depth exceeded or invalid max_depth")
        
        sanitized = []

        for item in data:
            if isinstance(item, str):
                sanitized.append(cls.sanitize_html(item))
            elif isinstance(item, dict):
                sanitized.append(cls.sanitize_dict(item, max_depth=max_depth - 1))
            elif isinstance(item, list):
                sanitized.append(cls.sanitize_list(item, max_depth=max_depth - 1))
            else:
                sanitized.append(item)

        return sanitized


# Convenience functions
def sanitize_input(value: str | dict | list) -> str | dict | list:
    """Sanitize any input value."""
    if isinstance(value, str):
        return InputSanitizer.sanitize_html(value)
    elif isinstance(value, dict):
        return InputSanitizer.sanitize_dict(value)
    elif isinstance(value, list):
        return InputSanitizer.sanitize_list(value)
    return value


def validate_identifier(value: str) -> str:
    """Validate and return identifier."""
    return InputSanitizer.sanitize_identifier(value)
