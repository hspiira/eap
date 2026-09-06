"""Every script under scripts/ must be runnable as a script.

`python scripts/foo.py` puts scripts/ on sys.path, not the repo root, so a
script that imports `app.*` without inserting the project root dies with
ModuleNotFoundError. scripts/outbox_worker.py shipped that way: the audit
worker could not start at all, which stays invisible while tests only import
its functions instead of running the process.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

APP_SCRIPTS = sorted(
    path.name
    for path in SCRIPTS_DIR.glob("*.py")
    if path.name != "__init__.py" and "from app" in path.read_text()
)


def _env() -> dict[str, str]:
    """Config the app package needs at import time, with an unusable database."""
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", "/tmp"),
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@127.0.0.1:1/nonexistent",
        "SECRET_KEY": "test-secret-key-at-least-32-characters-long",
        "ALGORITHM": "HS256",
        "ENVIRONMENT": "test",
    }


def test_app_scripts_are_discovered():
    """Guard the guard: an empty parametrize list would pass vacuously."""
    assert "outbox_worker.py" in APP_SCRIPTS


@pytest.mark.parametrize("script", APP_SCRIPTS)
def test_script_resolves_the_app_package_when_run_as_a_script(script: str):
    """Execute the script's imports the way `python scripts/x.py` would.

    Runs from outside the project root so a script relying on the working
    directory fails here rather than in a deployed container.
    """
    path = SCRIPTS_DIR / script
    # Mirror the interpreter's own behaviour: scripts/ leads sys.path, and the
    # project root is absent unless the script inserts it.
    program = (
        f"import sys; sys.path.insert(0, {str(SCRIPTS_DIR)!r}); "
        f"source = open({str(path)!r}).read().split('if __name__')[0]; "
        f"exec(compile(source, {script!r}, 'exec'), {{'__name__': 'not_main', '__file__': {str(path)!r}}})"
    )
    result = subprocess.run(
        [sys.executable, "-c", program],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=PROJECT_ROOT.parent,
        env=_env(),
    )
    assert "ModuleNotFoundError" not in result.stderr, (
        f"{script} cannot import its dependencies when run as a script:\n{result.stderr}"
    )
    assert result.returncode == 0, result.stderr
