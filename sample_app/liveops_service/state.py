from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RewardState:
    claim_count_by_player: dict[str, int] = field(default_factory=dict)
    idempotency: dict[str, dict[str, object]] = field(default_factory=dict)

    def reset(self) -> None:
        self.claim_count_by_player.clear()
        self.idempotency.clear()


STATE = RewardState()
