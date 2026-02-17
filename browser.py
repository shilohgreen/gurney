from __future__ import annotations

from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright, Page, Browser

from config import ACTION_DELAY, MAX_SNAPSHOT_CHARS


async def launch_browser(headless: bool = True):
    """Launch Chromium and return (playwright, browser, page)."""
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=headless)
    context = await browser.new_context(
        viewport={"width": 1280, "height": 900},
        ignore_https_errors=True,
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    )
    page = await context.new_page()
    return pw, browser, page


async def navigate(page: Page, url: str):
    """Navigate to a URL and wait for the page to fully render."""
    print(f"\n🌐  Navigating to {url} …")
    await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

    try:
        await page.wait_for_load_state("networkidle", timeout=15_000)
    except Exception:
        print("  ⏳  Network idle timeout — continuing anyway")

    # Wait for JS frameworks (Next.js, etc.) to finish hydrating
    try:
        await page.wait_for_function(
            "() => document.readyState === 'complete' && "
            "!document.querySelector('#__next[data-reactroot]') || "
            "document.readyState === 'complete'",
            timeout=10_000,
        )
    except Exception:
        pass

    await page.wait_for_timeout(3000)


async def get_snapshot(page: Page) -> str:
    """Get the accessibility tree snapshot for the current page."""
    try:
        tree_text = await page.locator("body").aria_snapshot()
    except Exception as e:
        tree_text = f"[Error getting accessibility tree: {e}]"

    if len(tree_text) > MAX_SNAPSHOT_CHARS:
        tree_text = tree_text[:MAX_SNAPSHOT_CHARS] + "\n…[truncated]"

    return tree_text


# ── Action execution ─────────────────────────────────────────────────────────

def _resolve_locator(page: Page, target: dict):
    """Turn a target dict into a Playwright locator."""
    if "role" in target and "name" in target:
        return page.get_by_role(target["role"], name=target["name"])
    elif "text" in target:
        return page.get_by_text(target["text"], exact=False)
    elif "label" in target:
        return page.get_by_label(target["label"])
    elif "placeholder" in target:
        return page.get_by_placeholder(target["placeholder"])
    else:
        raise ValueError(f"Cannot resolve target: {target}")


async def execute_action(page: Page, action: dict) -> str | None:
    """Execute a single action on the page. Returns an answer string or None."""
    act = action.get("action")

    if act == "answer":
        return action.get("text", "")

    elif act == "click":
        target = action.get("target", {})
        locator = _resolve_locator(page, target)
        await locator.first.click(timeout=5000)

    elif act == "fill":
        target = action.get("target", {})
        text = action.get("text", "")
        submit = action.get("submit", False)
        locator = _resolve_locator(page, target)
        await locator.first.fill(text)
        if submit:
            await locator.first.press("Enter")

    else:
        print(f"  ⚠️  Unknown action: {act}")

    # Wait for page to settle, then fixed delay between interactions
    try:
        await page.wait_for_load_state("networkidle", timeout=5_000)
    except Exception:
        pass
    await page.wait_for_timeout(ACTION_DELAY)
    return None


# ── Screenshot ────────────────────────────────────────────────────────────────

SCREENSHOTS_DIR = Path("screenshots")


async def take_screenshot(page: Page, label: str = "exit") -> str:
    """Save a screenshot of the current page. Returns the file path."""
    SCREENSHOTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = SCREENSHOTS_DIR / f"{label}_{timestamp}.png"
    await page.screenshot(path=str(filename), full_page=True)
    print(f"  📸  Screenshot saved: {filename}")
    return str(filename)

