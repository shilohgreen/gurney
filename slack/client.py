"""
slack/client.py — Async HTTP client that calls the deployed Gurney API.
"""
from __future__ import annotations

import logging

import aiohttp

from slack.config import GURNEY_API_URL, GURNEY_DEFAULT_URL, GURNEY_MAX_STEPS, GURNEY_API_TIMEOUT

logger = logging.getLogger(__name__)


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

    api_url = f"{GURNEY_API_URL}/run"
    logger.info(f"[ 🌐 run_agent ] Calling API: {api_url}")
    logger.info(f"[ 🌐 run_agent ] Payload: prompt={prompt!r}, url={payload['url']}, max_steps={payload['max_steps']}")

    timeout = aiohttp.ClientTimeout(total=GURNEY_API_TIMEOUT)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(api_url, json=payload) as resp:
                logger.info(f"[ 🌐 run_agent ] API response status: {resp.status}")
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(f"[ 🌐 run_agent ] API error: {resp.status} - {text[:500]}")
                    return {
                        "success": False,
                        "result": None,
                        "error": f"API returned {resp.status}: {text[:500]}",
                    }
                result = await resp.json()
                logger.info(f"[ 🌐 run_agent ] API success: {result.get('success', False)}")
                return result
    except aiohttp.ClientError as e:
        logger.error(f"[ 🌐 run_agent ] Connection error: {e}")
        raise
    except Exception as e:
        logger.error(f"[ 🌐 run_agent ] Unexpected error: {e}")
        raise

