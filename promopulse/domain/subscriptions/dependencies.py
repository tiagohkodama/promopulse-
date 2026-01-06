from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from promopulse.db.session import get_async_session
from promopulse.infrastructure.subscriptions.repository import SubscriptionRepository
from promopulse.infrastructure.users.repository import UserRepository
from promopulse.infrastructure.promotions.repository import PromotionRepository
from promopulse.domain.subscriptions.service import SubscriptionService

# Import dependencies from other domains
from promopulse.domain.users.dependencies import get_user_repository
from promopulse.domain.promotions.dependencies import get_promotion_repository


def get_subscription_repository(
    session: AsyncSession = Depends(get_async_session)
) -> SubscriptionRepository:
    """FastAPI dependency to get SubscriptionRepository instance."""
    return SubscriptionRepository(session)


def get_subscription_service(
    subscription_repository: SubscriptionRepository = Depends(get_subscription_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    promotion_repository: PromotionRepository = Depends(get_promotion_repository),
) -> SubscriptionService:
    """FastAPI dependency to get SubscriptionService instance."""
    return SubscriptionService(
        subscription_repository,
        user_repository,
        promotion_repository
    )
