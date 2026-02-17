from __future__ import annotations

import os
import textwrap

from dotenv import load_dotenv

load_dotenv()

# ── Defaults ──────────────────────────────────────────────────────────────────

DEFAULT_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/openai"
DEFAULT_MODEL = "gemini-2.0-flash"
DEFAULT_API_KEY = os.getenv("GEMINI_API_KEY", "no-key")
DEFAULT_URL = "https://learnpf.ai"

LEARNPF_USERNAME = os.getenv("LEARNPF_USERNAME")
LEARNPF_PASSWORD = os.getenv("LEARNPF_PASSWORD")

print(LEARNPF_USERNAME)
print(LEARNPF_PASSWORD)

if not LEARNPF_USERNAME:
    print("⚠️  LEARNPF_USERNAME not set in .env")
if not LEARNPF_PASSWORD:
    print("⚠️  LEARNPF_PASSWORD not set in .env")

# ── Constants ────────────────────────────────────────────────────────────────

MAX_SNAPSHOT_CHARS = 48_000
ACTION_DELAY = 3000  # ms between every interaction

# ── System prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = textwrap.dedent("""\
You are a web-browsing agent. You are given:
1. A user GOAL that you must accomplish.
2. An accessibility tree snapshot of the current page. Each node has a "role" and "name".

You can perform ONE action per turn by responding with a JSON object.

Available actions:

  Click an element — use ONE of these targeting methods:
  {"action": "click", "target": {"role": "<role>", "name": "<name>"}, "reason": "..."}
  {"action": "click", "target": {"text": "<visible text>"}, "reason": "..."}

  Fill an input field — use ONE of these targeting methods:
  {"action": "fill", "target": {"role": "<role>", "name": "<name>"}, "text": "value", "submit": true/false, "reason": "..."}
  {"action": "fill", "target": {"label": "<label text>"}, "text": "value", "submit": true/false, "reason": "..."}
  {"action": "fill", "target": {"placeholder": "<placeholder>"}, "text": "value", "submit": true/false, "reason": "..."}

  Provide a final answer when the GOAL is satisfied:
  {"action": "answer", "text": "your final answer", "reason": "..."}

Targeting rules:
- "target" tells the agent HOW to find the element. Pick the most specific method.
- For "role"/"name": use values from the accessibility tree. Common roles: link, button, textbox, heading, combobox, checkbox, radio, menuitem, tab, img.
- For "text": use the exact visible text on the element.
- For "label": use the form field's label text.
- For "placeholder": use the input's placeholder text.

Credentials:
- When filling login/auth fields, use these exact placeholders as the "text" value:
  - For username or email fields: {{username}}
  - For password fields: {{password}}
- NEVER invent or guess credentials. Always use the placeholders above.

General rules:
- Respond ONLY with a single JSON object — no markdown, no extra text.
- When you have enough information to satisfy the GOAL, use the "answer" action.
- Keep "reason" short (one sentence).
""")

