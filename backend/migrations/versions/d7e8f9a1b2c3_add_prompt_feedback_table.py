"""add_prompt_feedback_table

Revision ID: d7e8f9a1b2c3
Revises: c600ac93b635
Create Date: 2025-10-12 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd7e8f9a1b2c3'
down_revision: Union[str, None] = 'c600ac93b635'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add prompt_feedback table."""
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    if dialect_name == "postgresql":
        uuid = sa.UUID()
    else:
        uuid = sa.String(length=36)

    # Create prompt_feedback table
    op.create_table('prompt_feedback',
        sa.Column('feedback_id', uuid, nullable=False),
        sa.Column('player_id', uuid, nullable=False),
        sa.Column('prompt_id', uuid, nullable=False),
        sa.Column('round_id', uuid, nullable=False),
        sa.Column('feedback_type', sa.String(length=10), nullable=False),
        sa.Column(
            'last_updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(['player_id'], ['players.player_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.prompt_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['round_id'], ['rounds.round_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('feedback_id'),
        sa.UniqueConstraint('player_id', 'round_id', name='uq_prompt_feedback_player_round')
    )

    # Create indexes
    op.create_index('ix_prompt_feedback_player_id', 'prompt_feedback', ['player_id'], unique=False)
    op.create_index('ix_prompt_feedback_prompt_id', 'prompt_feedback', ['prompt_id'], unique=False)
    op.create_index('ix_prompt_feedback_round_id', 'prompt_feedback', ['round_id'], unique=False)


def downgrade() -> None:
    """Remove prompt_feedback table."""
    op.drop_index('ix_prompt_feedback_round_id', table_name='prompt_feedback')
    op.drop_index('ix_prompt_feedback_prompt_id', table_name='prompt_feedback')
    op.drop_index('ix_prompt_feedback_player_id', table_name='prompt_feedback')
    op.drop_table('prompt_feedback')
