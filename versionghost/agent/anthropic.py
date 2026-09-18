from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx

from versionghost.agent.openai_compat import _read_candidate_files
from versionghost.models import ChangeContract, ImpactReport, PatchSet


class AnthropicProvider:
    """Optional hosted LLM route using the Anthropic Messages API."""

    name = "anthropic"

    def __init__(self) -> None:
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY is required for provider=anthropic")
        self.api_key = key
        self.model = os.getenv("VERSIONGHOST_ANTHROPIC_MODEL", "claude-sonnet-4-5")
        self.timeout = float(os.getenv("VERSIONGHOST_LLM_TIMEOUT_SECONDS", "60"))

    def _chat_json(self, system: str, user: str) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 5000,
                    "temperature": 0,
                    "system": system + " Return raw JSON only, without markdown fences.",
                    "messages": [{"role": "user", "content": user}],
                },
            )
            response.raise_for_status()
        blocks = response.json().get("content", [])
        text = "".join(block.get("text", "") for block in blocks if block.get("type") == "text")
        return json.loads(text)

    def build_contract(self, request_text: str, impact: ImpactReport) -> ChangeContract:
        data = self._chat_json(
            "Compile a software change request into ChangeContract JSON with explicit compatibility and invariant checks.",
            json.dumps({"request": request_text, "impact": impact.model_dump()}, ensure_ascii=False),
        )
        return ChangeContract.model_validate(data)

    def propose_patch(
        self, request_text: str, contract: ChangeContract, repo_root: Path, impact: ImpactReport
    ) -> PatchSet:
        data = self._chat_json(
            "Produce PatchSet JSON containing exact find/replace operations only. Never change tests or historical client fixtures and never request shell execution.",
            json.dumps(
                {
                    "request": request_text,
                    "contract": contract.model_dump(),
                    "files": _read_candidate_files(repo_root, impact.touched_candidates),
                },
                ensure_ascii=False,
            ),
        )
        return PatchSet.model_validate(data)

    def repair_patch(
        self,
        request_text: str,
        contract: ChangeContract,
        repo_root: Path,
        failure_summary: str,
        impact: ImpactReport,
    ) -> PatchSet:
        data = self._chat_json(
            "Repair the candidate using the verification failures. Return PatchSet JSON only. Preserve the verification surface.",
            json.dumps(
                {
                    "request": request_text,
                    "contract": contract.model_dump(),
                    "failure_summary": failure_summary,
                    "files": _read_candidate_files(repo_root, impact.touched_candidates),
                },
                ensure_ascii=False,
            ),
        )
        return PatchSet.model_validate(data)
