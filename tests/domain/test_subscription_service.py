import pytest
from unittest.mock import AsyncMock
from sqlalchemy.exc import IntegrityError

from promopulse.domain.subscriptions.service import SubscriptionService
from promopulse.domain.subscriptions.exceptions import (
    PromotionNotActiveError,
    UserNotFoundError,
    DuplicateSubscriptionError,
    SubscriptionNotFoundError,
    SubscriptionAlreadyInactiveError,
)
from promopulse.db.models.subscription import Subscription
from promopulse.db.models.promotion import Promotion, PromotionStatus
from promopulse.db.models.user import User


@pytest.fixture
def mock_subscription_repository():
    return AsyncMock()


@pytest.fixture
def mock_user_repository():
    return AsyncMock()


@pytest.fixture
def mock_promotion_repository():
    return AsyncMock()


@pytest.fixture
def subscription_service(
    mock_subscription_repository,
    mock_user_repository,
    mock_promotion_repository
):
    return SubscriptionService(
        mock_subscription_repository,
        mock_user_repository,
        mock_promotion_repository
    )


class TestCreateSubscription:
    """Tests for create_subscription business logic."""

    @pytest.mark.asyncio
    async def test_create_subscription_success(
        self,
        subscription_service,
        mock_user_repository,
        mock_promotion_repository,
        mock_subscription_repository
    ):
        """Test successful subscription creation."""
        # Arrange
        user_id = 1
        promotion_id = 2

        # Mock user exists
        mock_user = User(id=user_id, full_name="Test User", encrypted_email="test@example.com")
        mock_user_repository.get_by_id.return_value = mock_user

        # Mock promotion is ACTIVE
        mock_promotion = Promotion(
            id=promotion_id,
            name="Test Promotion",
            status=PromotionStatus.ACTIVE
        )
        mock_promotion_repository.get_by_id.return_value = mock_promotion

        # Mock no existing subscription
        mock_subscription_repository.get_active_subscription.return_value = None

        # Mock subscription creation
        created_sub = Subscription(
            id=1,
            user_id=user_id,
            promotion_id=promotion_id,
            is_active=True
        )
        mock_subscription_repository.create.return_value = created_sub

        # Act
        result = await subscription_service.create_subscription(
            user_id=user_id,
            promotion_id=promotion_id
        )

        # Assert
        assert result.id == 1
        assert result.user_id == user_id
        assert result.promotion_id == promotion_id
        assert result.is_active is True
        mock_subscription_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_subscription_user_not_found(
        self,
        subscription_service,
        mock_user_repository
    ):
        """Test subscription creation fails when user doesn't exist."""
        # Arrange
        mock_user_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(UserNotFoundError) as exc_info:
            await subscription_service.create_subscription(
                user_id=999,
                promotion_id=1
            )

        assert exc_info.value.user_id == 999

    @pytest.mark.asyncio
    async def test_create_subscription_promotion_not_found(
        self,
        subscription_service,
        mock_user_repository,
        mock_promotion_repository
    ):
        """Test subscription creation fails when promotion doesn't exist."""
        # Arrange
        mock_user = User(id=1, full_name="Test User", encrypted_email="test@example.com")
        mock_user_repository.get_by_id.return_value = mock_user
        mock_promotion_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(PromotionNotActiveError) as exc_info:
            await subscription_service.create_subscription(
                user_id=1,
                promotion_id=999
            )

        assert exc_info.value.promotion_id == 999
        assert exc_info.value.status == "not_found"

    @pytest.mark.asyncio
    async def test_create_subscription_promotion_not_active(
        self,
        subscription_service,
        mock_user_repository,
        mock_promotion_repository
    ):
        """Test subscription creation fails when promotion is not ACTIVE."""
        # Arrange
        mock_user = User(id=1, full_name="Test User", encrypted_email="test@example.com")
        mock_user_repository.get_by_id.return_value = mock_user

        mock_promotion = Promotion(
            id=1,
            name="Test Promotion",
            status=PromotionStatus.DRAFT
        )
        mock_promotion_repository.get_by_id.return_value = mock_promotion

        # Act & Assert
        with pytest.raises(PromotionNotActiveError) as exc_info:
            await subscription_service.create_subscription(
                user_id=1,
                promotion_id=1
            )

        assert exc_info.value.status == "draft"

    @pytest.mark.asyncio
    async def test_create_subscription_duplicate_active(
        self,
        subscription_service,
        mock_user_repository,
        mock_promotion_repository,
        mock_subscription_repository
    ):
        """Test subscription creation fails when active subscription already exists."""
        # Arrange
        mock_user = User(id=1, full_name="Test User", encrypted_email="test@example.com")
        mock_user_repository.get_by_id.return_value = mock_user

        mock_promotion = Promotion(
            id=1,
            name="Test Promotion",
            status=PromotionStatus.ACTIVE
        )
        mock_promotion_repository.get_by_id.return_value = mock_promotion

        # Existing active subscription
        mock_subscription_repository.get_active_subscription.return_value = Subscription(
            id=99,
            user_id=1,
            promotion_id=1,
            is_active=True
        )

        # Act & Assert
        with pytest.raises(DuplicateSubscriptionError) as exc_info:
            await subscription_service.create_subscription(
                user_id=1,
                promotion_id=1
            )

        assert exc_info.value.user_id == 1
        assert exc_info.value.promotion_id == 1

    @pytest.mark.asyncio
    async def test_create_subscription_race_condition_integrity_error(
        self,
        subscription_service,
        mock_user_repository,
        mock_promotion_repository,
        mock_subscription_repository
    ):
        """Test subscription creation handles race condition (IntegrityError)."""
        # Arrange
        mock_user = User(id=1, full_name="Test User", encrypted_email="test@example.com")
        mock_user_repository.get_by_id.return_value = mock_user

        mock_promotion = Promotion(
            id=1,
            name="Test Promotion",
            status=PromotionStatus.ACTIVE
        )
        mock_promotion_repository.get_by_id.return_value = mock_promotion

        mock_subscription_repository.get_active_subscription.return_value = None

        # Simulate race condition: IntegrityError on create
        mock_subscription_repository.create.side_effect = IntegrityError(
            "duplicate key",
            {},
            None
        )

        # Act & Assert
        with pytest.raises(DuplicateSubscriptionError):
            await subscription_service.create_subscription(
                user_id=1,
                promotion_id=1
            )


class TestDeactivateSubscription:
    """Tests for deactivate_subscription business logic."""

    @pytest.mark.asyncio
    async def test_deactivate_subscription_success(
        self,
        subscription_service,
        mock_subscription_repository
    ):
        """Test successful subscription deactivation."""
        # Arrange
        active_sub = Subscription(id=1, user_id=1, promotion_id=1, is_active=True)
        mock_subscription_repository.get_by_id.return_value = active_sub

        deactivated_sub = Subscription(id=1, user_id=1, promotion_id=1, is_active=False)
        mock_subscription_repository.deactivate.return_value = deactivated_sub

        # Act
        result = await subscription_service.deactivate_subscription(1)

        # Assert
        assert result.is_active is False
        mock_subscription_repository.deactivate.assert_called_once_with(active_sub)

    @pytest.mark.asyncio
    async def test_deactivate_subscription_not_found(
        self,
        subscription_service,
        mock_subscription_repository
    ):
        """Test deactivation fails when subscription doesn't exist."""
        # Arrange
        mock_subscription_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(SubscriptionNotFoundError):
            await subscription_service.deactivate_subscription(999)

    @pytest.mark.asyncio
    async def test_deactivate_subscription_already_inactive(
        self,
        subscription_service,
        mock_subscription_repository
    ):
        """Test deactivation fails when subscription is already inactive."""
        # Arrange
        inactive_sub = Subscription(id=1, user_id=1, promotion_id=1, is_active=False)
        mock_subscription_repository.get_by_id.return_value = inactive_sub

        # Act & Assert
        with pytest.raises(SubscriptionAlreadyInactiveError):
            await subscription_service.deactivate_subscription(1)
