from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

BASE_URL = os.getenv("BASE_URL", "https://versionghost.onrender.com").rstrip("/")
EXPECTED_COMMIT = os.getenv("EXPECTED_COMMIT", "").strip()
TIMEOUT_SECONDS = int(os.getenv("SMOKE_TIMEOUT_SECONDS", "600"))

REQUEST_TEXT = (
    "Add a streak bonus for v2 mobile clients. v2 must receive base_coins, "
    "streak_bonus, and total_coins. Keep v1.4/v1.9 response compatibility, "
    "preserve idempotent retries, keep the three-claim daily limit as HTTP 409, "
    "and make a retry safe even if the client upgrades from v1 to v2 between attempts."
)


def request_json(path: str, method: str = "GET", payload: dict[str, object] | None = None) -> dict[str, object]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        BASE_URL + path,
        data=body,
        method=method,
        headers={"Content-Type": "application/json", "User-Agent": "versionghost-live-smoke/1"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_for_release(deadline: float) -> dict[str, object]:
    last: object = None
    while time.monotonic() < deadline:
        try:
            release = request_json("/api/release")
            last = release
            commit = str(release.get("commit", ""))
            if not EXPECTED_COMMIT or commit == EXPECTED_COMMIT:
                return release
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            last = repr(exc)
        time.sleep(5)
    raise RuntimeError("deployment did not reach expected commit %r; last=%r" % (EXPECTED_COMMIT, last))


def main() -> None:
    deadline = time.monotonic() + TIMEOUT_SECONDS
    release = wait_for_release(deadline)
    health = request_json("/api/health")
    assert health.get("status") == "ok", health

    created = request_json(
        "/api/runs",
        method="POST",
        payload={
            "request_text": REQUEST_TEXT,
            "provider": "deterministic-demo",
            "scenario": "streak-bonus-compatibility",
        },
    )
    run_id = str(created["id"])

    record: dict[str, object] | None = None
    while time.monotonic() < deadline:
        record = request_json("/api/runs/" + run_id)
        if record.get("stage") in {"complete", "failed"}:
            break
        time.sleep(2)

    if record is None or record.get("stage") != "complete":
        raise RuntimeError("live run did not complete: %r" % (record,))

    packet = record.get("packet")
    if not isinstance(packet, dict):
        raise RuntimeError("missing merge packet: %r" % (record,))

    attempts = packet.get("attempts")
    evidence = packet.get("requirement_evidence")
    assert packet.get("verdict") == "ready_with_evidence", packet
    assert isinstance(attempts, list) and len(attempts) == 2, attempts
    assert attempts[0].get("passed") is False, attempts[0]
    assert attempts[1].get("passed") is True, attempts[1]
    replay = attempts[1].get("replay")
    assert isinstance(replay, list) and len(replay) == 6, replay
    assert all(cell.get("status") == "pass" for cell in replay), replay
    assert isinstance(evidence, list) and len(evidence) == 5, evidence
    assert all(row.get("status") == "proven" for row in evidence), evidence

    print(json.dumps({
        "release": release,
        "run_id": run_id,
        "verdict": packet["verdict"],
        "attempts": len(attempts),
        "final_replay": "6/6",
        "requirements": "5/5",
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
