"""add jwt authentication tables"""
from collections.abc import Sequence
from typing import Any

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision: str = "0c0b2fd2a6c3"
down_revision: str | None = "f5bb6c8b42df"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _uuid_column() -> sa.types.TypeEngine[Any]:
    """Utility to create UUID column compatible with SQLite and Postgres."""
    bind = op.get_bind()
    dialect_name = bind.dialect.name if bind else "postgresql"
    if dialect_name == "postgresql":
        return sa.UUID()
    return sa.String(length=36)


def upgrade() -> None:
    with op.batch_alter_table("players") as batch_op:
        batch_op.add_column(sa.Column("email", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("password_hash", sa.String(length=255), nullable=True))

    conn = op.get_bind()
    result = conn.execute(text("SELECT player_id, username FROM players WHERE email IS NULL"))
    rows = result.fetchall()
    for player_id, username in rows:
        placeholder_email = f"{username.lower()}@migration.local"
        conn.execute(
            text("UPDATE players SET email = :email WHERE player_id = :player_id"),
            {"email": placeholder_email, "player_id": str(player_id)},
        )
    conn.execute(
        text("UPDATE players SET password_hash = 'legacy-placeholder' WHERE password_hash IS NULL")
    )

    with op.batch_alter_table("players") as batch_op:
        batch_op.alter_column("email", existing_type=sa.String(length=255), nullable=False)
        batch_op.alter_column("password_hash", existing_type=sa.String(length=255), nullable=False)
        batch_op.create_unique_constraint("uq_players_email", ["email"])

    uuid_type = _uuid_column()
    op.create_table(
        "refresh_tokens",
        sa.Column("token_id", uuid_type, nullable=False),
        sa.Column("player_id", uuid_type, nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["player_id"], ["players.player_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("token_id"),
    )
    op.create_index("ix_refresh_tokens_player_id", "refresh_tokens", ["player_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_player_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    with op.batch_alter_table("players") as batch_op:
        batch_op.drop_constraint("uq_players_email", type_="unique")
        batch_op.drop_column("password_hash")
        batch_op.drop_column("email")
