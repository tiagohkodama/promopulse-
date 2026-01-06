"""add subscriptions table

Revision ID: b2f11580b088
Revises: 6c169da741c8
Create Date: 2026-01-06 14:22:18.650544

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b2f11580b088'
down_revision = '6c169da741c8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create subscriptions table
    op.create_table('subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('promotion_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        # Primary key
        sa.PrimaryKeyConstraint('id'),

        # Foreign keys with CASCADE delete
        # When user/promotion is deleted, subscriptions are automatically cleaned up
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['promotion_id'], ['promotions.id'], ondelete='CASCADE'),

        # Uniqueness constraint to prevent duplicate subscriptions
        # Handles race conditions at database level
        sa.UniqueConstraint('user_id', 'promotion_id', name='uq_subscription_user_promotion')
    )

    # Create indexes for query performance
    # Single-column indexes for foreign key queries
    op.create_index('ix_subscriptions_user_id', 'subscriptions', ['user_id'])
    op.create_index('ix_subscriptions_promotion_id', 'subscriptions', ['promotion_id'])
    op.create_index('ix_subscriptions_is_active', 'subscriptions', ['is_active'])

    # Composite indexes for common filtering patterns
    op.create_index('ix_subscriptions_user_active', 'subscriptions', ['user_id', 'is_active'])
    op.create_index('ix_subscriptions_promotion_active', 'subscriptions', ['promotion_id', 'is_active'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_subscriptions_promotion_active', table_name='subscriptions')
    op.drop_index('ix_subscriptions_user_active', table_name='subscriptions')
    op.drop_index('ix_subscriptions_is_active', table_name='subscriptions')
    op.drop_index('ix_subscriptions_promotion_id', table_name='subscriptions')
    op.drop_index('ix_subscriptions_user_id', table_name='subscriptions')

    # Drop table (foreign keys are dropped automatically)
    op.drop_table('subscriptions')
