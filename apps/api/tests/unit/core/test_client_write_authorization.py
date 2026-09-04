import pytest
from fastapi import HTTPException

from app.core.authorization import require_not_viewer
from app.core.security import TokenData


@pytest.mark.asyncio
async def test_viewer_role_is_case_insensitive() -> None:
    with pytest.raises(HTTPException) as error:
        await require_not_viewer(
            TokenData(user_id="user-1", tenant_id="tenant-1", role="VIEWER")
        )

    assert error.value.status_code == 403


@pytest.mark.asyncio
async def test_user_role_can_write() -> None:
    user = TokenData(user_id="user-1", tenant_id="tenant-1", role="User")

    assert await require_not_viewer(user) == user
