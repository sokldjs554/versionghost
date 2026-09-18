from __future__ import annotations

from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .service import ClaimRequest, claim_reward

app = FastAPI(title="Synthetic LiveOps API", version="1.0")


class ClaimBody(BaseModel):
    player_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1)
    streak_days: int = Field(default=0, ge=0)


@app.post("/v1/rewards/claim")
def claim(body: ClaimBody, x_client_version: str = Header(default="1.9")) -> JSONResponse:
    status, payload = claim_reward(
        ClaimRequest(
            player_id=body.player_id,
            event_id=body.event_id,
            idempotency_key=body.idempotency_key,
            streak_days=body.streak_days,
        )
    )
    return JSONResponse(status_code=status, content=payload)
