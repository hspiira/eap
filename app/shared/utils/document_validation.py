"""
Document path and URL validation for security (path traversal, SSRF).

Used when accepting file_path or file_url from clients for document create/update.
"""

import re
from pathlib import Path
from urllib.parse import urlparse

# Private IP ranges and localhost (for SSRF prevention)
_PRIVATE_IP_PATTERN = re.compile(
    r"^localhost$|^127\.|^10\.|^172\.(1[6-9]|2[0-9]|3[0-1])\.|^192\.168\.|^169\.254\.|^::1$|^\[::1\]$|^0\.0\.0\.0$",
    re.IGNORECASE,
)


def validate_document_file_path(value: str | None, upload_root: str) -> str | None:
    """
    Validate and normalize document file_path. Reject path traversal and absolute paths.

    Args:
        value: Client-supplied file path (relative or absolute).
        upload_root: Application upload root directory (e.g. from settings).

    Returns:
        Normalized path relative to upload root, or None if value is None.

    Raises:
        ValueError: If path escapes upload root (e.g. ..) or is absolute.
    """
    if value is None or not value.strip():
        return None
    value = value.strip()
    if value.startswith("/") or (len(value) >= 2 and value[1] == ":"):
        raise ValueError("Invalid file path: absolute paths are not allowed")
    if ".." in value:
        raise ValueError("Invalid file path: path cannot contain '..'")
    root = Path(upload_root).resolve()
    try:
        resolved = (root / value).resolve()
        return str(resolved.relative_to(root))
    except (ValueError, OSError) as err:
        raise ValueError(
            "Invalid file path: path must be relative and cannot escape upload directory"
        ) from err


def validate_document_file_url(value: str | None, allowed_schemes: list[str]) -> str | None:
    """
    Validate document file_url. Reject file://, localhost, and private IPs (SSRF).

    Args:
        value: Client-supplied URL.
        allowed_schemes: Allowed schemes (e.g. ['https']).

    Returns:
        The value if valid, or None if value is None.

    Raises:
        ValueError: If scheme not allowed or host is local/private.
    """
    if value is None or not value.strip():
        return None
    value = value.strip()
    parsed = urlparse(value)
    scheme = (parsed.scheme or "").lower()
    if scheme not in [s.lower() for s in allowed_schemes]:
        raise ValueError(
            f"Invalid document URL: only {', '.join(allowed_schemes)} schemes are allowed"
        )
    host = (parsed.hostname or "").lower()
    if _PRIVATE_IP_PATTERN.search(host):
        raise ValueError("Invalid document URL: localhost and private IP addresses are not allowed")
    return value
