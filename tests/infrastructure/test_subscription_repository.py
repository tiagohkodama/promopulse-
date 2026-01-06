import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone

from promopulse.db.models.base import Base
from promopulse.db.models.user import User
from promopulse.db.models.promotion import Promotion, PromotionStatus
from promopulse.db.models.subscription import Subscription
from promopulse.infrastructure.subscriptions.repository import SubscriptionRepository


# Test database URL (in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine):
    """Create test database session."""
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def test_user(session):
    """Create a test user."""
    user = User(
        encrypted_email="encrypted_test@example.com",
        full_name="Test User",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_promotion(session, test_user):
    """Create a test promotion."""
    promotion = Promotion(
        name="Test Promotion",
        status=PromotionStatus.ACTIVE,
        start_at=datetime.now(timezone.utc),
        end_at=datetime.now(timezone.utc),
        created_by=test_user.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    session.add(promotion)
    await session.commit()
    await session.refresh(promotion)
    return promotion


@pytest.mark.asyncio
async def test_create_subscription(session, test_user, test_promotion):
    """Test creating a subscription."""
    repo = SubscriptionRepository(session)

    subscription = await repo.create(
        user_id=test_user.id,
        promotion_id=test_promotion.id,
        metadata={"source": "web"}
    )

    assert subscription.id is not None
    assert subscription.user_id == test_user.id
    assert subscription.promotion_id == test_promotion.id
    assert subscription.is_active is True
    assert subscription.subscription_metadata == {"source": "web"}
    assert subscription.created_at is not None


@pytest.mark.asyncio
async def test_create_duplicate_subscription_raises_integrity_error(
    session,
    test_user,
    test_promotion
):
    """Test that duplicate subscriptions raise IntegrityError."""
    repo = SubscriptionRepository(session)

    # Create first subscription
    await repo.create(
        user_id=test_user.id,
        promotion_id=test_promotion.id
    )

    # Attempt to create duplicate
    with pytest.raises(IntegrityError):
        await repo.create(
            user_id=test_user.id,
            promotion_id=test_promotion.id
        )


@pytest.mark.asyncio
async def test_get_active_subscription(session, test_user, test_promotion):
    """Test getting active subscription."""
    repo = SubscriptionRepository(session)

    # Create subscription
    created = await repo.create(
        user_id=test_user.id,
        promotion_id=test_promotion.id
    )

    # Retrieve active subscription
    found = await repo.get_active_subscription(
        user_id=test_user.id,
        promotion_id=test_promotion.id
    )

    assert found is not None
    assert found.id == created.id
    assert found.is_active is True


@pytest.mark.asyncio
async def test_get_active_subscription_returns_none_when_inactive(session, test_user, test_promotion):
    """Test get_active_subscription returns None for inactive subscriptions."""
    repo = SubscriptionRepository(session)

    # Create and deactivate subscription
    subscription = await repo.create(
        user_id=test_user.id,
        promotion_id=test_promotion.id
    )
    await repo.deactivate(subscription)

    # Try to get active subscription
    found = await repo.get_active_subscription(
        user_id=test_user.id,
        promotion_id=test_promotion.id
    )

    assert found is None


@pytest.mark.asyncio
async def test_list_by_user_pagination(session, test_user):
    """Test listing subscriptions by user with pagination."""
    repo = SubscriptionRepository(session)

    # Create multiple promotions and subscriptions
    for i in range(5):
        promo = Promotion(
            name=f"Promo {i}",
            status=PromotionStatus.ACTIVE,
            start_at=datetime.now(timezone.utc),
            end_at=datetime.now(timezone.utc),
            created_by=test_user.id
        )
        session.add(promo)
        await session.commit()
        await session.refresh(promo)

        await repo.create(user_id=test_user.id, promotion_id=promo.id)

    # Test pagination
    subs, total = await repo.list_by_user(user_id=test_user.id, limit=3, offset=0)
    assert len(subs) == 3
    assert total == 5

    subs, total = await repo.list_by_user(user_id=test_user.id, limit=3, offset=3)
    assert len(subs) == 2
    assert total == 5


@pytest.mark.asyncio
async def test_list_by_user_with_is_active_filter(session, test_user, test_promotion):
    """Test listing subscriptions filtered by is_active status."""
    repo = SubscriptionRepository(session)

    # Create two subscriptions
    sub1 = await repo.create(user_id=test_user.id, promotion_id=test_promotion.id)

    promo2 = Promotion(
        name="Promo 2",
        status=PromotionStatus.ACTIVE,
        start_at=datetime.now(timezone.utc),
        end_at=datetime.now(timezone.utc),
        created_by=test_user.id
    )
    session.add(promo2)
    await session.commit()
    await session.refresh(promo2)

    sub2 = await repo.create(user_id=test_user.id, promotion_id=promo2.id)

    # Deactivate one subscription
    await repo.deactivate(sub1)

    # List only active subscriptions
    subs, total = await repo.list_by_user(user_id=test_user.id, is_active=True)
    assert len(subs) == 1
    assert total == 1
    assert subs[0].id == sub2.id

    # List only inactive subscriptions
    subs, total = await repo.list_by_user(user_id=test_user.id, is_active=False)
    assert len(subs) == 1
    assert total == 1
    assert subs[0].id == sub1.id


@pytest.mark.asyncio
async def test_list_by_promotion(session, test_user, test_promotion):
    """Test listing subscriptions by promotion."""
    repo = SubscriptionRepository(session)

    # Create multiple users and subscriptions
    for i in range(3):
        user = User(
            encrypted_email=f"encrypted_user{i}@example.com",
            full_name=f"User {i}"
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        await repo.create(user_id=user.id, promotion_id=test_promotion.id)

    # List subscriptions for promotion
    subs, total = await repo.list_by_promotion(promotion_id=test_promotion.id)
    assert len(subs) == 3
    assert total == 3


@pytest.mark.asyncio
async def test_deactivate_subscription(session, test_user, test_promotion):
    """Test deactivating a subscription."""
    repo = SubscriptionRepository(session)

    # Create subscription
    subscription = await repo.create(
        user_id=test_user.id,
        promotion_id=test_promotion.id
    )
    assert subscription.is_active is True

    # Deactivate
    deactivated = await repo.deactivate(subscription)

    assert deactivated.id == subscription.id
    assert deactivated.is_active is False


@pytest.mark.asyncio
async def test_count_active_subscribers(session, test_user, test_promotion):
    """Test counting active subscribers for a promotion."""
    repo = SubscriptionRepository(session)

    # Create multiple users and subscriptions
    for i in range(3):
        user = User(
            encrypted_email=f"encrypted_user{i}@example.com",
            full_name=f"User {i}"
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        await repo.create(user_id=user.id, promotion_id=test_promotion.id)

    # Count active subscribers
    count = await repo.count_active_subscribers(test_promotion.id)
    assert count == 3

    # Deactivate one subscription
    subs, _ = await repo.list_by_promotion(promotion_id=test_promotion.id, limit=1)
    await repo.deactivate(subs[0])

    # Count again
    count = await repo.count_active_subscribers(test_promotion.id)
    assert count == 2
