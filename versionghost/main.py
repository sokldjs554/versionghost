from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from versionghost.engine.pipeline import VersionGhostPipeline
from versionghost.store import RunStore

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = Path(os.getenv("VERSIONGHOST_STATE_DIR", PROJECT_ROOT / ".versionghost"))
STORE = RunStore(STATE_DIR / "runs.db")
PIPELINE = VersionGhostPipeline(PROJECT_ROOT, STORE)
EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="versionghost")

app = FastAPI(
    title="VersionGhost",
    version="0.1.0",
    description="AI compatibility agent for live-service API changes.",
)


class RunRequest(BaseModel):
    request_text: str = Field(min_length=12, max_length=5000)
    provider: str = Field(default="deterministic-demo")
    scenario: str = Field(default="streak-bonus-compatibility")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "versionghost", "version": "0.1.0"}


@app.post("/api/runs", status_code=202)
def create_run(body: RunRequest) -> dict[str, str]:
    if body.provider not in {"deterministic-demo", "openai-compatible", "ollama", "anthropic"}:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    run_id = PIPELINE.start_run(
        body.request_text, provider_name=body.provider, scenario=body.scenario
    )
    EXECUTOR.submit(PIPELINE.execute, run_id)
    return {"id": run_id, "stage": "queued"}


@app.get("/api/runs")
def list_runs() -> dict[str, object]:
    return {"items": [item.model_dump(mode="json") for item in STORE.list()]}


@app.get("/api/runs/{run_id}")
def get_run(run_id: str) -> dict[str, object]:
    try:
        return STORE.get(run_id).model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@app.get("/api/demo/request")
def demo_request() -> dict[str, str]:
    return {
        "request_text": (
            "Add a streak bonus for v2 mobile clients. v2 must receive base_coins, "
            "streak_bonus, and total_coins. Keep v1.4/v1.9 response compatibility, "
            "preserve idempotent retries, keep the three-claim daily limit as HTTP 409, "
            "and make a retry safe even if the client upgrades from v1 to v2 between attempts."
        )
    }


STATIC = PROJECT_ROOT / "versionghost" / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")
