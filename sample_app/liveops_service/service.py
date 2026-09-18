from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from .state import STATE


DAILY_LIMIT = 3
BASE_COINS = 100


@dataclass(frozen=True)
class ClaimRequest:
    player_id: str
    event_id: str
    idempotency_key: str
    streak_days: int = 0


def claim_reward(request: ClaimRequest) -> tuple[int, dict[str, object]]:
    """Baseline behavior: v1 response only, idempotent, three claims per player/day."""
    if request.idempotency_key in STATE.idempotency:
        return 200, dict(STATE.idempotency[request.idempotency_key])

    count = STATE.claim_count_by_player.get(request.player_id, 0)
    if count >= DAILY_LIMIT:
        return 409, {"error": "daily_limit_reached"}

    payload: dict[str, object] = {
        "claim_id": str(uuid4()),
        "coins": BASE_COINS,
    }
    STATE.claim_count_by_player[request.player_id] = count + 1
    STATE.idempotency[request.idempotency_key] = dict(payload)
    return 200, payload
