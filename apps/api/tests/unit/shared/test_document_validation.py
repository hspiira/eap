"""
Path-traversal and SSRF cover for the document path and URL validators.

Both functions are the only thing standing between a client-supplied string and
either the filesystem or an outbound request, so the negative cases matter more
than the positive ones. The URL cases include the numeric address encodings an
HTTP client resolves but a textual host check does not recognise.
"""

import pytest

from app.shared.utils.document_validation import (
    validate_document_file_path,
    validate_document_file_url,
)

UPLOAD_ROOT = "/srv/uploads"
HTTPS_ONLY = ["https"]


class TestFilePathAccepted:
    def test_none_and_blank_return_none(self) -> None:
        assert validate_document_file_path(None, UPLOAD_ROOT) is None
        assert validate_document_file_path("", UPLOAD_ROOT) is None
        assert validate_document_file_path("   ", UPLOAD_ROOT) is None

    def test_relative_path_is_normalised_against_the_root(self) -> None:
        assert validate_document_file_path("reports/q1.pdf", UPLOAD_ROOT) == "reports/q1.pdf"

    def test_surrounding_whitespace_is_stripped(self) -> None:
        assert validate_document_file_path("  reports/q1.pdf  ", UPLOAD_ROOT) == "reports/q1.pdf"

    def test_single_dot_segment_collapses(self) -> None:
        assert validate_document_file_path("./reports/q1.pdf", UPLOAD_ROOT) == "reports/q1.pdf"


class TestFilePathRejected:
    def test_absolute_posix_path(self) -> None:
        with pytest.raises(ValueError, match="absolute paths are not allowed"):
            validate_document_file_path("/etc/passwd", UPLOAD_ROOT)

    def test_windows_drive_letter(self) -> None:
        with pytest.raises(ValueError, match="absolute paths are not allowed"):
            validate_document_file_path("C:/windows/system32/config/sam", UPLOAD_ROOT)

    @pytest.mark.parametrize(
        "value",
        [
            "../../etc/passwd",
            "reports/../../etc/passwd",
            "reports/../q1.pdf",
            "..",
        ],
    )
    def test_parent_directory_traversal(self, value: str) -> None:
        with pytest.raises(ValueError, match="cannot contain"):
            validate_document_file_path(value, UPLOAD_ROOT)


class TestFileUrlAccepted:
    def test_none_and_blank_return_none(self) -> None:
        assert validate_document_file_url(None, HTTPS_ONLY) is None
        assert validate_document_file_url("", HTTPS_ONLY) is None
        assert validate_document_file_url("   ", HTTPS_ONLY) is None

    @pytest.mark.parametrize(
        "url",
        [
            "https://example.com/doc.pdf",
            "https://storage.googleapis.com/bucket/object.pdf",
            "https://8.8.8.8/doc.pdf",
            "https://sub.domain.example.co.ug/a/b/c.pdf?x=1",
        ],
    )
    def test_public_https_urls_pass(self, url: str) -> None:
        assert validate_document_file_url(url, HTTPS_ONLY) == url

    def test_scheme_matching_is_case_insensitive(self) -> None:
        url = "HTTPS://example.com/doc.pdf"
        assert validate_document_file_url(url, HTTPS_ONLY) == url


class TestFileUrlSchemeRejected:
    @pytest.mark.parametrize(
        "url",
        [
            "file:///etc/passwd",
            "http://example.com/doc.pdf",
            "ftp://example.com/doc.pdf",
            "gopher://example.com/",
            "data:text/plain;base64,SGVsbG8=",
        ],
    )
    def test_disallowed_schemes(self, url: str) -> None:
        with pytest.raises(ValueError, match="schemes are allowed"):
            validate_document_file_url(url, HTTPS_ONLY)


class TestFileUrlHostRejected:
    """Every one of these reaches the server itself or its private network."""

    @pytest.mark.parametrize(
        "url",
        [
            "https://localhost/doc.pdf",
            "https://localhost.localdomain/doc.pdf",
            "https://127.0.0.1/doc.pdf",
            "https://127.1/doc.pdf",
            "https://0.0.0.0/doc.pdf",
            "https://10.0.0.5/doc.pdf",
            "https://172.16.0.1/doc.pdf",
            "https://192.168.1.1/doc.pdf",
            "https://[::1]/doc.pdf",
        ],
    )
    def test_textual_local_hosts(self, url: str) -> None:
        with pytest.raises(ValueError, match="private IP addresses are not allowed"):
            validate_document_file_url(url, HTTPS_ONLY)

    def test_cloud_metadata_endpoint(self) -> None:
        with pytest.raises(ValueError, match="private IP addresses are not allowed"):
            validate_document_file_url(
                "https://169.254.169.254/latest/meta-data/iam/security-credentials/",
                HTTPS_ONLY,
            )

    @pytest.mark.parametrize(
        ("url", "encoding"),
        [
            ("https://2130706433/doc.pdf", "decimal"),
            ("https://0x7f000001/doc.pdf", "hexadecimal"),
            ("https://017700000001/doc.pdf", "octal"),
            ("https://[::ffff:127.0.0.1]/doc.pdf", "IPv4-mapped IPv6"),
        ],
    )
    def test_alternative_encodings_of_loopback(self, url: str, encoding: str) -> None:
        """A client resolves all of these to 127.0.0.1, so all of them must fail."""
        with pytest.raises(ValueError, match="private IP addresses are not allowed"):
            validate_document_file_url(url, HTTPS_ONLY)

    @pytest.mark.parametrize(
        "url",
        [
            "https://[fd00::1]/doc.pdf",
            "https://[fe80::1]/doc.pdf",
        ],
    )
    def test_ipv6_unique_local_and_link_local(self, url: str) -> None:
        with pytest.raises(ValueError, match="private IP addresses are not allowed"):
            validate_document_file_url(url, HTTPS_ONLY)
