from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, func
from enum import Enum as PyEnum

from .base import Base


class PromotionStatus(str, PyEnum):
    """
    Promotion lifecycle states.

    Transitions: DRAFT → ACTIVE → ENDED (one-way only)
    """
    DRAFT = "draft"
    ACTIVE = "active"
    ENDED = "ended"


class Promotion(Base):
    __tablename__ = "promotions"

    # Primary key
    id = Column(Integer, primary_key=True)

    # Core fields
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(PromotionStatus), nullable=False, default=PromotionStatus.DRAFT)

    # Time range fields
    start_at = Column(DateTime(timezone=True), nullable=False)
    end_at = Column(DateTime(timezone=True), nullable=False)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
