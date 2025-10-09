"""Tests for complete game flow."""
import pytest
import uuid
from backend.models.player import Player
from backend.models.prompt import Prompt
from backend.services.player_service import PlayerService
from backend.services.round_service import RoundService
from backend.services.transaction_service import TransactionService
from backend.services.vote_service import VoteService


@pytest.mark.asyncio
async def test_prompt_round_lifecycle(db_session):
    """Test prompt round from start to submission."""
    # Create player and services
    player_service = PlayerService(db_session)
    round_service = RoundService(db_session)
    transaction_service = TransactionService(db_session)

    player = await player_service.create_player()

    # Seed a test prompt with unique text
    prompt = Prompt(
        text=f"test prompt lifecycle {uuid.uuid4()}",
        category="test",
        enabled=True
    )
    db_session.add(prompt)
    await db_session.commit()

    # Start prompt round
    round = await round_service.start_prompt_round(player, transaction_service)

    assert round.round_type == "prompt"
    assert round.status == "active"
    assert round.cost == 100
    assert player.balance == 900  # $1000 - $100

    # Submit word
    round = await round_service.submit_prompt_word(
        round.round_id, "cat", player, transaction_service
    )

    assert round.status == "submitted"
    assert round.submitted_word == "cat"


@pytest.mark.asyncio
async def test_one_round_at_a_time_enforcement(db_session):
    """Test player can only have one active round."""
    player_service = PlayerService(db_session)
    round_service = RoundService(db_session)
    transaction_service = TransactionService(db_session)

    player = await player_service.create_player()

    # Seed prompt
    prompt = Prompt(text="test", category="test", enabled=True)
    db_session.add(prompt)
    await db_session.commit()

    # Start first round
    await round_service.start_prompt_round(player, transaction_service)

    # Try to start second round
    can_start, reason = await player_service.can_start_prompt_round(player)
    assert can_start is False
    assert reason == "already_in_round"


@pytest.mark.asyncio
async def test_insufficient_balance_prevention(db_session):
    """Test player cannot start round without sufficient balance."""
    player_service = PlayerService(db_session)
    player = await player_service.create_player()

    # Set balance to $50 (insufficient for $100 prompt)
    player.balance = 50
    await db_session.commit()

    can_start, reason = await player_service.can_start_prompt_round(player)
    assert can_start is False
    assert reason == "insufficient_balance"


@pytest.mark.asyncio
async def test_transaction_ledger_tracking(db_session):
    """Test all transactions are recorded with balance_after."""
    player_service = PlayerService(db_session)
    round_service = RoundService(db_session)
    transaction_service = TransactionService(db_session)

    player = await player_service.create_player()

    # Seed prompt with unique text
    prompt = Prompt(text=f"test ledger {uuid.uuid4()}", category="test", enabled=True)
    db_session.add(prompt)
    await db_session.commit()

    # Start round (should create transaction)
    await round_service.start_prompt_round(player, transaction_service)

    # Check transaction exists
    from sqlalchemy import select
    from backend.models.transaction import Transaction
    result = await db_session.execute(
        select(Transaction).where(Transaction.player_id == player.player_id)
    )
    transactions = result.scalars().all()

    assert len(transactions) == 1
    assert transactions[0].amount == -100
    assert transactions[0].type == "prompt_entry"
    assert transactions[0].balance_after == 900


@pytest.mark.asyncio
async def test_daily_bonus_logic(db_session):
    """Test daily bonus availability and claiming."""
    from datetime import date, timedelta, datetime, UTC

    player_service = PlayerService(db_session)
    transaction_service = TransactionService(db_session)

    player = await player_service.create_player()

    # Should not be available on creation day
    available = await player_service.is_daily_bonus_available(player)
    assert available is False

    # Simulate player created yesterday by modifying created_at and last_login_date
    player.created_at = datetime.now(UTC) - timedelta(days=1)
    player.last_login_date = date.today() - timedelta(days=1)
    await db_session.commit()
    await db_session.refresh(player)

    # Should now be available (created yesterday, last login yesterday, today is new day)
    available = await player_service.is_daily_bonus_available(player)
    assert available is True

    # Claim bonus
    amount = await player_service.claim_daily_bonus(player, transaction_service)
    assert amount == 100
    await db_session.refresh(player)
    assert player.balance == 1100

    # Should no longer be available today (last_login_date now set to today)
    available = await player_service.is_daily_bonus_available(player)
    assert available is False
