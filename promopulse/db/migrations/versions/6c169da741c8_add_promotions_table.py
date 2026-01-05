"""add promotions table

Revision ID: 6c169da741c8
Revises: 652e60e2bfd9
Create Date: 2026-01-05 15:17:58.927427

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '6c169da741c8'
down_revision = '652e60e2bfd9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create promotions table
    op.create_table('promotions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('status', sa.Enum('DRAFT', 'ACTIVE', 'ENDED', name='promotionstatus'), nullable=False),
    sa.Column('start_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('end_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for query performance
    op.create_index('ix_promotions_status', 'promotions', ['status'])
    op.create_index('ix_promotions_start_at', 'promotions', ['start_at'])
    op.create_index('ix_promotions_end_at', 'promotions', ['end_at'])
    op.create_index('ix_promotions_created_by', 'promotions', ['created_by'])
    # Composite index for common filtering patterns
    op.create_index('ix_promotions_status_start_end', 'promotions', ['status', 'start_at', 'end_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_promotions_status_start_end', table_name='promotions')
    op.drop_index('ix_promotions_created_by', table_name='promotions')
    op.drop_index('ix_promotions_end_at', table_name='promotions')
    op.drop_index('ix_promotions_start_at', table_name='promotions')
    op.drop_index('ix_promotions_status', table_name='promotions')

    # Drop table (will also drop the enum type)
    op.drop_table('promotions')
    op.execute('DROP TYPE promotionstatus')
