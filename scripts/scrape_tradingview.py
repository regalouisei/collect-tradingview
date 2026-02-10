"""TradingView Community Scripts Scraper using Playwright.

This script navigates TradingView's community scripts pages and extracts
Pine Script source code from open-source indicators and strategies.

Usage:
    python scripts/scrape_tradingview.py                    # Scrape all categories
    python scripts/scrape_tradingview.py --category top     # Only scrape 'top'
    python scripts/scrape_tradingview.py --limit 10         # Max 10 per category
    python scripts/scrape_tradingview.py --headed           # Show browser window

Requirements:
    - playwright installed: pip install playwright && playwright install chromium
    - TradingView account logged in (script will pause for manual login if needed)
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, Page, Browser

PROJECT_ROOT = Path(__file__).parent.parent
PINE_DIR = PROJECT_ROOT / "pinescript"

# TradingView script listing URLs
CATEGORY_URLS = {
    "editors_picks": "https://www.tradingview.com/scripts/editors-picks/",
    "top": "https://www.tradingview.com/scripts/?sort=top",
    "trending": "https://www.tradingview.com/scripts/?sort=trending",
}

# Tracks what we've already scraped
STATE_FILE = PROJECT_ROOT / "results" / ".scrape_state.json"


def load_state() -> dict:
    """Load scraping state (which scripts have been scraped)."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"scraped": []}


def save_state(state: dict) -> None:
    """Persist scraping state."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def slugify(name: str) -> str:
    """Convert script name to a safe filename slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug[:80]  # Limit length


def wait_for_login(page: Page) -> None:
    """Pause and wait for user to log in if not already authenticated."""
    # Check if logged in by looking for user menu
    try:
        page.wait_for_selector('[data-name="user-menu"]', timeout=5000)
        print("  Already logged in.")
    except Exception:
        print("\n" + "=" * 60)
        print("  Please log in to TradingView in the browser window.")
        print("  Press Enter here when done...")
        print("=" * 60)
        input()
        page.wait_for_selector('[data-name="user-menu"]', timeout=30000)
        print("  Login detected.")


def scrape_script_list(page: Page, category: str, limit: int = 0) -> list[dict]:
    """Scrape the list of scripts from a category page.

    Returns list of dicts with keys: name, url, author
    """
    url = CATEGORY_URLS[category]
    print(f"\n  Navigating to {category}: {url}")
    page.goto(url, wait_until="networkidle", timeout=30000)
    time.sleep(2)

    scripts = []
    scroll_count = 0
    max_scrolls = 50  # Safety limit

    while True:
        # Find script cards on the page
        cards = page.query_selector_all('[class*="card-"]')
        if not cards:
            # Try alternative selectors
            cards = page.query_selector_all('div[data-widget-type="script"]')
        if not cards:
            cards = page.query_selector_all('.tv-feed__item')

        for card in cards:
            try:
                link = card.query_selector('a[href*="/script/"]')
                if not link:
                    continue
                href = link.get_attribute("href")
                name = link.inner_text().strip()
                if not name or not href:
                    continue

                # Make absolute URL
                if href.startswith("/"):
                    href = f"https://www.tradingview.com{href}"

                script_id = href.split("/script/")[-1].rstrip("/")
                if script_id not in [s.get("id") for s in scripts]:
                    scripts.append({
                        "name": name,
                        "url": href,
                        "id": script_id,
                    })
            except Exception:
                continue

        # Check if we have enough
        if limit > 0 and len(scripts) >= limit:
            scripts = scripts[:limit]
            break

        # Scroll to load more
        scroll_count += 1
        if scroll_count >= max_scrolls:
            break

        prev_count = len(scripts)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1.5)

        # If no new scripts loaded after scroll, we're done
        new_cards = page.query_selector_all('[class*="card-"]')
        if len(new_cards) <= len(cards) and scroll_count > 3:
            break

    print(f"  Found {len(scripts)} scripts in {category}")
    return scripts


def scrape_pine_source(page: Page, script_url: str) -> str | None:
    """Navigate to a script page and extract the Pine Script source code.

    Returns the source code string, or None if not available (closed source).
    """
    try:
        page.goto(script_url, wait_until="networkidle", timeout=20000)
        time.sleep(1)

        # Look for the source code section
        # TradingView shows source in a code editor or pre block
        source_selectors = [
            '.pine-editor-view',
            '[class*="sourceCode"]',
            'pre.pine',
            '.tv-chart-view__source-code',
            '[data-name="pine-editor"]',
            'code',
        ]

        for selector in source_selectors:
            elements = page.query_selector_all(selector)
            for el in elements:
                text = el.inner_text().strip()
                if text and ("indicator(" in text or "strategy(" in text or "//@version" in text):
                    return text

        # Try clicking a "Source Code" or "Open Source" button/tab
        source_buttons = page.query_selector_all('button, [role="tab"]')
        for btn in source_buttons:
            btn_text = btn.inner_text().lower()
            if "source" in btn_text or "code" in btn_text:
                btn.click()
                time.sleep(1)
                # Re-check for source code
                for selector in source_selectors:
                    elements = page.query_selector_all(selector)
                    for el in elements:
                        text = el.inner_text().strip()
                        if text and len(text) > 50:
                            return text

        return None  # Closed source or couldn't find it

    except Exception as e:
        print(f"    Error scraping source: {e}")
        return None


def save_pine_script(pine_code: str, script_name: str, category: str) -> Path:
    """Save Pine Script to the appropriate category folder."""
    cat_dir = PINE_DIR / category
    cat_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{slugify(script_name)}.pine"
    filepath = cat_dir / filename
    filepath.write_text(pine_code, encoding="utf-8")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="TradingView Community Scripts Scraper")
    parser.add_argument("--category", choices=list(CATEGORY_URLS.keys()), help="Scrape only this category")
    parser.add_argument("--limit", type=int, default=0, help="Max scripts per category (0=all)")
    parser.add_argument("--headed", action="store_true", help="Show browser window")
    args = parser.parse_args()

    categories = [args.category] if args.category else list(CATEGORY_URLS.keys())
    state = load_state()

    print("OpenClaw TradingView Scraper")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        )
        page = context.new_page()

        # Navigate to TradingView and ensure logged in
        page.goto("https://www.tradingview.com/", wait_until="networkidle")
        wait_for_login(page)

        total_scraped = 0
        total_skipped = 0

        for category in categories:
            print(f"\n{'='*60}")
            print(f"Category: {category}")
            print(f"{'='*60}")

            # Get script list
            scripts = scrape_script_list(page, category, limit=args.limit)

            for i, script in enumerate(scripts, 1):
                script_id = script["id"]

                # Skip if already scraped
                if script_id in state["scraped"]:
                    total_skipped += 1
                    continue

                print(f"\n  [{i}/{len(scripts)}] {script['name']}")

                # Scrape source code
                pine_code = scrape_pine_source(page, script["url"])

                if pine_code:
                    filepath = save_pine_script(pine_code, script["name"], category)
                    print(f"    Saved: {filepath.name} ({len(pine_code)} chars)")
                    state["scraped"].append(script_id)
                    save_state(state)
                    total_scraped += 1
                else:
                    print(f"    Skipped (closed source or not found)")
                    state["scraped"].append(script_id)  # Don't retry
                    save_state(state)
                    total_skipped += 1

                # Rate limit
                time.sleep(1)

        browser.close()

    print(f"\n{'='*60}")
    print(f"Scraping complete: {total_scraped} saved, {total_skipped} skipped")
    print(f"Pine scripts in: {PINE_DIR}")


if __name__ == "__main__":
    main()
