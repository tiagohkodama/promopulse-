from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from promopulse.db.models.promotion import PromotionStatus


class PromotionCreatePayload(BaseModel):
    """Payload for creating a new promotion (always starts in DRAFT)."""
    name: str = Field(..., min_length=1, max_length=255, description="Promotion name")
    description: Optional[str] = Field(None, description="Promotion description")
    start_at: datetime = Field(..., description="Promotion start time (timezone-aware)")
    end_at: datetime = Field(..., description="Promotion end time (timezone-aware)")

    @field_validator('end_at')
    @classmethod
    def validate_time_range(cls, end_at: datetime, info) -> datetime:
        """Ensure end_at is after start_at."""
        start_at = info.data.get('start_at')
        if start_at and end_at <= start_at:
            raise ValueError('end_at must be after start_at')
        return end_at


class PromotionUpdatePayload(BaseModel):
    """
    Payload for updating a promotion.

    Fields allowed depend on status:
    - DRAFT: all fields
    - ACTIVE: name, description only
    - ENDED: no updates allowed
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None

    @field_validator('end_at')
    @classmethod
    def validate_time_range(cls, end_at: Optional[datetime], info) -> Optional[datetime]:
        """Ensure end_at is after start_at if both provided."""
        if end_at is None:
            return end_at
        start_at = info.data.get('start_at')
        if start_at and end_at <= start_at:
            raise ValueError('end_at must be after start_at')
        return end_at


class PromotionStatusChangePayload(BaseModel):
    """Payload for changing promotion status."""
    status: PromotionStatus = Field(..., description="New status to transition to")


class PromotionOut(BaseModel):
    """Response model for promotion data."""
    id: int
    name: str
    description: Optional[str]
    status: PromotionStatus
    start_at: datetime
    end_at: datetime
    created_at: datetime
    updated_at: datetime
    created_by: int

    class Config:
        from_attributes = True  # Pydantic v2 compatibility with SQLAlchemy


class PromotionListOut(BaseModel):
    """Response model for listing promotions."""
    items: list[PromotionOut]
    total: int
