from __future__ import annotations

import importlib
import json
import sys
import time
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from versionghost.models import CheckResult, ReplayCell


def run_client_replays(repo_root: Path) -> tuple[list[ReplayCell], CheckResult]:
    started = time.perf_counter()
    cells: list[ReplayCell] = []
    contracts_dir = repo_root / "sample_app" / "liveops_service" / "client_contracts"
    fixtures = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(contracts_dir.glob("*.json"))]

    _purge_target_modules()
    sys.path.insert(0, str(repo_root))
    try:
        api = importlib.import_module("sample_app.liveops_service.api")
        state_module = importlib.import_module("sample_app.liveops_service.state")
        client = TestClient(api.app)

        for fixture in fixtures:
            state_module.STATE.reset()
            kind = fixture.get("kind", "standard")
            if kind == "standard":
                cells.append(_standard(client, fixture))
            elif kind == "duplicate_idempotency":
                cells.append(_duplicate(client, state_module.STATE, fixture))
            elif kind == "daily_limit":
                cells.append(_daily_limit(client, fixture))
            elif kind == "cross_version_retry":
                cells.append(_cross_version_retry(client, state_module.STATE, fixture))
            else:
                cells.append(
                    ReplayCell(
                        client_version=str(fixture.get("client_version", "unknown")),
                        case_id=fixture.get("description", kind),
                        status="fail",
                        detail=f"Unknown fixture kind: {kind}",
                    )
                )
    finally:
        sys.path.pop(0)
        _purge_target_modules()

    failed = [cell for cell in cells if cell.status == "fail"]
    duration = int((time.perf_counter() - started) * 1000)
    check = CheckResult(
        name="historical-client-replay",
        status="fail" if failed else "pass",
        detail=(
            f"{len(cells) - len(failed)}/{len(cells)} compatibility probes passed."
            if cells
            else "No client contracts found."
        ),
        duration_ms=duration,
    )
    return cells, check


def _standard(client: TestClient, fixture: dict[str, Any]) -> ReplayCell:
    response = client.post(
        "/v1/rewards/claim",
        headers={"X-Client-Version": fixture["client_version"]},
        json=fixture["request"],
    )
    payload = response.json()
    errors: list[str] = []
    if response.status_code != fixture["expected_status"]:
        errors.append(f"status {response.status_code} != {fixture['expected_status']}")
    for key in fixture.get("required_keys", []):
        if key not in payload:
            errors.append(f"missing key {key}")
    for key in fixture.get("forbidden_keys", []):
        if key in payload:
            errors.append(f"unexpected key {key}")
    for key, value in fixture.get("exact_values", {}).items():
        if payload.get(key) != value:
            errors.append(f"{key}={payload.get(key)!r} != {value!r}")
    return ReplayCell(
        client_version=fixture["client_version"],
        case_id=_case_id(fixture),
        status="fail" if errors else "pass",
        detail="; ".join(errors) if errors else "Response contract matched.",
    )


def _duplicate(client: TestClient, state: Any, fixture: dict[str, Any]) -> ReplayCell:
    headers = {"X-Client-Version": fixture["client_version"]}
    first = client.post("/v1/rewards/claim", headers=headers, json=fixture["request"])
    second = client.post("/v1/rewards/claim", headers=headers, json=fixture["request"])
    errors: list[str] = []
    if first.status_code != fixture["expected_status"] or second.status_code != fixture["expected_status"]:
        errors.append(f"retry statuses were {first.status_code}/{second.status_code}")
    if first.json() != second.json():
        errors.append("retry payload changed")
    actual_count = state.claim_count_by_player.get(fixture["request"]["player_id"], 0)
    if actual_count != fixture["expected_claim_count"]:
        errors.append(f"claim_count={actual_count} != {fixture['expected_claim_count']}")
    return ReplayCell(
        client_version=fixture["client_version"],
        case_id=_case_id(fixture),
        status="fail" if errors else "pass",
        detail="; ".join(errors) if errors else "Idempotent retry preserved one claim slot.",
    )


def _daily_limit(client: TestClient, fixture: dict[str, Any]) -> ReplayCell:
    headers = {"X-Client-Version": fixture["client_version"]}
    base = dict(fixture["request"])
    last = None
    for i in range(4):
        req = dict(base)
        req["idempotency_key"] = f"{base['idempotency_key']}-{i}"
        last = client.post("/v1/rewards/claim", headers=headers, json=req)
    assert last is not None
    payload = last.json()
    errors: list[str] = []
    if last.status_code != fixture["expected_status"]:
        errors.append(f"status {last.status_code} != {fixture['expected_status']}")
    if payload.get("error") != fixture["expected_error"]:
        errors.append(f"error={payload.get('error')!r} != {fixture['expected_error']!r}")
    return ReplayCell(
        client_version=fixture["client_version"],
        case_id=_case_id(fixture),
        status="fail" if errors else "pass",
        detail="; ".join(errors) if errors else "Daily-limit boundary remained a 409 domain conflict.",
    )


def _cross_version_retry(client: TestClient, state: Any, fixture: dict[str, Any]) -> ReplayCell:
    first = client.post(
        "/v1/rewards/claim",
        headers={"X-Client-Version": fixture["first_version"]},
        json=fixture["request"],
    )
    second = client.post(
        "/v1/rewards/claim",
        headers={"X-Client-Version": fixture["second_version"]},
        json=fixture["request"],
    )
    errors: list[str] = []
    first_payload, second_payload = first.json(), second.json()
    if first.status_code != 200 or second.status_code != 200:
        errors.append(f"statuses were {first.status_code}/{second.status_code}")
    if not set(fixture["expected_first_keys"]).issubset(first_payload):
        errors.append("first response did not match v1 key set")
    if not set(fixture["expected_second_keys"]).issubset(second_payload):
        errors.append("second response did not match v2 key set")
    if second_payload.get("total_coins") != fixture["expected_total"]:
        errors.append(f"total_coins={second_payload.get('total_coins')!r}")
    if first_payload.get("claim_id") != second_payload.get("claim_id"):
        errors.append("canonical claim identity changed across retry")
    actual_count = state.claim_count_by_player.get(fixture["request"]["player_id"], 0)
    if actual_count != fixture["expected_claim_count"]:
        errors.append(f"claim_count={actual_count} != {fixture['expected_claim_count']}")
    return ReplayCell(
        client_version=fixture["client_version"],
        case_id=_case_id(fixture),
        status="fail" if errors else "pass",
        detail=(
            "; ".join(errors)
            if errors
            else "One canonical reward re-rendered correctly after the client-version change."
        ),
    )


def _purge_target_modules() -> None:
    for name in list(sys.modules):
        if name == "sample_app" or name.startswith("sample_app."):
            sys.modules.pop(name, None)


def _case_id(fixture: dict[str, Any]) -> str:
    return fixture.get("description", fixture.get("kind", "replay"))
