from __future__ import annotations

from pathlib import Path
from typing import Protocol

from versionghost.models import ChangeContract, ImpactReport, PatchSet


class AgentProvider(Protocol):
    name: str

    def build_contract(self, request_text: str, impact: ImpactReport) -> ChangeContract: ...

    def propose_patch(
        self, request_text: str, contract: ChangeContract, repo_root: Path, impact: ImpactReport
    ) -> PatchSet: ...

    def repair_patch(
        self,
        request_text: str,
        contract: ChangeContract,
        repo_root: Path,
        failure_summary: str,
        impact: ImpactReport,
    ) -> PatchSet: ...
