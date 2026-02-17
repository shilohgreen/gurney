#!/usr/bin/env python3
"""
slack/app.py — Entrypoint for the Gurney Slack bot.

Uses Bolt for Python (async) with Socket Mode so no public URL is needed.

Usage:
    python -m slack.app

Required env vars (set in .env):
    SLACK_BOT_TOKEN   — xoxb-… bot token
    SLACK_APP_TOKEN   — xapp-… app-level token (with connections:write scope)
    GURNEY_API_URL    — base URL of the deployed Gurney Cloud Run service
"""
from __future__ import annotations

import asyncio
import logging
import sys

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from slack.config import SLACK_BOT_TOKEN, SLACK_APP_TOKEN, GURNEY_API_URL
from slack.handlers import register_handlers

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ── Validate env ──────────────────────────────────────────────────────────────

def _check_env():
    missing = []
    if not SLACK_BOT_TOKEN:
        missing.append("SLACK_BOT_TOKEN")
    if not SLACK_APP_TOKEN:
        missing.append("SLACK_APP_TOKEN")
    if missing:
        logger.error(f"Missing required env vars: {', '.join(missing)}")
        logger.error("Set them in your .env file and try again.")
        sys.exit(1)


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> AsyncApp:
    """Build and configure the Bolt AsyncApp."""
    app = AsyncApp(token=SLACK_BOT_TOKEN)
    register_handlers(app)
    return app


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    _check_env()

    logger.info("🚀 Starting Gurney Slack bot (Socket Mode)")
    logger.info(f"   Gurney API: {GURNEY_API_URL}")

    app = create_app()
    handler = AsyncSocketModeHandler(app, SLACK_APP_TOKEN)
    await handler.start_async()


if __name__ == "__main__":
    asyncio.run(main())

