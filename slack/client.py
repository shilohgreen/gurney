"""
slack/client.py — Async HTTP client that calls the deployed Gurney API.
"""
from __future__ import annotations

import aiohttp

from slack.config import GURNEY_API_URL, GURNEY_DEFAULT_URL, GURNEY_MAX_STEPS, GURNEY_API_TIMEOUT


async def run_agent(prompt: str, url: str | None = None, max_steps: int | None = None) -> dict:
    """
    Call the Gurney /run endpoint and return the JSON response.

    Returns dict with keys: success (bool), result (str|None), error (str|None)
    Raises on network / HTTP errors.
    """
    payload = {
        "prompt": prompt,
        "url": url or GURNEY_DEFAULT_URL,
        "max_steps": max_steps or GURNEY_MAX_STEPS,
    }

    timeout = aiohttp.ClientTimeout(total=GURNEY_API_TIMEOUT)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(f"{GURNEY_API_URL}/run", json=payload) as resp:
            if resp.status != 200:
                text = await resp.text()
                return {
                    "success": False,
                    "result": None,
                    "error": f"API returned {resp.status}: {text[:500]}",
                }
            return await resp.json()

