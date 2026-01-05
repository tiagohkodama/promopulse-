from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from promopulse.db.session import get_async_session
from promopulse.infrastructure.promotions.repository import PromotionRepository
from promopulse.domain.promotions.service import PromotionService


def get_promotion_repository(
    session: AsyncSession = Depends(get_async_session)
) -> PromotionRepository:
    """FastAPI dependency to get PromotionRepository instance."""
    return PromotionRepository(session)


def get_promotion_service(
    repository: PromotionRepository = Depends(get_promotion_repository),
) -> PromotionService:
    """FastAPI dependency to get PromotionService instance."""
    return PromotionService(repository)
