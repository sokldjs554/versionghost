from __future__ import annotations

import json
import shutil
import time
import uuid
from pathlib import Path
from typing import Literal

from versionghost.agent.factory import build_provider
from versionghost.engine.checks import run_compile_check, run_python_tests
from versionghost.engine.evidence import build_requirement_evidence
from versionghost.engine.impact import analyze_repo
from versionghost.engine.patching import apply_patch_set
from versionghost.engine.replay import run_client_replays
from versionghost.engine.workspace import create_workspace
from versionghost.models import AttemptResult, MergePacket, RunStage
from versionghost.store import RunStore


class VersionGhostPipeline:
    def __init__(self, project_root: Path, store: RunStore) -> None:
        self.project_root = project_root
        self.store = store
        self.runs_root = project_root / ".versionghost" / "runs"
        self.runs_root.mkdir(parents=True, exist_ok=True)

    def start_run(
        self,
        request_text: str,
        *,
        provider_name: str = "deterministic-demo",
        scenario: str = "streak-bonus-compatibility",
    ) -> str:
        run_id = uuid.uuid4().hex[:12]
        self.store.create(run_id, request_text, scenario, provider_name)
        return run_id

    def execute(self, run_id: str) -> MergePacket:
        record = self.store.get(run_id)
        provider = build_provider(record.provider)
        run_root = self.runs_root / run_id
        started = time.perf_counter()
        try:
            self._event(run_id, RunStage.ANALYZING, "Building code/contract impact map")
            workspace = create_workspace(self.project_root, run_root)
            impact = analyze_repo(workspace, record.request_text)
            self._write_json(run_root / "impact.json", impact.model_dump())

            self._event(run_id, RunStage.CONTRACTING, "Compiling the change request into verifiable requirements")
            contract = provider.build_contract(record.request_text, impact)
            self._write_json(run_root / "change-contract.json", contract.model_dump())

            self._event(run_id, RunStage.PATCHING, "Generating a constrained first patch")
            patch = provider.propose_patch(record.request_text, contract, workspace, impact)
            changed_files = apply_patch_set(workspace, patch)
            self._write_json(run_root / "attempt-1-patch.json", patch.model_dump())

            self._event(run_id, RunStage.VERIFYING, "Running unit checks and historical-client replay matrix")
            attempt1 = self._verify_attempt(workspace, 1, patch.summary, changed_files)
            attempts = [attempt1]

            if not attempt1.passed:
                failure_summary = self._failure_summary(attempt1)
                self._event(
                    run_id,
                    RunStage.REPAIRING,
                    "Compatibility evidence rejected the first patch; generating a bounded repair",
                    extra={"failure_summary": failure_summary},
                )
                repair = provider.repair_patch(
                    record.request_text, contract, workspace, failure_summary, impact
                )
                repaired_files = apply_patch_set(workspace, repair)
                changed_files = sorted(set(changed_files + repaired_files))
                self._write_json(run_root / "attempt-2-repair.json", repair.model_dump())

                self._event(run_id, RunStage.VERIFYING, "Re-running the same verification surface after repair")
                attempt2 = self._verify_attempt(workspace, 2, repair.summary, repaired_files)
                attempts.append(attempt2)

            evidence = build_requirement_evidence(contract, attempts)
            final_passed = bool(attempts and attempts[-1].passed)
            all_requirements_proven = all(item.status == "proven" for item in evidence)
            verdict: Literal["ready_with_evidence", "blocked"] = (
                "ready_with_evidence" if final_passed and all_requirements_proven else "blocked"
            )
            elapsed_ms = int((time.perf_counter() - started) * 1000)

            packet = MergePacket(
                run_id=run_id,
                verdict=verdict,
                contract=contract,
                impact=impact,
                attempts=attempts,
                requirement_evidence=evidence,
                changed_files=changed_files,
                limitations=[
                    "The default provider is deterministic and exists to reproduce the orchestration path; it is not an LLM quality benchmark.",
                    "Historical clients are synthetic contract fixtures, not production traffic captures.",
                    "Only Python AST impact analysis is implemented in v0.1; dynamic/reflection edges may be missed.",
                    "The model may propose text replacements only; it cannot execute arbitrary shell commands or edit verification fixtures.",
                ],
                model_route=provider.name,
                metrics={
                    "pipeline_ms": elapsed_ms,
                    "attempt_count": len(attempts),
                    "impact_nodes": len(impact.nodes),
                    "impact_edges": len(impact.edges),
                    "replay_probes": len(attempts[-1].replay) if attempts else 0,
                    "final_replay_passes": sum(
                        1 for cell in (attempts[-1].replay if attempts else []) if cell.status == "pass"
                    ),
                },
            )
            self._write_json(run_root / "merge-packet.json", packet.model_dump())
            final_workspace = run_root / "final-workspace"
            if final_workspace.exists():
                shutil.rmtree(final_workspace)
            shutil.copytree(workspace, final_workspace)
            self.store.update(
                run_id,
                stage=RunStage.COMPLETE,
                status_message="Ready with evidence" if verdict == "ready_with_evidence" else "Blocked",
                packet=packet,
                event={"stage": "complete", "message": f"Verdict: {verdict}"},
            )
            return packet
        except Exception as exc:
            self.store.update(
                run_id,
                stage=RunStage.FAILED,
                status_message=f"Failed: {exc}",
                event={"stage": "failed", "message": str(exc)},
            )
            raise

    def _verify_attempt(
        self, workspace: Path, attempt: int, summary: str, changed_files: list[str]
    ) -> AttemptResult:
        compile_check = run_compile_check(workspace)
        unit_check = run_python_tests(workspace)
        replay, replay_check = run_client_replays(workspace)
        checks = [compile_check, unit_check, replay_check]
        return AttemptResult(
            attempt=attempt,
            patch_summary=summary,
            changed_files=changed_files,
            checks=checks,
            replay=replay,
            passed=all(check.status == "pass" for check in checks)
            and all(cell.status == "pass" for cell in replay),
        )

    def _event(
        self,
        run_id: str,
        stage: RunStage,
        message: str,
        *,
        extra: dict[str, object] | None = None,
    ) -> None:
        event: dict[str, object] = {"stage": stage.value, "message": message}
        if extra:
            event.update(extra)
        self.store.update(run_id, stage=stage, status_message=message, event=event)

    @staticmethod
    def _failure_summary(attempt: AttemptResult) -> str:
        parts = [check.detail for check in attempt.checks if check.status == "fail"]
        parts.extend(f"{cell.client_version}: {cell.detail}" for cell in attempt.replay if cell.status == "fail")
        return " | ".join(parts)[:5000]

    @staticmethod
    def _write_json(path: Path, data: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
