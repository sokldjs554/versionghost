from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_repository_legal_and_demo_contract() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "MIT" not in readme
    assert not any(ROOT.glob("LICENSE*"))
    assert "Copyright © 2026 윤기혁. All rights reserved. Portfolio project." in readme


def test_historical_client_contracts_are_present() -> None:
    contract_dir = ROOT / "sample_app" / "liveops_service" / "client_contracts"
    expected = {
        "v1_4.json",
        "v1_9.json",
        "v2_0.json",
        "v2_duplicate.json",
        "v2_limit.json",
        "v_cross_version_retry.json",
    }
    assert {path.name for path in contract_dir.glob("*.json")} == expected
