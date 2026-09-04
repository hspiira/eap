"""
Document path and URL validation for security (path traversal, SSRF).

Used when accepting file_path or file_url from clients for document create/update.
"""

import ipaddress
import re
from pathlib import Path
from urllib.parse import urlparse

# Textual hosts and dotted prefixes that never leave the machine or its private
# network. Kept as a literal check because it also catches the shorthand dotted
# forms (127.1) that ipaddress refuses to parse.
_PRIVATE_HOST_PATTERN = re.compile(
    r"^localhost$|^localhost\.localdomain$|^127\.|^10\.|"
    r"^172\.(1[6-9]|2[0-9]|3[0-1])\.|^192\.168\.|^169\.254\.|"
    r"^::1$|^\[::1\]$|^0\.0\.0\.0$",
    re.IGNORECASE,
)


def _parse_host_ip(host: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    """Parse a URL host as an IP address, accepting the encodings HTTP clients accept.

    A dotted quad, an IPv6 literal, and the decimal, hexadecimal and octal forms
    of an IPv4 address all reach the same host, so all of them must parse here.
    """
    if host.startswith(("0x", "0X")):
        try:
            return ipaddress.ip_address(int(host, 16))
        except ValueError:
            return None
    if host.isdigit():
        base = 8 if host.startswith("0") and len(host) > 1 else 10
        try:
            return ipaddress.ip_address(int(host, base))
        except ValueError:
            return None
    try:
        return ipaddress.ip_address(host)
    except ValueError:
        return None


def _is_local_or_private_host(host: str) -> bool:
    """True when the host points inside the network the server itself sits on."""
    if _PRIVATE_HOST_PATTERN.search(host):
        return True
    ip = _parse_host_ip(host)
    if ip is None:
        return False
    mapped = getattr(ip, "ipv4_mapped", None)
    if mapped is not None:
        ip = mapped
    return (
        ip.is_loopback
        or ip.is_private
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_unspecified
        or ip.is_multicast
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
    if _is_local_or_private_host(host):
        raise ValueError("Invalid document URL: localhost and private IP addresses are not allowed")
    return value
