from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean, func, JSON, UniqueConstraint, Index

from .base import Base


class Subscription(Base):
    """
    Subscription model linking users to promotions.

    Business rules:
    - User can subscribe only to ACTIVE promotions (enforced in service layer)
    - Each user can subscribe to a promotion only once (DB-level uniqueness constraint)
    - Subscriptions can be deactivated (soft delete via is_active flag)
    - Metadata field for extensibility (event tracking, campaign info, etc.)
    """
    __tablename__ = "subscriptions"

    # Primary key
    id = Column(Integer, primary_key=True)

    # Foreign keys with CASCADE delete
    # When user/promotion is deleted, subscriptions are automatically cleaned up
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    promotion_id = Column(Integer, ForeignKey("promotions.id", ondelete="CASCADE"), nullable=False)

    # Core fields
    is_active = Column(Boolean, nullable=False, default=True)
    subscription_metadata = Column("metadata", JSON, nullable=True)  # JSONB in PostgreSQL for extensibility

    # Audit fields
    # No updated_at since subscriptions are created then deactivated (no updates)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Constraints and indexes
    __table_args__ = (
        # DB-level uniqueness constraint prevents duplicate subscriptions
        # Handles race conditions at database level
        UniqueConstraint('user_id', 'promotion_id', name='uq_subscription_user_promotion'),

        # Single-column indexes for foreign key queries
        Index('ix_subscriptions_user_id', 'user_id'),
        Index('ix_subscriptions_promotion_id', 'promotion_id'),
        Index('ix_subscriptions_is_active', 'is_active'),

        # Composite indexes for common filtering patterns
        Index('ix_subscriptions_user_active', 'user_id', 'is_active'),
        Index('ix_subscriptions_promotion_active', 'promotion_id', 'is_active'),
    )
