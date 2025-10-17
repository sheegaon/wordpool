"""Add AI metrics table for tracking usage and performance

Revision ID: 057f3d5c9698
Revises: 0c0b2fd2a6c3
Create Date: 2025-10-17 01:33:40.218183

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '057f3d5c9698'
down_revision: Union[str, None] = '0c0b2fd2a6c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ai_metrics',
        sa.Column('metric_id', sa.String(36), nullable=False),
        sa.Column('operation_type', sa.String(50), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.String(500), nullable=True),
        sa.Column('estimated_cost_usd', sa.Float(), nullable=True),
        sa.Column('prompt_length', sa.Integer(), nullable=True),
        sa.Column('response_length', sa.Integer(), nullable=True),
        sa.Column('validation_passed', sa.Boolean(), nullable=True),
        sa.Column('vote_correct', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('metric_id')
    )
    op.create_index('ix_ai_metrics_operation_type', 'ai_metrics', ['operation_type'])
    op.create_index('ix_ai_metrics_provider', 'ai_metrics', ['provider'])
    op.create_index('ix_ai_metrics_success', 'ai_metrics', ['success'])
    op.create_index('ix_ai_metrics_created_at', 'ai_metrics', ['created_at'])
    op.create_index('ix_ai_metrics_created_at_success', 'ai_metrics', ['created_at', 'success'])
    op.create_index('ix_ai_metrics_operation_provider', 'ai_metrics', ['operation_type', 'provider'])


def downgrade() -> None:
    op.drop_index('ix_ai_metrics_operation_provider', 'ai_metrics')
    op.drop_index('ix_ai_metrics_created_at_success', 'ai_metrics')
    op.drop_index('ix_ai_metrics_created_at', 'ai_metrics')
    op.drop_index('ix_ai_metrics_success', 'ai_metrics')
    op.drop_index('ix_ai_metrics_provider', 'ai_metrics')
    op.drop_index('ix_ai_metrics_operation_type', 'ai_metrics')
    op.drop_table('ai_metrics')
