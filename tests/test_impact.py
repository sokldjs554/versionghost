from pathlib import Path

from versionghost.engine.impact import analyze_repo


def test_impact_map_finds_reward_service() -> None:
    root = Path(__file__).resolve().parents[1]
    report = analyze_repo(root, "change reward claim response by client version")
    assert any(path.endswith("sample_app/liveops_service/service.py") for path in report.touched_candidates)
    assert any(node.symbol == "claim_reward" for node in report.nodes)
