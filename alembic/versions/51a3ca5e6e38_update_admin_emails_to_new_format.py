"""update_admin_emails_to_new_format

Revision ID: 51a3ca5e6e38
Revises: 748f01f4ddf3
Create Date: 2026-01-23 19:57:17.592177

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '51a3ca5e6e38'
down_revision: Union[str, Sequence[str], None] = '748f01f4ddf3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
