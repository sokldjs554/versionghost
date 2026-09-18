from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class RunStage(StrEnum):
    QUEUED = "queued"
    ANALYZING = "analyzing"
    CONTRACTING = "contracting"
    PATCHING = "patching"
    VERIFYING = "verifying"
    REPAIRING = "repairing"
    COMPLETE = "complete"
    FAILED = "failed"


class Requirement(BaseModel):
    id: str
    text: str
    kind: Literal["behavior", "compatibility", "invariant", "error_contract"]
    verification: str


class ChangeContract(BaseModel):
    title: str
    intent: str
    requirements: list[Requirement]
    protected_clients: list[str]
    assumptions: list[str] = Field(default_factory=list)


class PatchOperation(BaseModel):
    path: str
    find: str
    replace: str
    rationale: str


class PatchSet(BaseModel):
    summary: str
    operations: list[PatchOperation]


class ImpactNode(BaseModel):
    id: str
    kind: str
    path: str
    symbol: str | None = None


class ImpactEdge(BaseModel):
    source: str
    target: str
    relation: str


class ImpactReport(BaseModel):
    nodes: list[ImpactNode]
    edges: list[ImpactEdge]
    touched_candidates: list[str]
    uncertainty: list[str] = Field(default_factory=list)


class CheckResult(BaseModel):
    name: str
    status: Literal["pass", "fail", "warn"]
    detail: str
    duration_ms: int = 0


class ReplayCell(BaseModel):
    client_version: str
    case_id: str
    status: Literal["pass", "fail"]
    detail: str


class AttemptResult(BaseModel):
    attempt: int
    patch_summary: str
    changed_files: list[str]
    checks: list[CheckResult]
    replay: list[ReplayCell]
    passed: bool


class RequirementEvidence(BaseModel):
    requirement_id: str
    status: Literal["proven", "unproven"]
    evidence: list[str]


class MergePacket(BaseModel):
    run_id: str
    verdict: Literal["ready_with_evidence", "blocked"]
    contract: ChangeContract
    impact: ImpactReport
    attempts: list[AttemptResult]
    requirement_evidence: list[RequirementEvidence]
    changed_files: list[str]
    limitations: list[str]
    model_route: str
    metrics: dict[str, Any] = Field(default_factory=dict)


class RunRecord(BaseModel):
    id: str
    request_text: str
    scenario: str
    provider: str
    stage: RunStage
    status_message: str
    created_at: str
    updated_at: str
    packet: MergePacket | None = None
    events: list[dict[str, Any]] = Field(default_factory=list)
