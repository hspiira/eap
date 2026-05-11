"""Privacy-wall access-scope guard tests."""

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.authorization import (
    require_clinical_scope,
    require_employer_scope,
    require_scope,
)
from app.core.security import TokenData, get_current_user
from app.domain.enums import AccessScope


def _build_app(scopes: list[str]):
    app = FastAPI()

    async def _fake_user() -> TokenData:
        return TokenData(
            user_id="u-1",
            tenant_id="t-1",
            access_scopes=scopes,
        )

    app.dependency_overrides[get_current_user] = _fake_user

    @app.get("/clinical-only")
    async def clinical_only(_: TokenData = Depends(require_clinical_scope)):
        return {"ok": True}

    @app.get("/employer-only")
    async def employer_only(_: TokenData = Depends(require_employer_scope)):
        return {"ok": True}

    fail_closed = require_scope(
        AccessScope.CLINICAL, fail_closed_on_legacy=True
    )

    @app.get("/clinical-strict")
    async def clinical_strict(_: TokenData = Depends(fail_closed)):
        return {"ok": True}

    return app


class TestClinicalScope:
    def test_clinical_token_admitted(self):
        client = TestClient(_build_app([AccessScope.CLINICAL.value]))
        assert client.get("/clinical-only").status_code == 200

    def test_employer_token_refused_on_clinical(self):
        client = TestClient(_build_app([AccessScope.EMPLOYER_PORTAL.value]))
        r = client.get("/clinical-only")
        assert r.status_code == 403
        assert "scope" in r.json()["detail"].lower()

    def test_platform_admin_admitted_everywhere(self):
        client = TestClient(_build_app([AccessScope.PLATFORM_ADMIN.value]))
        assert client.get("/clinical-only").status_code == 200
        assert client.get("/employer-only").status_code == 200


class TestEmployerScope:
    def test_employer_token_admitted(self):
        client = TestClient(_build_app([AccessScope.EMPLOYER_PORTAL.value]))
        assert client.get("/employer-only").status_code == 200

    def test_clinical_token_refused_on_employer(self):
        client = TestClient(_build_app([AccessScope.CLINICAL.value]))
        assert client.get("/employer-only").status_code == 403


class TestLegacyTokens:
    def test_legacy_token_admitted_by_default(self):
        client = TestClient(_build_app([]))
        assert client.get("/clinical-only").status_code == 200
        assert client.get("/employer-only").status_code == 200

    def test_fail_closed_refuses_legacy_tokens(self):
        client = TestClient(_build_app([]))
        r = client.get("/clinical-strict")
        assert r.status_code == 403
