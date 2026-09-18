from pathlib import Path

from versionghost.engine.pipeline import VersionGhostPipeline
from versionghost.store import RunStore


REQUEST = (
    "Add a streak bonus for v2 mobile clients while preserving v1.4/v1.9 response compatibility, "
    "idempotent retries, the three-claim daily limit, and cross-version retries."
)


def test_demo_pipeline_rejects_first_patch_then_repairs(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    store = RunStore(tmp_path / "runs.db")
    pipeline = VersionGhostPipeline(project_root, store)
    pipeline.runs_root = tmp_path / "runs"
    run_id = pipeline.start_run(REQUEST)
    packet = pipeline.execute(run_id)

    assert packet.verdict == "ready_with_evidence"
    assert len(packet.attempts) == 2
    assert packet.attempts[0].passed is False
    assert packet.attempts[1].passed is True
    assert any(cell.status == "fail" for cell in packet.attempts[0].replay)
    assert all(cell.status == "pass" for cell in packet.attempts[1].replay)
    assert all(row.status == "proven" for row in packet.requirement_evidence)
