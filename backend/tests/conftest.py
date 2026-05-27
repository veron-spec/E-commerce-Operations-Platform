"""Test infrastructure: SQLite in-memory DB, test client, fixtures."""
import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.core.auth import create_access_token, hash_password
from app.infrastructure.database import Base
from app.main import app
from app.models.store import Store
from app.models.user import User

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DB_URL, echo=False)
TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# ============ Plain pytest fixtures (no DB/async needed) ============

@pytest.fixture
def sample_shopify_order() -> dict:
    return {
        "id": 1234567890,
        "order_number": 1001,
        "email": "customer@example.com",
        "total_price": "129.99",
        "subtotal_price": "109.99",
        "total_discounts": "20.00",
        "financial_status": "paid",
        "fulfillment_status": "fulfilled",
        "customer": {"id": 987654321},
        "shipping_address": {"city": "Beijing", "country": "China"},
        "line_items": [
            {
                "product_id": 111,
                "variant_id": 222,
                "title": "Test Product",
                "sku": "TP-001",
                "quantity": 2,
                "price": "54.99",
            }
        ],
        "created_at": "2026-05-01T10:00:00Z",
        "updated_at": "2026-05-02T10:00:00Z",
    }


@pytest.fixture
def sample_shopify_product() -> dict:
    return {
        "id": 111,
        "title": "Test Product",
        "body_html": "<p>A test product</p>",
        "product_type": "Electronics",
        "status": "active",
        "tags": "new, featured",
        "variants": [
            {
                "price": "54.99",
                "compare_at_price": "69.99",
                "sku": "TP-001",
                "barcode": "123456789",
                "inventory_quantity": 25,
            }
        ],
        "images": [{"src": "https://example.com/image.jpg"}],
        "created_at": "2026-04-01T10:00:00Z",
        "updated_at": "2026-05-01T10:00:00Z",
    }


# ============ Async test lifecycle ============

@pytest.fixture(scope="session")
def event_loop():
    """Session-scoped event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def _setup_db():
    """Create tables before each test, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def _get_test_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSession() as session:
        try:
            yield session
        finally:
            await session.close()


# ============ Data fixtures ============

@pytest_asyncio.fixture
async def db() -> AsyncSession:
    """Provide a clean test DB session."""
    async with TestSession() as session:
        yield session


@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> dict:
    """Create and return a test user."""
    user = User(
        email="test@example.com",
        name="TestUser",
        password_hash=hash_password("Pass@1234"),
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"id": user.id, "email": user.email, "name": user.name}


@pytest_asyncio.fixture
async def test_store(db: AsyncSession, test_user: dict) -> dict:
    """Create and return a test store belonging to test_user."""
    store = Store(
        user_id=test_user["id"],
        name="测试店铺",
        platform_type="taobao",
        api_key="test_key",
        api_secret="test_secret",
        store_url="test_store",
        is_active=True,
    )
    db.add(store)
    await db.commit()
    await db.refresh(store)
    return {"id": store.id, "name": store.name, "platform_type": store.platform_type}


@pytest_asyncio.fixture
async def second_user(db: AsyncSession) -> dict:
    """Another user for data isolation tests."""
    user = User(
        email="other@example.com",
        name="OtherUser",
        password_hash=hash_password("Pass@4567"),
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"id": user.id, "email": user.email, "name": user.name}


@pytest_asyncio.fixture
async def second_store(db: AsyncSession, second_user: dict) -> dict:
    """Store belonging to second_user (for isolation tests)."""
    store = Store(
        user_id=second_user["id"],
        name="他人店铺",
        platform_type="shopify",
        api_key="other_key",
        api_secret="other_secret",
        store_url="other_store",
        is_active=True,
    )
    db.add(store)
    await db.commit()
    await db.refresh(store)
    return {"id": store.id, "name": store.name}


# ============ Auth token fixtures ============

@pytest_asyncio.fixture
async def user_token(test_user: dict) -> str:
    """JWT token for test_user."""
    return create_access_token(test_user["id"], test_user["email"])


@pytest_asyncio.fixture
async def auth_headers(user_token: str) -> dict:
    """Authorization headers for test_user."""
    return {"Authorization": f"Bearer {user_token}"}


@pytest_asyncio.fixture
async def second_user_token(second_user: dict) -> str:
    """JWT token for second_user."""
    return create_access_token(second_user["id"], second_user["email"])


@pytest_asyncio.fixture
async def second_auth_headers(second_user_token: str) -> dict:
    """Authorization headers for second_user."""
    return {"Authorization": f"Bearer {second_user_token}"}


# ============ HTTP client fixtures ============

@pytest_asyncio.fixture
async def client(auth_headers: dict) -> AsyncGenerator[AsyncClient, None]:
    """FastAPI test client with auth and test DB overrides."""
    app.dependency_overrides[get_db] = _get_test_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers=auth_headers,
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def unauth_client() -> AsyncGenerator[AsyncClient, None]:
    """Test client without auth headers."""
    app.dependency_overrides[get_db] = _get_test_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def other_client(second_auth_headers: dict) -> AsyncGenerator[AsyncClient, None]:
    """Test client authenticated as second_user."""
    app.dependency_overrides[get_db] = _get_test_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers=second_auth_headers,
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
