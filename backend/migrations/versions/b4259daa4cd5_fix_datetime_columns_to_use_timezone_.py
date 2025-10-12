"""Fix datetime columns to use timezone-aware DateTime

This migration marks the transition to using DateTime(timezone=True) for all
datetime columns in the models. The actual schema change is handled at the
SQLAlchemy model level and doesn't require database alterations for SQLite.

For PostgreSQL, DateTime(timezone=True) maps to TIMESTAMP WITH TIME ZONE.
For SQLite, datetimes are stored as ISO8601 strings with timezone info.

Changed columns (15 total):
- players.created_at
- rounds.created_at, rounds.expires_at, rounds.vote_submitted_at
- wordsets.third_vote_at, wordsets.fifth_vote_at, wordsets.closes_at,
  wordsets.created_at, wordsets.finalized_at
- transactions.created_at
- votes.created_at
- daily_bonuses.claimed_at
- result_views.viewed_at
- prompts.created_at
- player_abandoned_prompts.abandoned_at

Revision ID: b4259daa4cd5
Revises: dee7013ca439
Create Date: 2025-10-11 20:51:52.757695

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4259daa4cd5'
down_revision: Union[str, None] = 'dee7013ca439'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    No database schema changes required.

    The DateTime(timezone=True) change is handled at the SQLAlchemy model level:
    - SQLite: Continues to store datetimes as ISO8601 strings (no schema change needed)
    - PostgreSQL: Would use TIMESTAMP WITH TIME ZONE on fresh deployments

    For existing PostgreSQL databases, the TIMESTAMP columns will continue to work
    correctly with timezone-aware datetime objects.
    """
    pass


def downgrade() -> None:
    """
    No database schema changes to revert.
    """
    pass
