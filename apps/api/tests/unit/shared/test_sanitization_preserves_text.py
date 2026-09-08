"""Sanitising a name must not corrupt it.

`nh3.clean` is an HTML sanitiser, so it escapes bare characters as well as
stripping tags. Every client, service and person whose name contains an
ampersand was stored escaped: "I&M Bank" became "I&amp;M Bank", which is a
corrupted name rather than a safer one. Two of the 43 companies in the
reference workbook are affected.

The pair of concerns is tested together on purpose: the point is that plain
text survives while everything carrying markup is sanitised exactly as before.
"""

import pytest

from app.shared.utils.sanitization import InputSanitizer


class TestPlainTextSurvives:
    @pytest.mark.parametrize(
        "value",
        [
            "I&M Bank",
            "Ministry Of Finance Planning & Economic Development",
            "Tom & Jerry",
            "AT&T",
            "Coaching/Mentorship",
            "Family & Relationship",
            "5 > 3 is true",
            "a < b",
            "quote \" and apostrophe '",
        ],
    )
    def test_text_without_markup_is_stored_as_written(self, value):
        assert InputSanitizer.sanitize_html(value) == value


class TestMarkupIsStillRemoved:
    """Unchanged behaviour: anything carrying markup is sanitised as before."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("<script>alert(1)</script>", ""),
            ("<b>bold</b> text", "bold text"),
            ("Tom & Jerry <img src=x onerror=alert(1)>", "Tom &amp; Jerry "),
            ("<a href='javascript:alert(1)'>click</a>", "click"),
            ("<iframe src='evil'></iframe>", ""),
            ("<div onclick='steal()'>hi</div>", "hi"),
        ],
    )
    def test_markup_is_stripped(self, value, expected):
        assert InputSanitizer.sanitize_html(value) == expected

    @pytest.mark.parametrize(
        "value",
        [
            "<script>alert(1)</script>",
            "<img src=x onerror=alert(1)>",
            "<svg/onload=alert(1)>",
            "<a href='javascript:alert(1)'>x</a>",
            "<iframe src='evil'></iframe>",
        ],
    )
    def test_no_tag_or_handler_survives(self, value):
        cleaned = InputSanitizer.sanitize_html(value)
        assert "<" not in cleaned
        assert "javascript:" not in cleaned
        assert "onerror" not in cleaned and "onload" not in cleaned


def test_an_empty_value_is_unchanged():
    assert InputSanitizer.sanitize_html("") == ""
