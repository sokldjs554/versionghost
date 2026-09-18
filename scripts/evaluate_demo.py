from __future__ import annotations

import json
import statistics
import tempfile
import time
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from versionghost.engine.pipeline import VersionGhostPipeline
from versionghost.store import RunStore

REQUEST = (
    "Add a streak bonus for v2 mobile clients. v2 must receive base_coins, streak_bonus, "
    "and total_coins. Keep v1.4/v1.9 response compatibility, preserve idempotent retries, "
    "keep the three-claim daily limit as HTTP 409, and make a retry safe even if the client "
    "upgrades from v1 to v2 between attempts."
)
RUNS = 3


def main() -> None:
    project_root = PROJECT_ROOT
    rows: list[dict[str, object]] = []
    for i in range(RUNS):
        with tempfile.TemporaryDirectory(prefix="versionghost-eval-") as tmp:
            tmp_path = Path(tmp)
            store = RunStore(tmp_path / "runs.db")
            pipeline = VersionGhostPipeline(project_root, store)
            pipeline.runs_root = tmp_path / "runs"
            run_id = pipeline.start_run(REQUEST)
            started = time.perf_counter()
            packet = pipeline.execute(run_id)
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            rows.append(
                {
                    "run": i + 1,
                    "verdict": packet.verdict,
                    "attempts": len(packet.attempts),
                    "first_replay_passes": sum(
                        1 for cell in packet.attempts[0].replay if cell.status == "pass"
                    ),
                    "first_replay_total": len(packet.attempts[0].replay),
                    "final_replay_passes": sum(
                        1 for cell in packet.attempts[-1].replay if cell.status == "pass"
                    ),
                    "final_replay_total": len(packet.attempts[-1].replay),
                    "requirements_proven": sum(
                        1 for item in packet.requirement_evidence if item.status == "proven"
                    ),
                    "requirements_total": len(packet.requirement_evidence),
                    "pipeline_ms": elapsed_ms,
                }
            )

    times = [int(row["pipeline_ms"]) for row in rows]
    artifact = {
        "evaluation": "deterministic-demo-orchestration",
        "runs": rows,
        "summary": {
            "ready_runs": sum(row["verdict"] == "ready_with_evidence" for row in rows),
            "total_runs": RUNS,
            "first_attempt_replay_passes": rows[0]["first_replay_passes"],
            "first_attempt_replay_total": rows[0]["first_replay_total"],
            "final_replay_passes": rows[0]["final_replay_passes"],
            "final_replay_total": rows[0]["final_replay_total"],
            "requirements_proven": rows[0]["requirements_proven"],
            "requirements_total": rows[0]["requirements_total"],
            "median_pipeline_ms": int(statistics.median(times)),
            "min_pipeline_ms": min(times),
            "max_pipeline_ms": max(times),
        },
        "limitations": [
            "This evaluates deterministic orchestration/gates, not LLM coding quality.",
            "Client contracts and traffic are synthetic.",
            "Pipeline time is a local evaluation measurement, not production latency.",
        ],
    }
    output = project_root / "artifacts" / "evaluation.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(artifact["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
