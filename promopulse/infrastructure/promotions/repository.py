import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from promopulse.db.models.promotion import Promotion, PromotionStatus


logger = logging.getLogger(__name__)


class PromotionRepository:
    """Repository for Promotion database operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        name: str,
        description: Optional[str],
        start_at,
        end_at,
        created_by: int,
        status: PromotionStatus,
    ) -> Promotion:
        """
        Create a new promotion in the database.

        Returns:
            The created Promotion instance
        """
        promotion = Promotion(
            name=name,
            description=description,
            start_at=start_at,
            end_at=end_at,
            created_by=created_by,
            status=status,
        )

        self.session.add(promotion)
        await self.session.commit()
        await self.session.refresh(promotion)

        logger.info(
            f"Promotion created successfully with id={promotion.id}",
            extra={"correlation_id": "-"}
        )

        return promotion

    async def get_by_id(self, promotion_id: int) -> Optional[Promotion]:
        """Get a promotion by ID."""
        result = await self.session.execute(
            select(Promotion).where(Promotion.id == promotion_id)
        )
        return result.scalar_one_or_none()

    async def list_promotions(
        self,
        *,
        status_filter: Optional[PromotionStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[list[Promotion], int]:
        """
        List promotions with optional filtering and pagination.

        Returns:
            Tuple of (promotions list, total count)
        """
        # Build base query
        query = select(Promotion)
        count_query = select(func.count()).select_from(Promotion)

        # Apply status filter if provided
        if status_filter:
            query = query.where(Promotion.status == status_filter)
            count_query = count_query.where(Promotion.status == status_filter)

        # Get total count
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()

        # Apply pagination and ordering
        query = query.order_by(Promotion.created_at.desc()).limit(limit).offset(offset)

        # Execute query
        result = await self.session.execute(query)
        promotions = list(result.scalars().all())

        return promotions, total

    async def update(
        self,
        promotion: Promotion,
        update_data: dict
    ) -> Promotion:
        """
        Update promotion fields.

        Args:
            promotion: Promotion instance to update
            update_data: Dict of field names to new values

        Returns:
            Updated Promotion instance
        """
        for field, value in update_data.items():
            setattr(promotion, field, value)

        await self.session.commit()
        await self.session.refresh(promotion)

        logger.info(
            f"Promotion {promotion.id} updated successfully",
            extra={"correlation_id": "-"}
        )

        return promotion

    async def update_status(
        self,
        promotion: Promotion,
        new_status: PromotionStatus
    ) -> Promotion:
        """
        Update promotion status.

        Returns:
            Updated Promotion instance
        """
        promotion.status = new_status

        await self.session.commit()
        await self.session.refresh(promotion)

        logger.info(
            f"Promotion {promotion.id} status changed to {new_status.value}",
            extra={"correlation_id": "-"}
        )

        return promotion
