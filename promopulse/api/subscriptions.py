import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from promopulse.api.schemas.subscriptions import (
    SubscriptionCreatePayload,
    SubscriptionOut,
    SubscriptionListOut,
)
from promopulse.domain.subscriptions.service import SubscriptionService
from promopulse.domain.subscriptions.dependencies import get_subscription_service
from promopulse.domain.subscriptions.exceptions import (
    SubscriptionNotFoundError,
    PromotionNotActiveError,
    UserNotFoundError,
    DuplicateSubscriptionError,
    SubscriptionAlreadyInactiveError,
)


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/subscriptions",
    summary="Create a subscription",
    response_model=SubscriptionOut,
    status_code=201
)
async def create_subscription(
    payload: SubscriptionCreatePayload,
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """
    Create a new subscription to a promotion.

    Business rules enforced:
    - User must exist (404 if not found)
    - Promotion must be ACTIVE (422 if not active)
    - No duplicate subscriptions allowed (409 if duplicate)

    Returns the created subscription.
    """
    try:
        subscription = await subscription_service.create_subscription(
            user_id=payload.user_id,
            promotion_id=payload.promotion_id,
            metadata=payload.metadata,
        )
        return SubscriptionOut.model_validate(subscription)

    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PromotionNotActiveError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except DuplicateSubscriptionError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(
            f"Unexpected error creating subscription: {str(e)}",
            extra={"correlation_id": "-"}
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/subscriptions",
    summary="List subscriptions",
    response_model=SubscriptionListOut
)
async def list_subscriptions(
    user_id: Optional[int] = Query(None, gt=0, description="Filter by user ID"),
    promotion_id: Optional[int] = Query(None, gt=0, description="Filter by promotion ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """
    List subscriptions with filtering.

    Must provide exactly ONE of: user_id OR promotion_id (not both, not neither).

    Supports:
    - Filter by user_id to see all subscriptions for a user
    - Filter by promotion_id to see all subscribers to a promotion
    - Optional is_active filter for both cases
    - Pagination via limit/offset
    """
    # Validation: exactly one of user_id or promotion_id must be provided
    if user_id is None and promotion_id is None:
        raise HTTPException(
            status_code=422,
            detail="Must provide either user_id or promotion_id"
        )
    if user_id is not None and promotion_id is not None:
        raise HTTPException(
            status_code=422,
            detail="Cannot filter by both user_id and promotion_id simultaneously"
        )

    try:
        if user_id is not None:
            subscriptions, total = await subscription_service.list_subscriptions_by_user(
                user_id=user_id,
                is_active=is_active,
                limit=limit,
                offset=offset
            )
        else:  # promotion_id is not None
            subscriptions, total = await subscription_service.list_subscriptions_by_promotion(
                promotion_id=promotion_id,
                is_active=is_active,
                limit=limit,
                offset=offset
            )

        return SubscriptionListOut(
            items=[SubscriptionOut.model_validate(s) for s in subscriptions],
            total=total
        )

    except Exception as e:
        logger.error(
            f"Unexpected error listing subscriptions: {str(e)}",
            extra={"correlation_id": "-"}
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch(
    "/subscriptions/{subscription_id}/deactivate",
    summary="Deactivate a subscription",
    response_model=SubscriptionOut
)
async def deactivate_subscription(
    subscription_id: int,
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """
    Deactivate a subscription (soft delete).

    Sets is_active=False. Idempotent operation - returns 422 if already inactive.
    """
    try:
        subscription = await subscription_service.deactivate_subscription(subscription_id)
        return SubscriptionOut.model_validate(subscription)

    except SubscriptionNotFoundError:
        raise HTTPException(status_code=404, detail="Subscription not found")
    except SubscriptionAlreadyInactiveError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(
            f"Unexpected error deactivating subscription {subscription_id}: {str(e)}",
            extra={"correlation_id": "-"}
        )
        raise HTTPException(status_code=500, detail="Internal server error")
