"""
slack/handlers.py — Slack event handlers for the Gurney bot.

Handles:
  - /gurney <prompt>       (slash command)
  - @gurney <prompt>       (app mention)
  - DM messages to the bot (direct messages)
"""
from __future__ import annotations

import logging
import re
import traceback

from slack_bolt.async_app import AsyncApp

from slack.client import run_agent

logger = logging.getLogger(__name__)


def _extract_prompt(text: str) -> str:
    """Strip bot mention markup (<@UXXXX>) and return the remaining text."""
    return re.sub(r"<@[A-Z0-9]+>\s*", "", text).strip()


async def _process_prompt(prompt: str, say, channel: str | None = None):
    """
    Shared logic: call the Gurney API and post the result back to Slack.
    """
    if not prompt:
        await say(":warning: Please provide a prompt. Example: `/gurney Log in and describe the dashboard`")
        return

    # Let the user know the agent is working
    await say(f":robot_face: Running Gurney agent…\n> _{prompt}_")

    try:
        result = await run_agent(prompt)

        if result.get("success"):
            answer = result.get("result", "(no result)")
            await say(f":white_check_mark: *Gurney result:*\n\n{answer}")
        else:
            error = result.get("error", "Unknown error")
            await say(f":x: Agent failed: {error}")

    except Exception as e:
        logger.error(f"[ 🔥 _process_prompt ] {traceback.format_exc()}")
        await say(f":x: Something went wrong calling the Gurney API:\n```{e}```")


def register_handlers(app: AsyncApp):
    """Attach all event/command listeners to the Bolt app."""

    # ── Slash command: /gurney ────────────────────────────────────────────────
    @app.command("/gurney")
    async def handle_gurney_command(ack, body, say):
        """Handle /gurney <prompt>."""
        await ack()
        prompt = (body.get("text") or "").strip()
        logger.info(f"[ 🎯 handle_gurney_command ] prompt={prompt!r}")
        await _process_prompt(prompt, say)

    # ── App mention: @gurney <prompt> ─────────────────────────────────────────
    @app.event("app_mention")
    async def handle_app_mention(event, say):
        """Handle @gurney mentions in channels."""
        raw_text = event.get("text", "")
        prompt = _extract_prompt(raw_text)
        logger.info(f"[ 💬 handle_app_mention ] prompt={prompt!r}")
        await _process_prompt(prompt, say)

    # ── Direct messages ───────────────────────────────────────────────────────
    @app.event("message")
    async def handle_dm(event, say):
        """Handle direct messages sent to the bot."""
        # Only respond in DMs (channel type 'im')
        if event.get("channel_type") != "im":
            return
        # Ignore bot's own messages and message_changed subtypes
        if event.get("bot_id") or event.get("subtype"):
            return

        prompt = (event.get("text") or "").strip()
        logger.info(f"[ 📩 handle_dm ] prompt={prompt!r}")
        await _process_prompt(prompt, say)

