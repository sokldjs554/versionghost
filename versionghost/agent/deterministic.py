from __future__ import annotations

from pathlib import Path

from versionghost.models import (
    ChangeContract,
    ImpactReport,
    PatchOperation,
    PatchSet,
    Requirement,
)


class DeterministicDemoProvider:
    """Reproducible provider for the built-in compatibility scenario.

    It intentionally produces a plausible first patch with a compatibility bug so the
    verification/repair loop can be demonstrated without an external API key. It is not
    presented as a model-quality benchmark.
    """

    name = "deterministic-demo"

    def build_contract(self, request_text: str, impact: ImpactReport) -> ChangeContract:
        del impact
        return ChangeContract(
            title="Versioned streak bonus without breaking v1 clients",
            intent=request_text,
            protected_clients=["1.4", "1.9", "2.0"],
            assumptions=[
                "Client major version is supplied by X-Client-Version.",
                "All demo traffic and player identifiers are synthetic.",
                "The daily limit remains three unique successful claims per player.",
            ],
            requirements=[
                Requirement(
                    id="REQ-1",
                    text="v2 clients receive base_coins, streak_bonus, and total_coins.",
                    kind="behavior",
                    verification="Replay v2.0 historical contract fixture.",
                ),
                Requirement(
                    id="REQ-2",
                    text="v1.4 and v1.9 clients keep the exact legacy coins response contract.",
                    kind="compatibility",
                    verification="Replay v1.4 and v1.9 fixtures and reject new v2-only fields.",
                ),
                Requirement(
                    id="REQ-3",
                    text="Retries with the same idempotency key never consume another daily claim slot.",
                    kind="invariant",
                    verification="Replay duplicate-idempotency probe and inspect stored claim count.",
                ),
                Requirement(
                    id="REQ-4",
                    text="The fourth unique claim stays a 409 daily_limit_reached domain conflict.",
                    kind="error_contract",
                    verification="Replay daily-limit boundary probe.",
                ),
                Requirement(
                    id="REQ-5",
                    text="A retry crossing from a v1 client to a v2 client renders the same canonical reward in the new response shape.",
                    kind="compatibility",
                    verification="Replay cross-version retry probe with one idempotency key.",
                ),
            ],
        )

    def propose_patch(
        self, request_text: str, contract: ChangeContract, repo_root: Path, impact: ImpactReport
    ) -> PatchSet:
        del request_text, contract, repo_root, impact
        service_find = '''def claim_reward(request: ClaimRequest) -> tuple[int, dict[str, object]]:\n    """Baseline behavior: v1 response only, idempotent, three claims per player/day."""\n    if request.idempotency_key in STATE.idempotency:\n        return 200, dict(STATE.idempotency[request.idempotency_key])\n\n    count = STATE.claim_count_by_player.get(request.player_id, 0)\n    if count >= DAILY_LIMIT:\n        return 409, {"error": "daily_limit_reached"}\n\n    payload: dict[str, object] = {\n        "claim_id": str(uuid4()),\n        "coins": BASE_COINS,\n    }\n    STATE.claim_count_by_player[request.player_id] = count + 1\n    STATE.idempotency[request.idempotency_key] = dict(payload)\n    return 200, payload\n'''
        service_replace = '''def claim_reward(\n    request: ClaimRequest, client_version: str = "1.9"\n) -> tuple[int, dict[str, object]]:\n    """First implementation attempt: add a v2 reward breakdown."""\n    if request.idempotency_key in STATE.idempotency:\n        return 200, dict(STATE.idempotency[request.idempotency_key])\n\n    count = STATE.claim_count_by_player.get(request.player_id, 0)\n    if count >= DAILY_LIMIT:\n        return 409, {"error": "daily_limit_reached"}\n\n    streak_bonus = min(request.streak_days, 7) * 5\n    payload: dict[str, object] = {\n        "claim_id": str(uuid4()),\n        "base_coins": BASE_COINS,\n        "streak_bonus": streak_bonus,\n        "total_coins": BASE_COINS + streak_bonus,\n    }\n    STATE.claim_count_by_player[request.player_id] = count + 1\n    STATE.idempotency[request.idempotency_key] = dict(payload)\n    return 200, payload\n'''
        api_find = '''    status, payload = claim_reward(\n        ClaimRequest(\n            player_id=body.player_id,\n            event_id=body.event_id,\n            idempotency_key=body.idempotency_key,\n            streak_days=body.streak_days,\n        )\n    )\n'''
        api_replace = '''    status, payload = claim_reward(\n        ClaimRequest(\n            player_id=body.player_id,\n            event_id=body.event_id,\n            idempotency_key=body.idempotency_key,\n            streak_days=body.streak_days,\n        ),\n        client_version=x_client_version,\n    )\n'''
        return PatchSet(
            summary="Add a version parameter and streak-bonus response shape.",
            operations=[
                PatchOperation(
                    path="sample_app/liveops_service/service.py",
                    find=service_find,
                    replace=service_replace,
                    rationale="Implement the requested v2 breakdown and preserve existing limit/idempotency flow.",
                ),
                PatchOperation(
                    path="sample_app/liveops_service/api.py",
                    find=api_find,
                    replace=api_replace,
                    rationale="Pass the client version header into the service layer.",
                ),
            ],
        )

    def repair_patch(
        self,
        request_text: str,
        contract: ChangeContract,
        repo_root: Path,
        failure_summary: str,
        impact: ImpactReport,
    ) -> PatchSet:
        del request_text, contract, repo_root, failure_summary, impact
        candidate_find = '''def claim_reward(\n    request: ClaimRequest, client_version: str = "1.9"\n) -> tuple[int, dict[str, object]]:\n    """First implementation attempt: add a v2 reward breakdown."""\n    if request.idempotency_key in STATE.idempotency:\n        return 200, dict(STATE.idempotency[request.idempotency_key])\n\n    count = STATE.claim_count_by_player.get(request.player_id, 0)\n    if count >= DAILY_LIMIT:\n        return 409, {"error": "daily_limit_reached"}\n\n    streak_bonus = min(request.streak_days, 7) * 5\n    payload: dict[str, object] = {\n        "claim_id": str(uuid4()),\n        "base_coins": BASE_COINS,\n        "streak_bonus": streak_bonus,\n        "total_coins": BASE_COINS + streak_bonus,\n    }\n    STATE.claim_count_by_player[request.player_id] = count + 1\n    STATE.idempotency[request.idempotency_key] = dict(payload)\n    return 200, payload\n'''
        repaired = '''def _render_reward(record: dict[str, object], client_version: str) -> dict[str, object]:\n    if client_version.startswith("2."):\n        return {\n            "claim_id": record["claim_id"],\n            "base_coins": record["base_coins"],\n            "streak_bonus": record["streak_bonus"],\n            "total_coins": record["total_coins"],\n        }\n    return {"claim_id": record["claim_id"], "coins": record["base_coins"]}\n\n\ndef claim_reward(\n    request: ClaimRequest, client_version: str = "1.9"\n) -> tuple[int, dict[str, object]]:\n    """Store one canonical reward record; render it for each client contract."""\n    if request.idempotency_key in STATE.idempotency:\n        return 200, _render_reward(STATE.idempotency[request.idempotency_key], client_version)\n\n    count = STATE.claim_count_by_player.get(request.player_id, 0)\n    if count >= DAILY_LIMIT:\n        return 409, {"error": "daily_limit_reached"}\n\n    streak_bonus = min(request.streak_days, 7) * 5\n    record: dict[str, object] = {\n        "claim_id": str(uuid4()),\n        "base_coins": BASE_COINS,\n        "streak_bonus": streak_bonus,\n        "total_coins": BASE_COINS + streak_bonus,\n    }\n    STATE.claim_count_by_player[request.player_id] = count + 1\n    STATE.idempotency[request.idempotency_key] = dict(record)\n    return 200, _render_reward(record, client_version)\n'''
        return PatchSet(
            summary="Separate canonical reward state from version-specific response rendering.",
            operations=[
                PatchOperation(
                    path="sample_app/liveops_service/service.py",
                    find=candidate_find,
                    replace=repaired,
                    rationale=(
                        "Historical replays showed that caching a rendered v2 payload breaks v1 and "
                        "cross-version retries; cache canonical state and render at the boundary instead."
                    ),
                )
            ],
        )
