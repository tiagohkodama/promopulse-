import logging
from datetime import datetime
from typing import Optional

from promopulse.api.schemas.promotions import (
    PromotionCreatePayload,
    PromotionUpdatePayload,
)
from promopulse.db.models.promotion import Promotion, PromotionStatus
from promopulse.infrastructure.promotions.repository import PromotionRepository
from .exceptions import (
    InvalidPromotionStatusTransitionError,
    PromotionNotEditableError,
    PromotionNotFoundError,
    InvalidTimeRangeError,
)


logger = logging.getLogger(__name__)


class PromotionService:
    """Service for promotion business logic and lifecycle management."""

    # Define valid state transitions (one-way only)
    VALID_TRANSITIONS = {
        PromotionStatus.DRAFT: [PromotionStatus.ACTIVE],
        PromotionStatus.ACTIVE: [PromotionStatus.ENDED],
        PromotionStatus.ENDED: [],  # Terminal state
    }

    # Define which fields are editable in each status
    EDITABLE_FIELDS = {
        PromotionStatus.DRAFT: {'name', 'description', 'start_at', 'end_at'},
        PromotionStatus.ACTIVE: {'name', 'description'},  # Limited editing
        PromotionStatus.ENDED: set(),  # Read-only
    }

    def __init__(self, repository: PromotionRepository):
        self.repository = repository

    def _validate_time_range(self, start_at: datetime, end_at: datetime) -> None:
        """Validate that time range is logically consistent."""
        if end_at <= start_at:
            raise InvalidTimeRangeError(
                f"end_at ({end_at}) must be after start_at ({start_at})"
            )

    def _validate_status_transition(
        self,
        current_status: PromotionStatus,
        target_status: PromotionStatus
    ) -> None:
        """
        Validate that status transition is allowed.

        Valid transitions:
        - DRAFT → ACTIVE
        - ACTIVE → ENDED

        Raises:
            InvalidPromotionStatusTransitionError: If transition is invalid
        """
        if current_status == target_status:
            return  # No transition needed

        valid_targets = self.VALID_TRANSITIONS.get(current_status, [])
        if target_status not in valid_targets:
            raise InvalidPromotionStatusTransitionError(
                current_status.value,
                target_status.value
            )

    def _validate_field_editable(
        self,
        status: PromotionStatus,
        field_name: str
    ) -> None:
        """
        Check if a field can be edited in the current status.

        Raises:
            PromotionNotEditableError: If field cannot be edited
        """
        editable_fields = self.EDITABLE_FIELDS.get(status, set())
        if field_name not in editable_fields:
            raise PromotionNotEditableError(status.value, field_name)

    async def create_promotion(
        self,
        payload: PromotionCreatePayload,
        created_by_user_id: int
    ) -> Promotion:
        """
        Create a new promotion in DRAFT status.

        Args:
            payload: Promotion creation data
            created_by_user_id: ID of user creating the promotion

        Returns:
            Created Promotion instance

        Raises:
            InvalidTimeRangeError: If time range is invalid
        """
        # Validate time range
        self._validate_time_range(payload.start_at, payload.end_at)

        logger.info(
            f"Creating promotion: name={payload.name}, created_by={created_by_user_id}",
            extra={"correlation_id": "-"}
        )

        promotion = await self.repository.create(
            name=payload.name,
            description=payload.description,
            start_at=payload.start_at,
            end_at=payload.end_at,
            created_by=created_by_user_id,
            status=PromotionStatus.DRAFT,
        )

        return promotion

    async def get_promotion_by_id(self, promotion_id: int) -> Optional[Promotion]:
        """Get promotion by ID."""
        return await self.repository.get_by_id(promotion_id)

    async def list_promotions(
        self,
        status_filter: Optional[PromotionStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[list[Promotion], int]:
        """
        List promotions with optional status filtering.

        Returns:
            Tuple of (promotions list, total count)
        """
        return await self.repository.list_promotions(
            status_filter=status_filter,
            limit=limit,
            offset=offset
        )

    async def update_promotion(
        self,
        promotion_id: int,
        payload: PromotionUpdatePayload
    ) -> Promotion:
        """
        Update promotion fields (respecting status-based restrictions).

        Rules:
        - DRAFT: all fields editable
        - ACTIVE: only name and description editable
        - ENDED: no updates allowed

        Raises:
            PromotionNotFoundError: If promotion not found
            PromotionNotEditableError: If field cannot be edited in current status
            InvalidTimeRangeError: If new time range is invalid
        """
        promotion = await self.repository.get_by_id(promotion_id)
        if not promotion:
            raise PromotionNotFoundError(f"Promotion {promotion_id} not found")

        # Build dict of fields to update
        update_data = payload.model_dump(exclude_unset=True)

        # Validate each field is editable in current status
        for field_name in update_data.keys():
            self._validate_field_editable(promotion.status, field_name)

        # If updating time range, validate consistency
        new_start = update_data.get('start_at', promotion.start_at)
        new_end = update_data.get('end_at', promotion.end_at)
        if 'start_at' in update_data or 'end_at' in update_data:
            self._validate_time_range(new_start, new_end)

        logger.info(
            f"Updating promotion {promotion_id}: fields={list(update_data.keys())}",
            extra={"correlation_id": "-"}
        )

        return await self.repository.update(promotion, update_data)

    async def change_promotion_status(
        self,
        promotion_id: int,
        target_status: PromotionStatus
    ) -> Promotion:
        """
        Change promotion status (with transition validation).

        Valid transitions: DRAFT→ACTIVE, ACTIVE→ENDED

        Raises:
            PromotionNotFoundError: If promotion not found
            InvalidPromotionStatusTransitionError: If transition is invalid
        """
        promotion = await self.repository.get_by_id(promotion_id)
        if not promotion:
            raise PromotionNotFoundError(f"Promotion {promotion_id} not found")

        # Validate transition
        self._validate_status_transition(promotion.status, target_status)

        logger.info(
            f"Changing promotion {promotion_id} status: "
            f"{promotion.status.value} → {target_status.value}",
            extra={"correlation_id": "-"}
        )

        return await self.repository.update_status(promotion, target_status)
