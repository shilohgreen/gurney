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


async def _process_prompt(prompt: str, say, thread_ts: str | None = None):
    """
    Shared logic: call the Gurney API and post the result back to Slack.
    All replies are posted in the same thread as the original message.
    """
    if not prompt:
        await say(
            ":warning: Please provide a prompt. Example: `/gurney Log in and describe the dashboard`",
            thread_ts=thread_ts,
        )
        return

    # Let the user know the agent is working
    await say(f"I'm working on it...\n> _{prompt}_", thread_ts=thread_ts)

    try:
        result = await run_agent(prompt)

        if result.get("success"):
            answer = result.get("result", "(no result)")
            await say(f":white_check_mark: *Gurney result:*\n\n{answer}", thread_ts=thread_ts)
        else:
            error = result.get("error", "Unknown error")
            await say(f":x: Agent failed: {error}", thread_ts=thread_ts)

    except Exception as e:
        logger.error(f"[ 🔥 _process_prompt ] {traceback.format_exc()}")
        await say(f":x: Something went wrong calling the Gurney API:\n```{e}```", thread_ts=thread_ts)


def register_handlers(app: AsyncApp):
    """Attach all event/command listeners to the Bolt app."""
    
    logger.info("[ 🔧 register_handlers ] Registering event handlers...")

    # ── Slash command: /gurney ────────────────────────────────────────────────
    @app.command("/gurney")
    async def handle_gurney_command(ack, body, say):
        """Handle /gurney <prompt>."""
        logger.info(f"[ 🎯 handle_gurney_command ] Received command: {body}")
        await ack()
        prompt = (body.get("text") or "").strip()
        logger.info(f"[ 🎯 handle_gurney_command ] prompt={prompt!r}")
        # Slash commands don't have a thread_ts, so replies go to channel
        await _process_prompt(prompt, say)

    # ── App mention: @gurney <prompt> ─────────────────────────────────────────
    @app.event("app_mention")
    async def handle_app_mention(event, say):
        """Handle @gurney mentions in channels."""
        logger.info(f"[ 💬 handle_app_mention ] Received event: {event}")
        raw_text = event.get("text", "")
        prompt = _extract_prompt(raw_text)
        thread_ts = event.get("thread_ts") or event.get("ts")
        logger.info(f"[ 💬 handle_app_mention ] prompt={prompt!r}")
        await _process_prompt(prompt, say, thread_ts=thread_ts)

    # ── Direct messages ───────────────────────────────────────────────────────
    @app.event("message")
    async def handle_dm(event, say):
        """Handle direct messages sent to the bot."""
        logger.info(f"[ 📩 handle_dm ] Received message event: {event}")
        # Only respond in DMs (channel type 'im')
        if event.get("channel_type") != "im":
            logger.info(f"[ 📩 handle_dm ] Not a DM, channel_type={event.get('channel_type')}")
            return
        # Ignore bot's own messages and message_changed subtypes
        if event.get("bot_id") or event.get("subtype"):
            logger.info(f"[ 📩 handle_dm ] Ignoring bot message or subtype")
            return

        prompt = (event.get("text") or "").strip()
        thread_ts = event.get("thread_ts") or event.get("ts")
        logger.info(f"[ 📩 handle_dm ] prompt={prompt!r}")
        await _process_prompt(prompt, say, thread_ts=thread_ts)
    
    # ── Debug: Catch-all event handler to see ALL events ────────────────────────
    @app.event({"type": re.compile(".*")})
    async def catch_all_events(event, logger):
        """Catch-all handler to log any events we're not explicitly handling."""
        event_type = event.get("type", "unknown")
        logger.info(f"[ 🔍 catch_all_events ] Unhandled event type: {event_type}")
        logger.info(f"[ 🔍 catch_all_events ] Event data: {event}")
    
    logger.info("[ 🔧 register_handlers ] Handlers registered successfully")

