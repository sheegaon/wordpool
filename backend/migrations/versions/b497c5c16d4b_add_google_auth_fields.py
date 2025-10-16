"""add Google OAuth fields to players

Revision ID: b497c5c16d4b
Revises: dee7013ca439
Create Date: 2024-03-23 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b497c5c16d4b"
down_revision: Union[str, None] = "dee7013ca439"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("players", sa.Column("google_sub", sa.String(length=64), nullable=True))
    op.add_column("players", sa.Column("email", sa.String(length=255), nullable=True))
    op.create_index("ix_players_google_sub", "players", ["google_sub"], unique=False)
    op.create_unique_constraint("uq_players_google_sub", "players", ["google_sub"])
    op.create_unique_constraint("uq_players_email", "players", ["email"])


def downgrade() -> None:
    op.drop_constraint("uq_players_email", "players", type_="unique")
    op.drop_constraint("uq_players_google_sub", "players", type_="unique")
    op.drop_index("ix_players_google_sub", table_name="players")
    op.drop_column("players", "email")
    op.drop_column("players", "google_sub")
