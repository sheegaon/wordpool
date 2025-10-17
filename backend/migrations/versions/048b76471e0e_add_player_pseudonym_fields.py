"""add_player_pseudonym_fields

Revision ID: 048b76471e0e
Revises: 057f3d5c9698
Create Date: 2025-10-17 07:37:01.049847

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '048b76471e0e'
down_revision: Union[str, None] = '057f3d5c9698'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add pseudonym and pseudonym_canonical columns (non-nullable with default)
    # We set nullable=False directly because SQLite doesn't support ALTER COLUMN SET NOT NULL
    # For existing rows, we use server_default to populate them
    op.add_column('players', sa.Column('pseudonym', sa.String(length=80), nullable=False, server_default=''))
    op.add_column('players', sa.Column('pseudonym_canonical', sa.String(length=80), nullable=False, server_default=''))
    op.create_index('ix_players_pseudonym', 'players', ['pseudonym'], unique=False)

    # Populate pseudonyms for existing players using their username
    op.execute("""
        UPDATE players
        SET pseudonym = username,
            pseudonym_canonical = username_canonical
        WHERE pseudonym = '' OR pseudonym_canonical = ''
    """)


def downgrade() -> None:
    op.drop_index('ix_players_pseudonym', table_name='players')
    op.drop_column('players', 'pseudonym_canonical')
    op.drop_column('players', 'pseudonym')
