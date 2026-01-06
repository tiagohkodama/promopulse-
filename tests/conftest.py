import pytest
import pytest_asyncio
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from promopulse.db.models.base import Base
from promopulse.db.models.user import User
from promopulse.db.models.promotion import Promotion, PromotionStatus
from promopulse.app.main import app
from promopulse.db.session import get_async_session


# Test database configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    """Create test database session."""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def test_user(db_session):
    """Create a test user."""
    user = User(
        encrypted_email="encrypted_test@example.com",
        full_name="Test User",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_active_promotion(db_session, test_user):
    """Create an ACTIVE test promotion."""
    promotion = Promotion(
        name="Test Active Promotion",
        status=PromotionStatus.ACTIVE,
        start_at=datetime.now(timezone.utc),
        end_at=datetime.now(timezone.utc),
        created_by=test_user.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(promotion)
    await db_session.commit()
    await db_session.refresh(promotion)
    return promotion


@pytest_asyncio.fixture
async def test_draft_promotion(db_session, test_user):
    """Create a DRAFT test promotion."""
    promotion = Promotion(
        name="Test Draft Promotion",
        status=PromotionStatus.DRAFT,
        start_at=datetime.now(timezone.utc),
        end_at=datetime.now(timezone.utc),
        created_by=test_user.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(promotion)
    await db_session.commit()
    await db_session.refresh(promotion)
    return promotion


@pytest_asyncio.fixture
async def client(db_session):
    """Create test HTTP client with database override."""
    # Override get_async_session dependency to use test database
    async def override_get_async_session():
        yield db_session

    app.dependency_overrides[get_async_session] = override_get_async_session

    # Create async client with ASGI transport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
