from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx

from versionghost.models import ChangeContract, ImpactReport, PatchSet


class OpenAICompatibleProvider:
    """Provider for Ollama/vLLM/OpenAI-compatible chat endpoints.

    This adapter is intentionally small. The engine still owns file allowlists, patch application,
    test execution, and compatibility gates; model output never executes shell commands directly.
    """

    name = "openai-compatible"

    def __init__(self) -> None:
        self.base_url = os.getenv("VERSIONGHOST_OPENAI_BASE_URL", "http://127.0.0.1:11434/v1")
        self.model = os.getenv("VERSIONGHOST_OPENAI_MODEL", "qwen2.5-coder:7b")
        self.api_key = os.getenv("VERSIONGHOST_OPENAI_API_KEY", "ollama")
        self.timeout = float(os.getenv("VERSIONGHOST_LLM_TIMEOUT_SECONDS", "60"))

    def _chat_json(self, system: str, user: str) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "response_format": {"type": "json_object"},
        }
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)

    def build_contract(self, request_text: str, impact: ImpactReport) -> ChangeContract:
        data = self._chat_json(
            "Return only JSON matching the ChangeContract schema. Preserve backward compatibility as an explicit requirement when historical clients exist.",
            json.dumps({"request": request_text, "impact": impact.model_dump()}, ensure_ascii=False),
        )
        return ChangeContract.model_validate(data)

    def propose_patch(
        self, request_text: str, contract: ChangeContract, repo_root: Path, impact: ImpactReport
    ) -> PatchSet:
        context = _read_candidate_files(repo_root, impact.touched_candidates)
        data = self._chat_json(
            "Return only JSON matching PatchSet. Use exact find/replace operations. Never request shell commands, new dependencies, or paths outside the repository.",
            json.dumps(
                {
                    "request": request_text,
                    "contract": contract.model_dump(),
                    "files": context,
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
        context = _read_candidate_files(repo_root, impact.touched_candidates)
        data = self._chat_json(
            "Repair the patch using verification failures. Return only PatchSet JSON. Do not weaken or delete tests and do not change historical client fixtures.",
            json.dumps(
                {
                    "request": request_text,
                    "contract": contract.model_dump(),
                    "failure_summary": failure_summary,
                    "files": context,
                },
                ensure_ascii=False,
            ),
        )
        return PatchSet.model_validate(data)


def _read_candidate_files(repo_root: Path, candidates: list[str], limit: int = 6) -> dict[str, str]:
    files: dict[str, str] = {}
    for rel in candidates[:limit]:
        path = (repo_root / rel).resolve()
        if repo_root.resolve() not in path.parents or not path.is_file():
            continue
        if path.suffix not in {".py", ".ts", ".tsx", ".json", ".yaml", ".yml"}:
            continue
        files[rel] = path.read_text(encoding="utf-8")[:16000]
    return files
