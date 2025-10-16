"""merge google auth and phraseset tracking branches

Revision ID: b89f98d236e9
Revises: f5bb6c8b42df, b497c5c16d4b
Create Date: 2025-10-15 23:22:16.207599

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b89f98d236e9'
down_revision: Union[str, None] = ('f5bb6c8b42df', 'b497c5c16d4b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
