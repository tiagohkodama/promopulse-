import logging
from typing import Optional
from sqlalchemy.exc import IntegrityError

from promopulse.db.models.subscription import Subscription
from promopulse.db.models.promotion import PromotionStatus
from promopulse.infrastructure.subscriptions.repository import SubscriptionRepository
from promopulse.infrastructure.users.repository import UserRepository
from promopulse.infrastructure.promotions.repository import PromotionRepository
from .exceptions import (
    SubscriptionNotFoundError,
    PromotionNotActiveError,
    UserNotFoundError,
    DuplicateSubscriptionError,
    SubscriptionAlreadyInactiveError,
)


logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service for subscription business logic and validation."""

    def __init__(
        self,
        subscription_repository: SubscriptionRepository,
        user_repository: UserRepository,
        promotion_repository: PromotionRepository,
    ):
        self.subscription_repository = subscription_repository
        self.user_repository = user_repository
        self.promotion_repository = promotion_repository

    async def _validate_user_exists(self, user_id: int) -> None:
        """
        Validate that user exists.

        Args:
            user_id: ID of the user to validate

        Raises:
            UserNotFoundError: If user does not exist
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)

    async def _validate_promotion_is_active(self, promotion_id: int) -> None:
        """
        Validate that promotion exists and is in ACTIVE status.

        Args:
            promotion_id: ID of the promotion to validate

        Raises:
            PromotionNotActiveError: If promotion is not ACTIVE
        """
        promotion = await self.promotion_repository.get_by_id(promotion_id)
        if not promotion:
            raise PromotionNotActiveError(promotion_id, "not_found")

        if promotion.status != PromotionStatus.ACTIVE:
            raise PromotionNotActiveError(promotion_id, promotion.status.value)

    async def create_subscription(
        self,
        *,
        user_id: int,
        promotion_id: int,
        metadata: Optional[dict] = None
    ) -> Subscription:
        """
        Create a new subscription with full validation.

        Business rules enforced:
        1. User must exist
        2. Promotion must be ACTIVE
        3. No duplicate active subscription for same user/promotion pair

        Args:
            user_id: ID of the user subscribing
            promotion_id: ID of the promotion being subscribed to
            metadata: Optional metadata (e.g., source, campaign tracking)

        Returns:
            Created Subscription instance

        Raises:
            UserNotFoundError: If user does not exist
            PromotionNotActiveError: If promotion is not ACTIVE
            DuplicateSubscriptionError: If active subscription already exists
        """
        logger.info(
            f"Creating subscription: user_id={user_id}, promotion_id={promotion_id}",
            extra={"correlation_id": "-"}
        )

        # Validation 1: User must exist
        await self._validate_user_exists(user_id)

        # Validation 2: Promotion must be ACTIVE
        await self._validate_promotion_is_active(promotion_id)

        # Validation 3: Check for existing active subscription
        existing = await self.subscription_repository.get_active_subscription(
            user_id=user_id,
            promotion_id=promotion_id
        )
        if existing:
            raise DuplicateSubscriptionError(user_id, promotion_id)

        # Create subscription
        try:
            subscription = await self.subscription_repository.create(
                user_id=user_id,
                promotion_id=promotion_id,
                metadata=metadata,
            )
            return subscription
        except IntegrityError as e:
            # Race condition: another request created the subscription concurrently
            # The DB uniqueness constraint caught it
            logger.warning(
                f"Integrity error creating subscription (race condition): {str(e)}",
                extra={"correlation_id": "-"}
            )
            raise DuplicateSubscriptionError(user_id, promotion_id)

    async def get_subscription_by_id(self, subscription_id: int) -> Optional[Subscription]:
        """
        Get subscription by ID.

        Args:
            subscription_id: ID of the subscription

        Returns:
            Subscription instance or None if not found
        """
        return await self.subscription_repository.get_by_id(subscription_id)

    async def list_subscriptions_by_user(
        self,
        *,
        user_id: int,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[list[Subscription], int]:
        """
        List subscriptions for a specific user.

        Args:
            user_id: ID of the user
            is_active: Optional filter for active/inactive subscriptions
            limit: Maximum items to return
            offset: Number of items to skip

        Returns:
            Tuple of (subscriptions list, total count)
        """
        return await self.subscription_repository.list_by_user(
            user_id=user_id,
            is_active=is_active,
            limit=limit,
            offset=offset
        )

    async def list_subscriptions_by_promotion(
        self,
        *,
        promotion_id: int,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[list[Subscription], int]:
        """
        List subscriptions for a specific promotion.

        Args:
            promotion_id: ID of the promotion
            is_active: Optional filter for active/inactive subscriptions
            limit: Maximum items to return
            offset: Number of items to skip

        Returns:
            Tuple of (subscriptions list, total count)
        """
        return await self.subscription_repository.list_by_promotion(
            promotion_id=promotion_id,
            is_active=is_active,
            limit=limit,
            offset=offset
        )

    async def deactivate_subscription(self, subscription_id: int) -> Subscription:
        """
        Deactivate a subscription.

        Args:
            subscription_id: ID of subscription to deactivate

        Returns:
            Updated Subscription instance

        Raises:
            SubscriptionNotFoundError: If subscription not found
            SubscriptionAlreadyInactiveError: If subscription already inactive
        """
        subscription = await self.subscription_repository.get_by_id(subscription_id)
        if not subscription:
            raise SubscriptionNotFoundError(f"Subscription {subscription_id} not found")

        if not subscription.is_active:
            raise SubscriptionAlreadyInactiveError(subscription_id)

        logger.info(
            f"Deactivating subscription {subscription_id}",
            extra={"correlation_id": "-"}
        )

        return await self.subscription_repository.deactivate(subscription)
