"""Production misconfiguration that is silent until it bites.

Both of these are per-instance state that reads as correct on one instance and
is wrong on several, which is what serverless always is. Neither fails a boot,
because a deployment that refuses to start is worse than one that warns, but
neither should be silent either.
"""

import warnings

import pytest

from app.core.config import Settings

BASE = {
    "SECRET_KEY": "x" * 32,
    "DATABASE_URL": "postgresql+asyncpg://u:p@localhost/db",
}


def _settings(**overrides) -> tuple[Settings, list[warnings.WarningMessage]]:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        settings = Settings(**{**BASE, **overrides})
    return settings, list(caught)


def _messages(caught: list[warnings.WarningMessage]) -> str:
    return " ".join(str(w.message) for w in caught)


class TestLoginRateLimitBackend:
    def test_memory_in_production_warns_that_the_limit_is_per_instance(self):
        _, caught = _settings(ENVIRONMENT="production", LOGIN_RATE_LIMIT_BACKEND="memory")
        assert "counted per instance" in _messages(caught)

    def test_redis_in_production_does_not_warn(self):
        _, caught = _settings(
            ENVIRONMENT="production",
            LOGIN_RATE_LIMIT_BACKEND="redis",
            REDIS_URL="redis://localhost:6379/0",
        )
        assert "counted per instance" not in _messages(caught)

    def test_memory_in_development_is_left_alone(self):
        """A developer running one process is the case memory is correct for."""
        _, caught = _settings(ENVIRONMENT="development", LOGIN_RATE_LIMIT_BACKEND="memory")
        assert "counted per instance" not in _messages(caught)


class TestReferenceCacheBackend:
    def test_no_redis_url_in_production_warns_about_stale_vocabulary(self):
        _, caught = _settings(ENVIRONMENT="production")
        assert "reference cache is per-instance" in _messages(caught)

    def test_a_redis_url_in_production_does_not_warn(self):
        _, caught = _settings(ENVIRONMENT="production", REDIS_URL="redis://localhost:6379/0")
        assert "reference cache is per-instance" not in _messages(caught)

    def test_development_without_redis_is_left_alone(self):
        _, caught = _settings(ENVIRONMENT="development")
        assert "reference cache is per-instance" not in _messages(caught)


class TestStillFailsOnWhatItAlreadyFailedOn:
    @pytest.mark.parametrize("missing", ["SECRET_KEY", "DATABASE_URL"])
    def test_a_missing_essential_is_still_an_error_not_a_warning(self, missing):
        with pytest.raises(ValueError, match="Missing required configuration"):
            Settings(**{**BASE, missing: ""})
