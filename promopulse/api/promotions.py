import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from promopulse.api.schemas.promotions import (
    PromotionCreatePayload,
    PromotionUpdatePayload,
    PromotionStatusChangePayload,
    PromotionOut,
    PromotionListOut,
)
from promopulse.db.models.promotion import PromotionStatus
from promopulse.domain.promotions.service import PromotionService
from promopulse.domain.promotions.dependencies import get_promotion_service
from promopulse.domain.promotions.exceptions import (
    InvalidPromotionStatusTransitionError,
    PromotionNotEditableError,
    PromotionNotFoundError,
    InvalidTimeRangeError,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# TODO: Replace with real authentication once implemented
MOCK_USER_ID = 1  # Temporary: assumes user with ID 1 exists


@router.post(
    "/promotions",
    summary="Create a promotion",
    response_model=PromotionOut,
    status_code=201
)
async def create_promotion(
    payload: PromotionCreatePayload,
    promotion_service: PromotionService = Depends(get_promotion_service),
):
    """
    Create a new promotion in DRAFT status.

    - Validates time range (end_at > start_at)
    - Assigns created_by to current user
    - Returns created promotion
    """
    try:
        promotion = await promotion_service.create_promotion(
            payload=payload,
            created_by_user_id=MOCK_USER_ID  # TODO: Replace with authenticated user
        )
        return PromotionOut.model_validate(promotion)

    except InvalidTimeRangeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(
            f"Unexpected error creating promotion: {str(e)}",
            extra={"correlation_id": "-"}
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/promotions/{promotion_id}",
    summary="Get promotion by ID",
    response_model=PromotionOut
)
async def get_promotion(
    promotion_id: int,
    promotion_service: PromotionService = Depends(get_promotion_service),
):
    """Get a promotion by its ID."""
    promotion = await promotion_service.get_promotion_by_id(promotion_id)

    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found")

    return PromotionOut.model_validate(promotion)


@router.get(
    "/promotions",
    summary="List promotions",
    response_model=PromotionListOut
)
async def list_promotions(
    status: Optional[PromotionStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    promotion_service: PromotionService = Depends(get_promotion_service),
):
    """
    List promotions with optional filtering by status.

    - Supports pagination via limit/offset
    - Returns total count for client-side pagination
    """
    promotions, total = await promotion_service.list_promotions(
        status_filter=status,
        limit=limit,
        offset=offset
    )

    return PromotionListOut(
        items=[PromotionOut.model_validate(p) for p in promotions],
        total=total
    )


@router.patch(
    "/promotions/{promotion_id}",
    summary="Update promotion fields",
    response_model=PromotionOut
)
async def update_promotion(
    promotion_id: int,
    payload: PromotionUpdatePayload,
    promotion_service: PromotionService = Depends(get_promotion_service),
):
    """
    Update promotion fields (restrictions apply based on status).

    Editable fields by status:
    - DRAFT: all fields (name, description, start_at, end_at)
    - ACTIVE: limited fields (name, description only)
    - ENDED: no updates allowed
    """
    try:
        promotion = await promotion_service.update_promotion(
            promotion_id=promotion_id,
            payload=payload
        )
        return PromotionOut.model_validate(promotion)

    except PromotionNotFoundError:
        raise HTTPException(status_code=404, detail="Promotion not found")
    except PromotionNotEditableError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except InvalidTimeRangeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(
            f"Unexpected error updating promotion {promotion_id}: {str(e)}",
            extra={"correlation_id": "-"}
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/promotions/{promotion_id}/status",
    summary="Change promotion status",
    response_model=PromotionOut
)
async def change_promotion_status(
    promotion_id: int,
    payload: PromotionStatusChangePayload,
    promotion_service: PromotionService = Depends(get_promotion_service),
):
    """
    Change promotion status with validation.

    Valid transitions (one-way only):
    - DRAFT → ACTIVE
    - ACTIVE → ENDED

    Invalid transitions return 422 with descriptive error.
    """
    try:
        promotion = await promotion_service.change_promotion_status(
            promotion_id=promotion_id,
            target_status=payload.status
        )
        return PromotionOut.model_validate(promotion)

    except PromotionNotFoundError:
        raise HTTPException(status_code=404, detail="Promotion not found")
    except InvalidPromotionStatusTransitionError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(
            f"Unexpected error changing status for promotion {promotion_id}: {str(e)}",
            extra={"correlation_id": "-"}
        )
        raise HTTPException(status_code=500, detail="Internal server error")
