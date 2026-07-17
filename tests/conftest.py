"""
Test Configuration and Fixtures

Provides async test client and database fixtures for E2E testing.
"""
# Force test environment before any app imports so rate limiting uses test limits
import os

os.environ["ENVIRONMENT"] = "test"

from collections.abc import AsyncGenerator
from datetime import UTC, date
from typing import Any

import pytest
import pytest_asyncio
from fastapi import Depends, Request
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.dependencies import (
    get_audit_repository,
    get_document_repository,
    get_user_repository,
)
from app.core.authorization import (
    get_audit_log_for_current_tenant,
    get_current_user_entity,
    get_document_for_current_tenant,
    get_user_in_tenant,
)
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.entities.audit import AuditLog
from app.domain.entities.document import DocumentEntity
from app.domain.entities.user import UserEntity
from app.domain.enums import TenantRole, UserStatus
from app.domain.repositories.audit_repository import AuditRepository
from app.domain.repositories.document_repository import DocumentRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.core import AuditLogId, DocumentId, Email, TenantId, UserId
from app.infrastructure.models.base import Base
from app.main import app
from app.shared.utils.datetime import utc_now
from app.shared.utils.generators import generate_cuid

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/eap_test",
)

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
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
    Create an async test client with overridden database and authentication dependencies.
    """
    
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session
    
    async def override_get_current_user(request: Request) -> TokenData:
        """Mock authentication for tests - returns a test user token with tenant_id from path or query."""
        # Path params (e.g. /tenants/{tenant_id}) take precedence so require_same_tenant passes
        tenant_id = request.path_params.get("tenant_id") or request.query_params.get("tenant_id", "test-tenant-id")
        return TokenData(
            user_id="test-user-id",
            tenant_id=tenant_id,
            email="test@example.com",
        )
    
    async def override_get_user_in_tenant(
        user_id: str,
        user_repo: UserRepository = Depends(get_user_repository),
    ) -> UserEntity:
        """In tests, load user by ID without tenant check so existing E2E tests pass."""
        from fastapi import HTTPException
        user = await user_repo.get_by_id(UserId(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    async def override_get_audit_log(
        audit_log_id: str,
        audit_repo: AuditRepository = Depends(get_audit_repository),
    ) -> AuditLog:
        """In tests, load audit log by ID without tenant check."""
        from fastapi import HTTPException
        log = await audit_repo.get_audit_log_by_id(AuditLogId(audit_log_id))
        if not log:
            raise HTTPException(status_code=404, detail="Audit log not found")
        return log

    async def override_get_document(
        document_id: str,
        document_repo: DocumentRepository = Depends(get_document_repository),
    ) -> DocumentEntity:
        """In tests, load document by ID without tenant check."""
        from fastapi import HTTPException
        doc = await document_repo.get_by_id(DocumentId(document_id))
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc

    async def override_get_current_user_entity(
        current_user: TokenData = Depends(get_current_user),
        user_repo: UserRepository = Depends(get_user_repository),
    ) -> UserEntity:
        """In tests, load current user for RBAC; if not in DB, return stub with ADMIN role."""
        user = await user_repo.get_by_id(UserId(current_user.user_id))
        if user:
            return user
        # Stub so require_tenant_role(ADMIN) passes in E2E
        now = utc_now()
        return UserEntity(
            id=UserId(current_user.user_id),
            tenant_id=TenantId(current_user.tenant_id),
            email=Email(current_user.email or "test@example.com"),
            status=UserStatus.ACTIVE,
            is_two_factor_enabled=False,
            role=TenantRole.ADMIN,
            created_at=now,
            updated_at=now,
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_user_entity] = override_get_current_user_entity
    app.dependency_overrides[get_user_in_tenant] = override_get_user_in_tenant
    app.dependency_overrides[get_audit_log_for_current_tenant] = override_get_audit_log
    app.dependency_overrides[get_document_for_current_tenant] = override_get_document

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
    from app.domain.enums import UserStatus
    from app.infrastructure.models.user_model import UserModel
    
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
    from app.domain.enums import UserStatus
    from app.infrastructure.models.user_model import UserModel
    
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
    from app.domain.enums import BaseStatus, PersonType, WorkStatus
    from app.infrastructure.models.person_model import PersonModel
    
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
    from app.domain.enums import BaseStatus, PersonType
    from app.infrastructure.models.person_model import PersonModel
    
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
    from app.domain.enums import BaseStatus, PersonType, UserStatus, WorkStatus
    from app.infrastructure.models.person_model import PersonModel
    from app.infrastructure.models.user_model import UserModel
    
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


# =============================================================================
# CLIENT TEST FIXTURES
# =============================================================================


@pytest_asyncio.fixture
async def client_test_tenant(client: AsyncClient) -> dict[str, Any]:
    """Create a test tenant for client tests and return its data."""
    response = await client.post(
        "/tenants/",
        json={
            "name": "Client Test Tenant",
            "code": "client-test",
            "subscription_tier": "Professional",
            "settings": {
                "max_users": 50,
                "max_clients": 25,
                "features_enabled": ["clients"],
                "custom_branding": False,
            },
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def sample_client_data() -> dict[str, Any]:
    """Sample client creation data."""
    return {
        "name": "Acme Corporation",
        "code": "ACME",
        "contact_info": {
            "phone": "+1-555-100-2000",
            "email": "contact@acme.com",
            "address": "123 Main St, Suite 100",
        },
        "billing_address": {
            "street": "123 Main St",
            "city": "New York",
            "country": "USA",
            "postal_code": "10001",
        },
    }


@pytest.fixture
def sample_client_data_minimal() -> dict[str, Any]:
    """Minimal client creation data."""
    return {
        "name": "Simple Client",
        "code": "SIMP",
        "contact_info": {
            "phone": "+1-555-999-8888",
        },
    }


@pytest_asyncio.fixture
async def test_client(
    client: AsyncClient, client_test_tenant: dict, sample_client_data: dict
) -> dict[str, Any]:
    """Create a test client via API and return its data."""
    tenant_id = client_test_tenant["id"]
    response = await client.post(
        f"/clients/?tenant_id={tenant_id}",
        json=sample_client_data,
    )
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def test_client_active(
    client: AsyncClient, client_test_tenant: dict
) -> dict[str, Any]:
    """Create and activate a test client."""
    tenant_id = client_test_tenant["id"]
    
    # Create client
    create_response = await client.post(
        f"/clients/?tenant_id={tenant_id}",
        json={
            "name": "Active Test Client",
            "code": "ACTV",
            "contact_info": {
                "phone": "+1-555-111-2222",
                "email": "active@testclient.com",
            },
        },
    )
    assert create_response.status_code == 201
    client_data = create_response.json()
    
    # Activate client
    activate_response = await client.post(f"/clients/{client_data['id']}/activate")
    assert activate_response.status_code == 200
    
    return activate_response.json()


@pytest_asyncio.fixture
async def test_client_2(
    client: AsyncClient, client_test_tenant: dict
) -> dict[str, Any]:
    """Create a second test client."""
    tenant_id = client_test_tenant["id"]
    response = await client.post(
        f"/clients/?tenant_id={tenant_id}",
        json={
            "name": "Second Client Corp",
            "code": "SEC2",
            "contact_info": {
                "phone": "+1-555-333-4444",
                "email": "info@secondclient.com",
            },
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def test_parent_client(
    client: AsyncClient, client_test_tenant: dict
) -> dict[str, Any]:
    """Create a parent test client."""
    tenant_id = client_test_tenant["id"]
    response = await client.post(
        f"/clients/?tenant_id={tenant_id}",
        json={
            "name": "Parent Organization",
            "code": "PRNT",
            "contact_info": {
                "phone": "+1-555-000-0001",
                "email": "parent@organization.com",
            },
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def test_child_client(
    client: AsyncClient, client_test_tenant: dict, test_parent_client: dict
) -> dict[str, Any]:
    """Create a child test client under parent."""
    tenant_id = client_test_tenant["id"]
    response = await client.post(
        f"/clients/?tenant_id={tenant_id}",
        json={
            "name": "Child Division",
            "code": "CHLD",
            "contact_info": {
                "phone": "+1-555-000-0002",
                "email": "child@organization.com",
            },
            "parent_client_id": test_parent_client["id"],
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def verifier_user(db_session: AsyncSession, client_test_tenant: dict) -> dict[str, Any]:
    """Create a user who can verify clients."""
    from app.domain.enums import UserStatus
    from app.infrastructure.models.user_model import UserModel
    
    user_id = generate_cuid()
    user = UserModel(
        id=user_id,
        tenant_id=client_test_tenant["id"],
        email=f"verifier-{user_id[:8]}@example.com",
        status=UserStatus.ACTIVE,
        is_two_factor_enabled=False,
    )
    db_session.add(user)
    await db_session.commit()
    
    return {
        "id": user_id,
        "tenant_id": client_test_tenant["id"],
        "email": user.email,
    }


# =============================================================================
# CONTRACT TEST FIXTURES
# =============================================================================


@pytest_asyncio.fixture
async def contract_test_tenant(client: AsyncClient) -> dict[str, Any]:
    """Create a test tenant for contract tests."""
    response = await client.post(
        "/tenants/",
        json={
            "name": "Contract Test Tenant",
            "code": "contract-test",
            "subscription_tier": "Professional",
            "settings": {
                "max_users": 50,
                "max_clients": 25,
                "features_enabled": ["contracts"],
                "custom_branding": False,
            },
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def contract_test_client(
    client: AsyncClient, contract_test_tenant: dict
) -> dict[str, Any]:
    """Create and activate a test client for contract tests."""
    tenant_id = contract_test_tenant["id"]
    
    # Create client
    create_response = await client.post(
        f"/clients/?tenant_id={tenant_id}",
        json={
            "name": "Contract Test Client",
            "code": "CTRC",
            "contact_info": {
                "phone": "+1-555-CONTRACT",
                "email": "contracts@testclient.com",
            },
        },
    )
    assert create_response.status_code == 201
    client_data = create_response.json()
    
    # Activate client
    activate_response = await client.post(f"/clients/{client_data['id']}/activate")
    assert activate_response.status_code == 200
    
    return activate_response.json()


@pytest_asyncio.fixture
async def contract_test_client_2(
    client: AsyncClient, contract_test_tenant: dict
) -> dict[str, Any]:
    """Create a second test client for contract tests."""
    tenant_id = contract_test_tenant["id"]
    
    create_response = await client.post(
        f"/clients/?tenant_id={tenant_id}",
        json={
            "name": "Second Contract Client",
            "code": "CTR2",
            "contact_info": {
                "phone": "+1-555-CONTRACT2",
                "email": "contracts2@testclient.com",
            },
        },
    )
    assert create_response.status_code == 201
    client_data = create_response.json()
    
    # Activate client
    activate_response = await client.post(f"/clients/{client_data['id']}/activate")
    assert activate_response.status_code == 200
    
    return activate_response.json()


@pytest.fixture
def sample_contract_data(contract_test_client: dict) -> dict[str, Any]:
    """Sample contract creation data."""
    from datetime import datetime, timedelta
    
    start_date = datetime.now(UTC).isoformat()
    end_date = (datetime.now(UTC) + timedelta(days=365)).isoformat()
    
    return {
        "client_id": contract_test_client["id"],
        "start_date": start_date,
        "end_date": end_date,
        "billing_rate": {
            "amount": "5000.00",
            "currency": "USD",
        },
        "payment_frequency": "Monthly",
        "is_auto_renew": False,
    }


@pytest_asyncio.fixture
async def test_contract(
    client: AsyncClient, contract_test_tenant: dict, contract_test_client: dict
) -> dict[str, Any]:
    """Create a test contract via API."""
    from datetime import datetime, timedelta
    
    tenant_id = contract_test_tenant["id"]
    start_date = datetime.now(UTC).isoformat()
    end_date = (datetime.now(UTC) + timedelta(days=365)).isoformat()
    
    response = await client.post(
        f"/contracts/?tenant_id={tenant_id}",
        json={
            "client_id": contract_test_client["id"],
            "start_date": start_date,
            "end_date": end_date,
            "billing_rate": {
                "amount": "5000.00",
                "currency": "USD",
            },
            "payment_frequency": "Monthly",
            "is_auto_renew": False,
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def test_contract_active(
    client: AsyncClient, contract_test_tenant: dict, contract_test_client: dict
) -> dict[str, Any]:
    """Create and activate a test contract."""
    from datetime import datetime, timedelta
    
    tenant_id = contract_test_tenant["id"]
    start_date = datetime.now(UTC).isoformat()
    end_date = (datetime.now(UTC) + timedelta(days=365)).isoformat()
    
    # Create contract
    create_response = await client.post(
        f"/contracts/?tenant_id={tenant_id}",
        json={
            "client_id": contract_test_client["id"],
            "start_date": start_date,
            "end_date": end_date,
            "billing_rate": {
                "amount": "10000.00",
                "currency": "USD",
            },
            "payment_frequency": "Monthly",
            "is_auto_renew": True,
        },
    )
    assert create_response.status_code == 201
    contract_data = create_response.json()
    
    # Activate contract
    activate_response = await client.post(f"/contracts/{contract_data['id']}/activate")
    assert activate_response.status_code == 200
    
    return activate_response.json()


@pytest_asyncio.fixture
async def test_contract_2(
    client: AsyncClient, contract_test_tenant: dict, contract_test_client_2: dict
) -> dict[str, Any]:
    """Create a second test contract for a different client."""
    from datetime import datetime, timedelta
    
    tenant_id = contract_test_tenant["id"]
    start_date = datetime.now(UTC).isoformat()
    end_date = (datetime.now(UTC) + timedelta(days=180)).isoformat()
    
    response = await client.post(
        f"/contracts/?tenant_id={tenant_id}",
        json={
            "client_id": contract_test_client_2["id"],
            "start_date": start_date,
            "end_date": end_date,
            "billing_rate": {
                "amount": "3000.00",
                "currency": "EUR",
            },
            "payment_frequency": "Quarterly",
            "is_auto_renew": False,
        },
    )
    assert response.status_code == 201
    return response.json()


# =============================================================================
# USER TEST FIXTURES
# =============================================================================


@pytest_asyncio.fixture
async def user_test_tenant(client: AsyncClient) -> dict[str, Any]:
    """Create a test tenant for user tests."""
    response = await client.post(
        "/tenants/",
        json={
            "name": "User Test Tenant",
            "code": "user-test",
            "subscription_tier": "Professional",
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def test_api_user(
    client: AsyncClient, user_test_tenant: dict
) -> dict[str, Any]:
    """Create a test user via API."""
    tenant_id = user_test_tenant["id"]
    response = await client.post(
        f"/users/?tenant_id={tenant_id}",
        json={
            "email": "testuser@example.com",
            "password": "SecurePassword123!",
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def test_api_user_2(
    client: AsyncClient, user_test_tenant: dict
) -> dict[str, Any]:
    """Create a second test user via API."""
    tenant_id = user_test_tenant["id"]
    response = await client.post(
        f"/users/?tenant_id={tenant_id}",
        json={
            "email": "testuser2@example.com",
            "password": "SecurePassword456!",
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def test_api_user_active(
    client: AsyncClient, user_test_tenant: dict
) -> dict[str, Any]:
    """Create and activate a test user."""
    tenant_id = user_test_tenant["id"]
    
    # Create user
    create_response = await client.post(
        f"/users/?tenant_id={tenant_id}",
        json={
            "email": "activeuser@example.com",
            "password": "SecurePassword789!",
        },
    )
    assert create_response.status_code == 201
    user_data = create_response.json()
    
    # Verify email first
    await client.post(f"/users/{user_data['id']}/verify-email")
    
    # Activate user
    activate_response = await client.post(f"/users/{user_data['id']}/activate")
    assert activate_response.status_code == 200
    
    return activate_response.json()


# =============================================================================
# SERVICE TEST FIXTURES
# =============================================================================


@pytest_asyncio.fixture
async def service_test_tenant(client: AsyncClient) -> dict[str, Any]:
    """Create a test tenant for service tests."""
    response = await client.post(
        "/tenants/",
        json={
            "name": "Service Test Tenant",
            "code": "service-test",
            "subscription_tier": "Professional",
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def test_service(
    client: AsyncClient, service_test_tenant: dict
) -> dict[str, Any]:
    """Create a test service via API."""
    tenant_id = service_test_tenant["id"]
    response = await client.post(
        f"/services/?tenant_id={tenant_id}",
        json={
            "name": "Individual Counseling",
            "description": "One-on-one counseling session",
            "category": "Counseling",
            "duration_minutes": 60,
            "is_group_service": False,
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def test_service_active(
    client: AsyncClient, service_test_tenant: dict
) -> dict[str, Any]:
    """Create and activate a test service."""
    tenant_id = service_test_tenant["id"]
    
    # Create service
    create_response = await client.post(
        f"/services/?tenant_id={tenant_id}",
        json={
            "name": "Active Counseling Service",
            "description": "An active service",
            "category": "Counseling",
            "duration_minutes": 45,
            "is_group_service": False,
        },
    )
    assert create_response.status_code == 201
    service_data = create_response.json()
    
    # Activate service
    activate_response = await client.post(f"/services/{service_data['id']}/activate")
    assert activate_response.status_code == 200
    
    return activate_response.json()


@pytest_asyncio.fixture
async def test_group_service(
    client: AsyncClient, service_test_tenant: dict
) -> dict[str, Any]:
    """Create a group service via API."""
    tenant_id = service_test_tenant["id"]
    response = await client.post(
        f"/services/?tenant_id={tenant_id}",
        json={
            "name": "Group Therapy",
            "description": "Group therapy session",
            "category": "Therapy",
            "duration_minutes": 90,
            "is_group_service": True,
            "max_participants": 10,
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def test_service_2(
    client: AsyncClient, service_test_tenant: dict
) -> dict[str, Any]:
    """Create a second test service."""
    tenant_id = service_test_tenant["id"]
    response = await client.post(
        f"/services/?tenant_id={tenant_id}",
        json={
            "name": "Crisis Intervention",
            "description": "Emergency counseling service",
            "category": "Emergency",
            "duration_minutes": 30,
            "is_group_service": False,
        },
    )
    assert response.status_code == 201
    return response.json()


# =============================================================================
# SERVICE SESSION TEST FIXTURES
# =============================================================================


@pytest_asyncio.fixture
async def session_test_tenant(client: AsyncClient) -> dict[str, Any]:
    """Create a test tenant for service session tests."""
    response = await client.post(
        "/tenants/",
        json={
            "name": "Session Test Tenant",
            "code": "session-test",
            "subscription_tier": "Professional",
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def session_test_service(
    client: AsyncClient, session_test_tenant: dict
) -> dict[str, Any]:
    """Create a test service for sessions."""
    tenant_id = session_test_tenant["id"]
    response = await client.post(
        f"/services/?tenant_id={tenant_id}",
        json={
            "name": "Session Test Service",
            "description": "Service for session tests",
            "category": "Testing",
            "duration_minutes": 60,
            "is_group_service": False,
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def session_test_provider(
    db_session: AsyncSession, session_test_tenant: dict
) -> dict[str, Any]:
    """Create a provider person for session tests."""
    from app.domain.enums import BaseStatus, PersonType, UserStatus
    from app.infrastructure.models.person_model import PersonModel
    from app.infrastructure.models.user_model import UserModel
    
    # Create user first
    user_id = generate_cuid()
    user = UserModel(
        id=user_id,
        tenant_id=session_test_tenant["id"],
        email=f"provider-{user_id[:8]}@example.com",
        status=UserStatus.ACTIVE,
        is_two_factor_enabled=False,
    )
    db_session.add(user)
    await db_session.flush()
    
    # Create provider person
    person_id = generate_cuid()
    person = PersonModel(
        id=person_id,
        tenant_id=session_test_tenant["id"],
        user_id=user_id,
        person_type=PersonType.SERVICE_PROVIDER,
        is_dual_role=False,
        status=BaseStatus.ACTIVE,
        license_info={
            "number": "LIC-TEST-001",
            "issuing_authority": "Test Board",
            "expiry_date": "2027-12-31",
        },
    )
    db_session.add(person)
    await db_session.commit()
    
    return {
        "id": person_id,
        "user_id": user_id,
        "tenant_id": session_test_tenant["id"],
    }


@pytest_asyncio.fixture
async def session_test_client_person(
    db_session: AsyncSession, session_test_tenant: dict
) -> dict[str, Any]:
    """Create a client employee person for session tests."""
    from datetime import date

    from app.domain.enums import BaseStatus, PersonType, UserStatus, WorkStatus
    from app.infrastructure.models.person_model import PersonModel
    from app.infrastructure.models.user_model import UserModel
    
    # Create user first
    user_id = generate_cuid()
    user = UserModel(
        id=user_id,
        tenant_id=session_test_tenant["id"],
        email=f"client-person-{user_id[:8]}@example.com",
        status=UserStatus.ACTIVE,
        is_two_factor_enabled=False,
    )
    db_session.add(user)
    await db_session.flush()
    
    # Create client employee person
    person_id = generate_cuid()
    person = PersonModel(
        id=person_id,
        tenant_id=session_test_tenant["id"],
        user_id=user_id,
        person_type=PersonType.CLIENT_EMPLOYEE,
        is_dual_role=False,
        status=BaseStatus.ACTIVE,
        employment_info={
            "role": "Test Employee",
            "start_date": date.today().isoformat(),
            "status": WorkStatus.ACTIVE.value,
            "department": "Testing",
        },
    )
    db_session.add(person)
    await db_session.commit()
    
    return {
        "id": person_id,
        "user_id": user_id,
        "tenant_id": session_test_tenant["id"],
    }


@pytest_asyncio.fixture
async def test_service_session(
    client: AsyncClient,
    session_test_tenant: dict,
    session_test_service: dict,
    session_test_provider: dict,
    session_test_client_person: dict,
) -> dict[str, Any]:
    """Create a test service session via API."""
    from datetime import datetime, timedelta
    
    tenant_id = session_test_tenant["id"]
    scheduled_at = (datetime.now(UTC) + timedelta(days=7)).isoformat()
    
    response = await client.post(
        f"/service-sessions/?tenant_id={tenant_id}",
        json={
            "service_id": session_test_service["id"],
            "provider_id": session_test_provider["id"],
            "person_id": session_test_client_person["id"],
            "scheduled_at": scheduled_at,
            "location": "Office A",
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def test_service_session_2(
    client: AsyncClient,
    session_test_tenant: dict,
    session_test_service: dict,
    session_test_provider: dict,
    session_test_client_person: dict,
) -> dict[str, Any]:
    """Create a second test service session."""
    from datetime import datetime, timedelta
    
    tenant_id = session_test_tenant["id"]
    scheduled_at = (datetime.now(UTC) + timedelta(days=14)).isoformat()
    
    response = await client.post(
        f"/service-sessions/?tenant_id={tenant_id}",
        json={
            "service_id": session_test_service["id"],
            "provider_id": session_test_provider["id"],
            "person_id": session_test_client_person["id"],
            "scheduled_at": scheduled_at,
            "location": "Office B",
        },
    )
    assert response.status_code == 201
    return response.json()


# =============================================================================
# AUDIT TEST FIXTURES
# =============================================================================


@pytest_asyncio.fixture
async def audit_test_tenant(client: AsyncClient) -> dict[str, Any]:
    """Create a test tenant for audit tests."""
    response = await client.post(
        "/tenants/",
        json={
            "name": "Audit Test Tenant",
            "code": "audit-test",
            "subscription_tier": "Professional",
        },
    )
    assert response.status_code == 201
    return response.json()
