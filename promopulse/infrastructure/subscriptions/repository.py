import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from promopulse.db.models.subscription import Subscription


logger = logging.getLogger(__name__)


class SubscriptionRepository:
    """Repository for Subscription database operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        user_id: int,
        promotion_id: int,
        metadata: Optional[dict] = None
    ) -> Subscription:
        """
        Create a new subscription in the database.

        Args:
            user_id: ID of the user subscribing
            promotion_id: ID of the promotion being subscribed to
            metadata: Optional metadata (e.g., source, campaign info)

        Returns:
            The created Subscription instance

        Raises:
            IntegrityError: If duplicate subscription exists (unique constraint violation)
        """
        subscription = Subscription(
            user_id=user_id,
            promotion_id=promotion_id,
            is_active=True,
            subscription_metadata=metadata,
        )

        self.session.add(subscription)
        await self.session.commit()
        await self.session.refresh(subscription)

        logger.info(
            f"Subscription created: id={subscription.id}, user_id={user_id}, promotion_id={promotion_id}",
            extra={"correlation_id": "-"}
        )

        return subscription

    async def get_by_id(self, subscription_id: int) -> Optional[Subscription]:
        """Get a subscription by ID."""
        result = await self.session.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        return result.scalar_one_or_none()

    async def get_active_subscription(
        self,
        user_id: int,
        promotion_id: int
    ) -> Optional[Subscription]:
        """
        Get active subscription for a user-promotion pair.

        Used to check for existing active subscriptions before creating new ones.

        Args:
            user_id: ID of the user
            promotion_id: ID of the promotion

        Returns:
            Active Subscription if exists, None otherwise
        """
        result = await self.session.execute(
            select(Subscription).where(
                and_(
                    Subscription.user_id == user_id,
                    Subscription.promotion_id == promotion_id,
                    Subscription.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        *,
        user_id: int,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[list[Subscription], int]:
        """
        List subscriptions for a specific user with optional filtering.

        Args:
            user_id: ID of the user
            is_active: Optional filter for active/inactive subscriptions
            limit: Maximum items to return
            offset: Number of items to skip

        Returns:
            Tuple of (subscriptions list, total count)
        """
        # Build base query
        query = select(Subscription).where(Subscription.user_id == user_id)
        count_query = select(func.count()).select_from(Subscription).where(
            Subscription.user_id == user_id
        )

        # Apply is_active filter if provided
        if is_active is not None:
            query = query.where(Subscription.is_active == is_active)
            count_query = count_query.where(Subscription.is_active == is_active)

        # Get total count
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()

        # Apply pagination and ordering (newest first)
        query = query.order_by(Subscription.created_at.desc()).limit(limit).offset(offset)

        # Execute query
        result = await self.session.execute(query)
        subscriptions = list(result.scalars().all())

        return subscriptions, total

    async def list_by_promotion(
        self,
        *,
        promotion_id: int,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[list[Subscription], int]:
        """
        List subscriptions for a specific promotion with optional filtering.

        Args:
            promotion_id: ID of the promotion
            is_active: Optional filter for active/inactive subscriptions
            limit: Maximum items to return
            offset: Number of items to skip

        Returns:
            Tuple of (subscriptions list, total count)
        """
        # Build base query
        query = select(Subscription).where(Subscription.promotion_id == promotion_id)
        count_query = select(func.count()).select_from(Subscription).where(
            Subscription.promotion_id == promotion_id
        )

        # Apply is_active filter if provided
        if is_active is not None:
            query = query.where(Subscription.is_active == is_active)
            count_query = count_query.where(Subscription.is_active == is_active)

        # Get total count
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()

        # Apply pagination and ordering (newest first)
        query = query.order_by(Subscription.created_at.desc()).limit(limit).offset(offset)

        # Execute query
        result = await self.session.execute(query)
        subscriptions = list(result.scalars().all())

        return subscriptions, total

    async def deactivate(self, subscription: Subscription) -> Subscription:
        """
        Deactivate a subscription (soft delete).

        Args:
            subscription: Subscription instance to deactivate

        Returns:
            Updated Subscription instance
        """
        subscription.is_active = False

        await self.session.commit()
        await self.session.refresh(subscription)

        logger.info(
            f"Subscription {subscription.id} deactivated",
            extra={"correlation_id": "-"}
        )

        return subscription

    async def count_active_subscribers(self, promotion_id: int) -> int:
        """
        Count active subscribers for a promotion.

        Useful for analytics and future rate limiting features.

        Args:
            promotion_id: ID of the promotion

        Returns:
            Count of active subscriptions
        """
        result = await self.session.execute(
            select(func.count()).select_from(Subscription).where(
                and_(
                    Subscription.promotion_id == promotion_id,
                    Subscription.is_active == True
                )
            )
        )
        return result.scalar()
