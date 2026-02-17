from __future__ import annotations

import json
import re
import time

from openai import OpenAI

from config import SYSTEM_PROMPT


class WebAgent:
    """LLM-powered agent that decides actions based on page snapshots."""

    def __init__(self, endpoint: str, model: str, api_key: str = "no-key"):
        self.client = OpenAI(base_url=endpoint, api_key=api_key)
        self.model = model
        self.history: list[dict] = []

    def chat(self, user_message: str) -> str:
        """Send a message to the LLM and get a response. Retries on 429."""
        self.history.append({"role": "user", "content": user_message})

        for attempt in range(4):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": SYSTEM_PROMPT}] + self.history,
                    temperature=0.2,
                )
                reply = resp.choices[0].message.content.strip()
                self.history.append({"role": "assistant", "content": reply})
                return reply
            except Exception as e:
                if "429" in str(e) and attempt < 3:
                    wait = (attempt + 1) * 5
                    print(f"  ⏳  Rate limited — retrying in {wait}s …")
                    time.sleep(wait)
                else:
                    raise

    def add_error(self, error_msg: str):
        """Feed an error back into history so the LLM can recover."""
        self.history.append(
            {"role": "user", "content": f"ERROR: {error_msg}. Try a different approach."}
        )

    @staticmethod
    def parse_action(text: str) -> dict | None:
        """Extract the first JSON object from the LLM response."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
        return None

