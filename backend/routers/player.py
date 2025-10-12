"""Player API router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.dependencies import get_current_player
from backend.models.player import Player
from backend.models.wordset import WordSet
from backend.models.round import Round
from backend.schemas.player import (
    PlayerBalance,
    ClaimDailyBonusResponse,
    CurrentRoundResponse,
    PendingResultsResponse,
    PendingResult,
    CreatePlayerResponse,
    RotateKeyResponse,
    UsernameLoginRequest,
    UsernameLoginResponse,
)
from backend.services.player_service import PlayerService
from backend.services.transaction_service import TransactionService
from backend.services.round_service import RoundService
from backend.utils.exceptions import DailyBonusNotAvailableError
from backend.config import get_settings
from datetime import datetime, UTC, timedelta
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


def ensure_utc(dt: datetime) -> datetime:
    """Ensure datetime has UTC timezone for proper JSON serialization."""
    if dt and dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


@router.post("", response_model=CreatePlayerResponse, status_code=201)
async def create_player(
    db: AsyncSession = Depends(get_db),
):
    """Create a new player account and return API key.

    This endpoint creates a new player with a starting balance and generates
    a unique API key for authentication. Save the API key - it cannot be retrieved later.
    """
    player_service = PlayerService(db)
    player = await player_service.create_player()

    return CreatePlayerResponse(
        player_id=player.player_id,
        username=player.username,
        api_key=player.api_key,
        balance=player.balance,
        message=(
            "Player created! Your username is "
            f'"{player.username}". The API key is required for API calls - '
            "keep it somewhere safe. Starting balance: "
            f"${player.balance}"
        ),
    )


@router.post("/rotate-key", response_model=RotateKeyResponse)
async def rotate_api_key(
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    """Rotate API key for security purposes.

    Generates a new API key and invalidates the old one. The old API key
    will immediately stop working. Use this if you suspect your key has been compromised.

    **Important:** You must start using the new key immediately - the old key in your
    current request will no longer work for future requests.
    """
    player_service = PlayerService(db)
    new_key = await player_service.rotate_api_key(player)

    return RotateKeyResponse(
        new_api_key=new_key,
        message="API key rotated successfully. Use the new key for all future requests. Your old key is now invalid."
    )


@router.get("/balance", response_model=PlayerBalance)
async def get_balance(
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    """Get player balance and status."""
    player_service = PlayerService(db)

    # Get daily bonus status
    bonus_available = await player_service.is_daily_bonus_available(player)

    # Get outstanding prompts count
    outstanding = await player_service.get_outstanding_prompts_count(player.player_id)

    return PlayerBalance(
        username=player.username,
        balance=player.balance,
        starting_balance=settings.starting_balance,
        daily_bonus_available=bonus_available,
        daily_bonus_amount=settings.daily_bonus_amount,
        last_login_date=player.last_login_date,
        outstanding_prompts=outstanding,
    )


@router.post("/login", response_model=UsernameLoginResponse)
async def login_with_username(
    request: UsernameLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve API key for an existing player via username."""
    player_service = PlayerService(db)
    player = await player_service.get_player_by_username(request.username)

    if not player:
        raise HTTPException(status_code=404, detail="username_not_found")

    return UsernameLoginResponse(
        player_id=player.player_id,
        username=player.username,
        api_key=player.api_key,
        message="Welcome back! We've restored your API key for this username.",
    )


@router.post("/claim-daily-bonus", response_model=ClaimDailyBonusResponse)
async def claim_daily_bonus(
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    """Claim daily login bonus."""
    player_service = PlayerService(db)
    transaction_service = TransactionService(db)

    try:
        amount = await player_service.claim_daily_bonus(player, transaction_service)

        # Refresh player to get updated balance
        await db.refresh(player)

        return ClaimDailyBonusResponse(
            success=True,
            amount=amount,
            new_balance=player.balance,
        )
    except DailyBonusNotAvailableError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/current-round", response_model=CurrentRoundResponse)
async def get_current_round(
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    """Get player's current active round if any."""
    if not player.active_round_id:
        return CurrentRoundResponse(
            round_id=None,
            round_type=None,
            state=None,
            expires_at=None,
        )

    # Get round details
    round = await db.get(Round, player.active_round_id)
    if not round:
        return CurrentRoundResponse(
            round_id=None,
            round_type=None,
            state=None,
            expires_at=None,
        )

    # If round already resolved, clear pointer and return empty response
    if round.status != "active":
        if player.active_round_id == round.round_id:
            player.active_round_id = None
            await db.commit()
            await db.refresh(player)
        return CurrentRoundResponse(
            round_id=None,
            round_type=None,
            state=None,
            expires_at=None,
        )

    expires_at_utc = ensure_utc(round.expires_at)
    grace_cutoff = expires_at_utc + timedelta(seconds=settings.grace_period_seconds)

    if datetime.now(UTC) > grace_cutoff:
        round_service = RoundService(db)
        transaction_service = TransactionService(db)
        await round_service.handle_timeout(round.round_id, transaction_service)
        await db.refresh(player)
        return CurrentRoundResponse(
            round_id=None,
            round_type=None,
            state=None,
            expires_at=None,
        )

    # Build state based on round type
    state = {
        "round_id": str(round.round_id),
        "status": round.status,
        "expires_at": expires_at_utc.isoformat(),
        "cost": round.cost,
    }

    if round.round_type == "prompt":
        state.update({
            "prompt_text": round.prompt_text,
        })
    elif round.round_type == "copy":
        state.update({
            "original_word": round.original_word,
            "prompt_round_id": str(round.prompt_round_id),
        })
    elif round.round_type == "vote":
        # Get wordset for voting
        wordset = await db.get(WordSet, round.wordset_id)
        if wordset:
            # Randomize word order per-voter
            import random
            words = [wordset.original_word, wordset.copy_word_1, wordset.copy_word_2]
            random.shuffle(words)
            state.update({
                "wordset_id": str(wordset.wordset_id),
                "prompt_text": wordset.prompt_text,
                "words": words,
            })

    return CurrentRoundResponse(
        round_id=round.round_id,
        round_type=round.round_type,
        state=state,
        expires_at=expires_at_utc,
    )


@router.get("/pending-results", response_model=PendingResultsResponse)
async def get_pending_results(
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    """Get list of finalized wordsets where player was contributor."""
    # Find wordsets where player was prompt contributor
    prompt_wordsets = await db.execute(
        select(WordSet)
        .join(Round, WordSet.prompt_round_id == Round.round_id)
        .where(Round.player_id == player.player_id)
        .where(WordSet.status == "finalized")
    )

    # Find wordsets where player was copy contributor
    copy_wordsets = await db.execute(
        select(WordSet)
        .where(
            (WordSet.copy_round_1_id.in_(
                select(Round.round_id).where(Round.player_id == player.player_id)
            )) |
            (WordSet.copy_round_2_id.in_(
                select(Round.round_id).where(Round.player_id == player.player_id)
            ))
        )
        .where(WordSet.status == "finalized")
    )

    all_wordsets = set(prompt_wordsets.scalars().all()) | set(copy_wordsets.scalars().all())

    # Build response
    pending = []
    for ws in all_wordsets:
        # Get role
        prompt_round = await db.get(Round, ws.prompt_round_id)
        role = "prompt" if prompt_round.player_id == player.player_id else "copy"

        # Check if already collected
        from backend.models.result_view import ResultView
        result_view_query = await db.execute(
            select(ResultView)
            .where(ResultView.wordset_id == ws.wordset_id)
            .where(ResultView.player_id == player.player_id)
        )
        result_view = result_view_query.scalar_one_or_none()

        pending.append(
            PendingResult(
                wordset_id=ws.wordset_id,
                prompt_text=ws.prompt_text,
                completed_at=ensure_utc(ws.finalized_at),
                role=role,
                payout_collected=result_view.payout_collected if result_view else False,
            )
        )

    # Sort by completion time (newest first)
    pending.sort(key=lambda x: x.completed_at, reverse=True)

    return PendingResultsResponse(pending=pending)
