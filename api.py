"""
api.py — FastAPI entrypoint for the Gurney web-browsing agent.

Deploy to Google Cloud Run as a containerized service.
"""
from __future__ import annotations

import os
import traceback

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from config import DEFAULT_ENDPOINT, DEFAULT_MODEL, DEFAULT_API_KEY, DEFAULT_URL
from gurney import run_agent

app = FastAPI(title="Gurney", description="Web-browsing agent API")


# ── Request / Response models ─────────────────────────────────────────────────

class RunRequest(BaseModel):
    prompt: str = Field(..., description="Goal / task for the agent")
    url: str = Field(default=DEFAULT_URL, description="Starting URL")
    max_steps: int = Field(default=20, ge=1, le=50, description="Max interaction steps")


class RunResponse(BaseModel):
    success: bool
    result: str | None = None
    error: str | None = None


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/run", response_model=RunResponse)
async def run(req: RunRequest):
    try:
        result = await run_agent(
            prompt=req.prompt,
            url=req.url,
            endpoint=DEFAULT_ENDPOINT,
            model=DEFAULT_MODEL,
            api_key=DEFAULT_API_KEY,
            max_steps=req.max_steps,
            headless=True,
        )

        if result is None:
            return RunResponse(
                success=False,
                error=f"Reached max steps ({req.max_steps}) without an answer.",
            )

        return RunResponse(success=True, result=result)

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

