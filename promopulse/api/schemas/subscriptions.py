from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SubscriptionCreatePayload(BaseModel):
    """Payload for creating a new subscription."""
    user_id: int = Field(..., gt=0, description="ID of the user subscribing")
    promotion_id: int = Field(..., gt=0, description="ID of the promotion to subscribe to")
    metadata: Optional[dict] = Field(None, description="Optional metadata (source, campaign info, etc.)")


class SubscriptionOut(BaseModel):
    """Response model for subscription data."""
    id: int
    user_id: int
    promotion_id: int
    is_active: bool
    subscription_metadata: Optional[dict] = Field(None, serialization_alias="metadata")
    created_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2 compatibility with SQLAlchemy


class SubscriptionListOut(BaseModel):
    """Response model for listing subscriptions."""
    items: list[SubscriptionOut]
    total: int
