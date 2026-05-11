"""Cell-suppression policy tests."""

import pytest

from app.domain.services.cell_suppression import (
    DEFAULT_MIN_CELL_SIZE,
    MinimumCellSize,
    is_suppressed,
    suppress_bucket_list,
    suppress_count,
    suppress_count_dict,
)


class TestMinimumCellSize:
    def test_default_is_five(self):
        assert MinimumCellSize().floor == 5
        assert DEFAULT_MIN_CELL_SIZE == 5

    def test_floor_below_one_rejected(self):
        with pytest.raises(ValueError):
            MinimumCellSize(floor=0)

    def test_custom_floor_honoured(self):
        assert MinimumCellSize(floor=10).floor == 10


class TestSuppressCount:
    def test_value_above_floor_passes_through(self):
        assert suppress_count(7) == 7

    def test_value_at_floor_passes_through(self):
        assert suppress_count(5) == 5

    def test_value_below_floor_replaced(self):
        assert suppress_count(2) == "<5"

    def test_custom_floor(self):
        assert suppress_count(8, floor=10) == "<10"
        assert suppress_count(11, floor=10) == 11


class TestSuppressCountDict:
    def test_mixed_dict(self):
        out = suppress_count_dict({"a": 7, "b": 2, "c": 0})
        assert out == {"a": 7, "b": "<5", "c": "<5"}

    def test_empty_dict(self):
        assert suppress_count_dict({}) == {}


class TestSuppressBucketList:
    def test_replaces_count_below_floor(self):
        out = suppress_bucket_list(
            [{"month": "2026-01", "count": 12}, {"month": "2026-02", "count": 3}]
        )
        assert out[0]["count"] == 12
        assert out[1]["count"] == "<5"
        assert out[1]["month"] == "2026-02"

    def test_drop_below_floor(self):
        out = suppress_bucket_list(
            [{"month": "2026-01", "count": 12}, {"month": "2026-02", "count": 3}],
            drop_below_floor=True,
        )
        assert len(out) == 1
        assert out[0]["month"] == "2026-01"

    def test_custom_count_field(self):
        out = suppress_bucket_list(
            [{"diagnosis": "PHQ9-mild", "n": 2}],
            count_field="n",
        )
        assert out[0]["n"] == "<5"

    def test_non_int_value_left_alone(self):
        out = suppress_bucket_list([{"month": "2026-01", "count": "n/a"}])
        assert out[0]["count"] == "n/a"


class TestIsSuppressed:
    def test_suppressed_string(self):
        assert is_suppressed("<5")
        assert is_suppressed("<10")

    def test_int_not_suppressed(self):
        assert not is_suppressed(7)
        assert not is_suppressed(0)
