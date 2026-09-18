from __future__ import annotations

import argparse
import json
from pathlib import Path

from versionghost.engine.pipeline import VersionGhostPipeline
from versionghost.store import RunStore

DEFAULT_REQUEST = (
    "Add a streak bonus for v2 mobile clients. v2 must receive base_coins, streak_bonus, "
    "and total_coins. Keep v1.4/v1.9 response compatibility, preserve idempotent retries, "
    "keep the three-claim daily limit as HTTP 409, and make cross-version retries safe."
)


def main() -> None:
    parser = argparse.ArgumentParser(prog="versionghost")
    parser.add_argument("command", choices=["demo"])
    parser.add_argument("--provider", default="deterministic-demo")
    parser.add_argument("--request", default=DEFAULT_REQUEST)
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    store = RunStore(root / ".versionghost" / "cli-runs.db")
    pipeline = VersionGhostPipeline(root, store)
    run_id = pipeline.start_run(args.request, provider_name=args.provider)
    packet = pipeline.execute(run_id)
    print(json.dumps(packet.model_dump(), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
