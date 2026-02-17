"""
slack/config.py — Environment variables and constants for the Slack bot.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

# ── Slack credentials ─────────────────────────────────────────────────────────
# Bot token (xoxb-…) — needs chat:write, app_mentions:read, commands scopes
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")

# App-level token (xapp-…) — needs connections:write scope (for Socket Mode)
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN", "")

# ── Gurney API ────────────────────────────────────────────────────────────────
# Base URL of the deployed Gurney Cloud Run service (no trailing slash)
GURNEY_API_URL = os.environ.get("GURNEY_API_URL", "http://localhost:8080")

# Default starting URL for the agent
GURNEY_DEFAULT_URL = os.environ.get("GURNEY_DEFAULT_URL", "https://learnpf.ai")

# Max steps the agent can take per run
GURNEY_MAX_STEPS = int(os.environ.get("GURNEY_MAX_STEPS", "20"))

# Timeout in seconds for waiting on the Gurney API (agent runs can be slow)
GURNEY_API_TIMEOUT = int(os.environ.get("GURNEY_API_TIMEOUT", "300"))

