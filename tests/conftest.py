"""
Test Configuration and Fixtures

Provides async test client and database fixtures for E2E testing.
"""

from collections.abc import AsyncGenerator
from datetime import date
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.infrastructure.models.base import Base
from app.core.database import get_db
from app.main import app
from app.shared.utils.generators import generate_cuid


# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

# Async session factory for tests
TestAsyncSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.
    
    Creates all tables before the test and drops them after.
    """
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestAsyncSessionLocal() as session:
        yield session
    
    # Drop all tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async test client with overridden database dependency.
    """
    
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


# =============================================================================
# TENANT FIXTURES
# =============================================================================


@pytest.fixture
def sample_tenant_data() -> dict[str, Any]:
    """Sample tenant creation data."""
    return {
        "name": "Test Company",
        "code": "test-co",
        "subscription_tier": "Free",
        "settings": {
            "max_users": 10,
            "max_clients": 5,
            "features_enabled": ["feature1", "feature2"],
            "custom_branding": False,
        },
    }


@pytest.fixture
def sample_tenant_data_premium() -> dict[str, Any]:
    """Sample tenant creation data with premium tier."""
    return {
        "name": "Premium Corp",
        "code": "premium-corp",
        "subscription_tier": "Enterprise",
        "settings": {
            "max_users": 100,
            "max_clients": 50,
            "features_enabled": ["feature1", "feature2", "premium_feature"],
            "custom_branding": True,
        },
    }


@pytest.fixture
def sample_tenant_data_minimal() -> dict[str, Any]:
    """Minimal tenant creation data (uses defaults)."""
    return {
        "name": "Minimal Tenant",
        "code": "minimal",
    }


# =============================================================================
# PERSON TEST FIXTURES
# =============================================================================


@pytest_asyncio.fixture
async def test_tenant(client: AsyncClient) -> dict[str, Any]:
    """Create a test tenant and return its data."""
    response = await client.post(
        "/tenants/",
        json={
            "name": "Person Test Tenant",
            "code": "person-test",
            "subscription_tier": "Professional",
            "settings": {
                "max_users": 50,
                "max_clients": 25,
                "features_enabled": ["persons"],
                "custom_branding": False,
            },
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, test_tenant: dict) -> dict[str, Any]:
    """Create a test user directly in the database."""
    from app.infrastructure.models.user_model import UserModel
    from app.domain.enums import UserStatus
    
    user_id = generate_cuid()
    user = UserModel(
        id=user_id,
        tenant_id=test_tenant["id"],
        email=f"test-{user_id[:8]}@example.com",
        status=UserStatus.ACTIVE,
        is_two_factor_enabled=False,
    )
    db_session.add(user)
    await db_session.commit()
    
    return {
        "id": user_id,
        "tenant_id": test_tenant["id"],
        "email": user.email,
        "status": UserStatus.ACTIVE.value,
    }


@pytest_asyncio.fixture
async def test_user_2(db_session: AsyncSession, test_tenant: dict) -> dict[str, Any]:
    """Create a second test user directly in the database."""
    from app.infrastructure.models.user_model import UserModel
    from app.domain.enums import UserStatus
    
    user_id = generate_cuid()
    user = UserModel(
        id=user_id,
        tenant_id=test_tenant["id"],
        email=f"test2-{user_id[:8]}@example.com",
        status=UserStatus.ACTIVE,
        is_two_factor_enabled=False,
    )
    db_session.add(user)
    await db_session.commit()
    
    return {
        "id": user_id,
        "tenant_id": test_tenant["id"],
        "email": user.email,
        "status": UserStatus.ACTIVE.value,
    }


@pytest_asyncio.fixture
async def test_client_employee(
    db_session: AsyncSession, test_tenant: dict, test_user: dict
) -> dict[str, Any]:
    """Create a test client employee person directly in the database."""
    from app.infrastructure.models.person_model import PersonModel
    from app.domain.enums import BaseStatus, PersonType, WorkStatus
    
    person_id = generate_cuid()
    person = PersonModel(
        id=person_id,
        tenant_id=test_tenant["id"],
        user_id=test_user["id"],
        person_type=PersonType.CLIENT_EMPLOYEE,
        is_dual_role=False,
        status=BaseStatus.ACTIVE,
        employment_info={
            "role": "Software Engineer",
            "start_date": date.today().isoformat(),
            "status": WorkStatus.ACTIVE.value,
            "department": "Engineering",
            "employee_id": "EMP001",
        },
    )
    db_session.add(person)
    await db_session.commit()
    
    return {
        "id": person_id,
        "tenant_id": test_tenant["id"],
        "user_id": test_user["id"],
        "person_type": PersonType.CLIENT_EMPLOYEE.value,
        "status": BaseStatus.ACTIVE.value,
    }


@pytest_asyncio.fixture
async def test_service_provider(
    db_session: AsyncSession, test_tenant: dict, test_user_2: dict
) -> dict[str, Any]:
    """Create a test service provider person directly in the database."""
    from app.infrastructure.models.person_model import PersonModel
    from app.domain.enums import BaseStatus, PersonType
    
    person_id = generate_cuid()
    person = PersonModel(
        id=person_id,
        tenant_id=test_tenant["id"],
        user_id=test_user_2["id"],
        person_type=PersonType.SERVICE_PROVIDER,
        is_dual_role=False,
        status=BaseStatus.ACTIVE,
        license_info={
            "number": "LIC-12345",
            "issuing_authority": "State Board",
            "expiry_date": "2025-12-31",
        },
    )
    db_session.add(person)
    await db_session.commit()
    
    return {
        "id": person_id,
        "tenant_id": test_tenant["id"],
        "user_id": test_user_2["id"],
        "person_type": PersonType.SERVICE_PROVIDER.value,
        "status": BaseStatus.ACTIVE.value,
    }


@pytest_asyncio.fixture
async def test_pending_person(
    db_session: AsyncSession, test_tenant: dict
) -> dict[str, Any]:
    """Create a test person in PENDING status."""
    from app.infrastructure.models.user_model import UserModel
    from app.infrastructure.models.person_model import PersonModel
    from app.domain.enums import BaseStatus, PersonType, UserStatus, WorkStatus
    
    # Create user first
    user_id = generate_cuid()
    user = UserModel(
        id=user_id,
        tenant_id=test_tenant["id"],
        email=f"pending-{user_id[:8]}@example.com",
        status=UserStatus.ACTIVE,
        is_two_factor_enabled=False,
    )
    db_session.add(user)
    
    # Create pending person
    person_id = generate_cuid()
    person = PersonModel(
        id=person_id,
        tenant_id=test_tenant["id"],
        user_id=user_id,
        person_type=PersonType.CLIENT_EMPLOYEE,
        is_dual_role=False,
        status=BaseStatus.PENDING,
        employment_info={
            "role": "New Hire",
            "start_date": date.today().isoformat(),
            "status": WorkStatus.ACTIVE.value,
            "department": "HR",
        },
    )
    db_session.add(person)
    await db_session.commit()
    
    return {
        "id": person_id,
        "tenant_id": test_tenant["id"],
        "user_id": user_id,
        "person_type": PersonType.CLIENT_EMPLOYEE.value,
        "status": BaseStatus.PENDING.value,
    }


@pytest.fixture
def sample_employment_info() -> dict[str, Any]:
    """Sample employment information."""
    return {
        "role": "Senior Developer",
        "start_date": date.today().isoformat(),
        "status": "Active",
        "department": "Technology",
        "employee_id": "EMP-NEW-001",
    }


@pytest.fixture
def sample_license_info() -> dict[str, Any]:
    """Sample license information."""
    return {
        "number": "LIC-NEW-99999",
        "issuing_authority": "Medical Board",
        "expiry_date": "2026-12-31",
    }


@pytest.fixture
def sample_staff_info() -> dict[str, Any]:
    """Sample staff information."""
    return {
        "role": "Admin",
        "client_id": generate_cuid(),
        "department": "Administration",
        "can_manage_clients": True,
        "can_manage_services": True,
        "can_view_reports": True,
    }


@pytest.fixture
def sample_emergency_contact() -> dict[str, Any]:
    """Sample emergency contact information."""
    return {
        "name": "Jane Doe",
        "phone": "+1-555-123-4567",
        "email": "jane.doe@example.com",
    }
