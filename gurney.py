import argparse
import asyncio
import json
import re
import sys
import textwrap

from openai import OpenAI
from playwright.async_api import async_playwright

# ── Constants ────────────────────────────────────────────────────────────────

MAX_SNAPSHOT_CHARS = 48_000  # Truncate snapshot to fit context windows

SYSTEM_PROMPT = textwrap.dedent("""\
You are a web-browsing agent. You are given:
1. A user GOAL that you must accomplish.
2. An accessibility tree snapshot of the current page. Each node has a "role" and "name".

You can perform ONE action per turn by responding with a JSON object.

Available actions:

  Click an element by its role and name:
  {"action": "click", "role": "<role>", "name": "<name>", "reason": "..."}

  Type into a field by its role and name:
  {"action": "type", "role": "<role>", "name": "<name>", "text": "text to type", "submit": true/false, "reason": "..."}

  Click a link or button by its exact visible text:
  {"action": "click_text", "text": "<visible text>", "reason": "..."}

  Fill a form field by its label:
  {"action": "fill_label", "label": "<label text>", "text": "value to fill", "reason": "..."}

  Fill a form field by its placeholder:
  {"action": "fill_placeholder", "placeholder": "<placeholder text>", "text": "value to fill", "reason": "..."}

  Navigate to a URL:
  {"action": "navigate", "url": "https://...", "reason": "..."}

  Scroll the page:
  {"action": "scroll", "direction": "up"|"down", "reason": "..."}

  Wait for the page to load:
  {"action": "wait", "seconds": 2, "reason": "..."}

  Provide a final answer when the GOAL is satisfied:
  {"action": "answer", "text": "your final answer", "reason": "..."}

Rules:
- Respond ONLY with a single JSON object — no markdown, no extra text.
- Use "role" and "name" from the accessibility tree to target elements.
- Common roles: link, button, textbox, heading, combobox, checkbox, radio, menuitem, tab, img.
- The "name" must match the accessible name shown in the tree.
- When you have enough information to satisfy the GOAL, use the "answer" action.
- If the page doesn't have what you need, navigate or click to find it.
- Keep "reason" short (one sentence).
""")


# ── Accessibility tree formatting ────────────────────────────────────────────

def format_a11y_tree(node: dict, depth: int = 0) -> str:
    """Convert Playwright's accessibility snapshot dict into a readable text tree."""
    if node is None:
        return "[empty page]"

    lines = []
    indent = "  " * depth
    role = node.get("role", "")
    name = node.get("name", "")
    value = node.get("value", "")
    checked = node.get("checked")
    selected = node.get("selected")
    level = node.get("level")

    # Build the node description
    parts = [role]
    if name:
        parts.append(f'"{name}"')
    if value:
        parts.append(f'value="{value}"')
    if checked is not None:
        parts.append(f'checked={checked}')
    if selected is not None:
        parts.append(f'selected={selected}')
    if level is not None:
        parts.append(f'level={level}')

    line = f"{indent}[{' '.join(parts)}]"
    lines.append(line)

    for child in node.get("children", []):
        lines.append(format_a11y_tree(child, depth + 1))

    return "\n".join(lines)


# ── Agent ────────────────────────────────────────────────────────────────────

class WebAgent:
    def __init__(self, endpoint: str, model: str, api_key: str = "no-key"):
        self.client = OpenAI(base_url=endpoint, api_key=api_key)
        self.model = model
        self.history: list[dict] = []

    def _chat(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + self.history,
            temperature=0.2,
        )
        reply = resp.choices[0].message.content.strip()
        self.history.append({"role": "assistant", "content": reply})
        return reply

    @staticmethod
    def _parse_action(text: str) -> dict | None:
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


# ── Execution ────────────────────────────────────────────────────────────────

async def execute_action(page, action: dict) -> str | None:
    """Execute a single action on the page. Returns an answer string or None."""
    act = action.get("action")

    if act == "answer":
        return action.get("text", "")

    elif act == "click":
        role = action.get("role", "")
        name = action.get("name", "")
        locator = page.get_by_role(role, name=name)
        await locator.first.click(timeout=5000)
        await page.wait_for_timeout(1500)

    elif act == "click_text":
        text = action.get("text", "")
        locator = page.get_by_text(text, exact=False)
        await locator.first.click(timeout=5000)
        await page.wait_for_timeout(1500)

    elif act == "type":
        role = action.get("role", "")
        name = action.get("name", "")
        text = action.get("text", "")
        submit = action.get("submit", False)
        locator = page.get_by_role(role, name=name)
        await locator.first.fill("")
        await locator.first.type(text, delay=30)
        if submit:
            await locator.first.press("Enter")
        await page.wait_for_timeout(1500)

    elif act == "fill_label":
        label = action.get("label", "")
        text = action.get("text", "")
        locator = page.get_by_label(label)
        await locator.first.fill(text)
        await page.wait_for_timeout(1000)

    elif act == "fill_placeholder":
        placeholder = action.get("placeholder", "")
        text = action.get("text", "")
        locator = page.get_by_placeholder(placeholder)
        await locator.first.fill(text)
        await page.wait_for_timeout(1000)

    elif act == "navigate":
        nav_url = action.get("url", "")
        await page.goto(nav_url, wait_until="domcontentloaded", timeout=30_000)
        await page.wait_for_timeout(2000)

    elif act == "scroll":
        direction = action.get("direction", "down")
        delta = -500 if direction == "up" else 500
        await page.mouse.wheel(0, delta)
        await page.wait_for_timeout(1000)

    elif act == "wait":
        secs = action.get("seconds", 2)
        await page.wait_for_timeout(int(secs * 1000))

    else:
        print(f"  ⚠️  Unknown action: {act}")

    return None


# ── Main loop ────────────────────────────────────────────────────────────────

async def run_agent(
    prompt: str,
    url: str,
    endpoint: str,
    model: str,
    api_key: str = "no-key",
    max_steps: int = 20,
    headless: bool = False,
):
    agent = WebAgent(endpoint, model, api_key)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        print(f"\n🌐  Navigating to {url} …")
        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        await page.wait_for_timeout(2000)

        for step in range(1, max_steps + 1):
            # ── 1. Grab accessibility snapshot ───────────────────────
            try:
                snapshot = await page.accessibility.snapshot()
                tree_text = format_a11y_tree(snapshot)
            except Exception as e:
                tree_text = f"[Error getting accessibility tree: {e}]"

            if len(tree_text) > MAX_SNAPSHOT_CHARS:
                tree_text = tree_text[:MAX_SNAPSHOT_CHARS] + "\n…[truncated]"

            current_url = page.url
            user_msg = (
                f"GOAL: {prompt}\n\n"
                f"Current URL: {current_url}\n\n"
                f"Accessibility Tree:\n{tree_text}"
            )

            # ── 2. Ask the LLM ──────────────────────────────────────
            print(f"\n{'─'*60}")
            print(f"  Step {step}/{max_steps}")
            print(f"  URL: {current_url}")

            raw = agent._chat(user_msg)

            action = agent._parse_action(raw)
            if action is None:
                print(f"  ⚠️  Could not parse action from LLM response:\n{raw[:300]}")
                continue

            act = action.get("action")
            reason = action.get("reason", "")
            print(f"  Action: {act}  —  {reason}")

            # ── 3. Execute the action ────────────────────────────────
            try:
                result = await execute_action(page, action)
                if result is not None:
                    print(f"\n{'═'*60}")
                    print(f"  ✅  AGENT ANSWER:\n\n{result}")
                    print(f"{'═'*60}\n")
                    await browser.close()
                    return result

            except Exception as e:
                err_msg = f"Action '{act}' failed: {e}"
                print(f"  ❌  {err_msg}")
                agent.history.append(
                    {"role": "user", "content": f"ERROR: {err_msg}. Try a different approach."}
                )

        print(f"\n⚠️  Reached max steps ({max_steps}) without an answer.")
        await browser.close()
        return None


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Web-browsing agent powered by an OpenAI-compatible LLM."
    )
    parser.add_argument("--prompt", required=True, help="Goal / task for the agent")
    parser.add_argument("--url", required=True, help="Starting URL to navigate to")
    parser.add_argument(
        "--endpoint",
        required=True,
        help="OpenAI-compatible API base URL (e.g. http://localhost:11434/v1)",
    )
    parser.add_argument("--model", required=True, help="Model name to use")
    parser.add_argument("--api-key", default="no-key", help="API key (default: no-key)")
    parser.add_argument(
        "--max-steps", type=int, default=20, help="Max interaction steps (default: 20)"
    )
    parser.add_argument(
        "--headless", action="store_true", help="Run browser in headless mode"
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
            headless=args.headless,
        )
    )

    if result is None:
        sys.exit(1)


if __name__ == "__main__":
    main()
