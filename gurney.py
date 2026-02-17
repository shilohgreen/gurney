#!/usr/bin/env python3
"""
gurney.py — CLI entrypoint for the web-browsing agent.

Usage:
    python gurney.py --prompt "Find the pricing plans"
    python gurney.py --prompt "Log in and describe the dashboard" --no-headless
"""
from __future__ import annotations

import argparse
import asyncio
import sys

from config import (
    DEFAULT_ENDPOINT, DEFAULT_MODEL, DEFAULT_API_KEY, DEFAULT_URL,
    LEARNPF_USERNAME, LEARNPF_PASSWORD,
)
from agent import WebAgent
from browser import launch_browser, navigate, get_snapshot, execute_action, take_screenshot


# ── Credential injection ─────────────────────────────────────────────────────

PLACEHOLDERS = {
    "{{username}}": LEARNPF_USERNAME,
    "{{password}}": LEARNPF_PASSWORD,
}


def inject_credentials(action: dict) -> dict:
    """Replace {{username}} / {{password}} placeholders with real values from .env."""
    if action.get("action") != "fill":
        return action

    text = action.get("text", "")
    for placeholder, real_value in PLACEHOLDERS.items():
        if placeholder in text and real_value:
            print(f"  🔑  Injecting real value for {placeholder}")
            action["text"] = text.replace(placeholder, real_value)

    return action


# ── Main loop ────────────────────────────────────────────────────────────────

async def run_agent(
    prompt: str,
    url: str,
    endpoint: str,
    model: str,
    api_key: str = "no-key",
    max_steps: int = 20,
    headless: bool = True,
):
    agent = WebAgent(endpoint, model, api_key)
    pw, browser, page = await launch_browser(headless=headless)

    try:
        await navigate(page, url)

        # ── Debug: print snapshot and exit (remove when agent loop is active)
        tree_text = await get_snapshot(page)
        print(f"\n{'═'*60}")
        print(f"  Accessibility Tree for {page.url}")
        print(f"{'═'*60}\n")
        print(tree_text)
        print(f"\n{'═'*60}\n")

        # ── Agent loop (uncomment when ready to use with LLM) ────
        for step in range(1, max_steps + 1):
            tree_text = await get_snapshot(page)
        
            user_msg = (
                f"GOAL: {prompt}\n\n"
                f"Current URL: {page.url}\n\n"
                f"Accessibility Tree:\n{tree_text}"
            )
        
            print(f"\n{'─'*60}")
            print(f"  Step {step}/{max_steps}")
            print(f"  URL: {page.url}")
        
            raw = agent.chat(user_msg)
        
            action = agent.parse_action(raw)
            if action is None:
                print(f"  ⚠️  Could not parse action:\n{raw[:300]}")
                continue
        
            act = action.get("action")
            reason = action.get("reason", "")
            print(f"  Action: {act}  —  {reason}")
        
            action = inject_credentials(action)

            try:
                result = await execute_action(page, action)
                if result is not None:
                    print(f"\n{'═'*60}")
                    print(f"  ✅  AGENT ANSWER:\n\n{result}")
                    print(f"{'═'*60}\n")
                    return result
            except Exception as e:
                err_msg = f"Action '{act}' failed: {e}"
                print(f"  ❌  {err_msg}")
                agent.add_error(err_msg)
        
        print(f"\n⚠️  Reached max steps ({max_steps}) without an answer.")
        return None

    finally:
        await take_screenshot(page, label="exit")
        await browser.close()
        await pw.stop()


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Web-browsing agent powered by an OpenAI-compatible LLM."
    )
    parser.add_argument("--prompt", required=True, help="Goal / task for the agent")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"Starting URL (default: {DEFAULT_URL})")
    parser.add_argument(
        "--endpoint",
        default=DEFAULT_ENDPOINT,
        help=f"OpenAI-compatible API base URL (default: {DEFAULT_ENDPOINT})",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model name (default: {DEFAULT_MODEL})")
    parser.add_argument("--api-key", default=DEFAULT_API_KEY, help="API key")
    parser.add_argument(
        "--max-steps", type=int, default=20, help="Max interaction steps (default: 20)"
    )
    parser.add_argument(
        "--no-headless", action="store_true", help="Show the browser window"
    )

    args = parser.parse_args()

    result = asyncio.run(
        run_agent(
            prompt=args.prompt,
            url=args.url,
            endpoint=args.endpoint,
            model=args.model,
            api_key=args.api_key,
            max_steps=args.max_steps,
            headless=not args.no_headless,
        )
    )

    if result is None:
        sys.exit(1)


if __name__ == "__main__":
    main()
