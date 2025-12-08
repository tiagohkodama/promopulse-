from alembic import op
import sqlalchemy as sa  # noqa: F401

# revision identifiers, used by Alembic.
revision = "20241208_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Baseline migration – no schema yet
    pass


def downgrade() -> None:
    # Baseline rollback – no-op
    pass
