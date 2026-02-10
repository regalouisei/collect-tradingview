"""Batch scraper: Extract Pine Script source from TradingView using Playwright.

Uses exported session cookies for authentication.
Saves .pine files directly to disk — no MCP size limits.

Usage:
    python scripts/batch_scraper.py --category editors_picks
    python scripts/batch_scraper.py --all
    python scripts/batch_scraper.py --urls scripts/urls_editors_picks.json
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).parent.parent
PINE_DIR = PROJECT_ROOT / "pinescript"
COOKIES_FILE = PROJECT_ROOT / "results" / ".tv_cookies.json"
STATE_FILE = PROJECT_ROOT / "results" / ".scrape_state.json"

CATEGORY_URLS = {
    "editors_picks": "https://www.tradingview.com/scripts/editors-picks/",
    "top": "https://www.tradingview.com/scripts/?sort=top",
    "trending": "https://www.tradingview.com/scripts/?sort=trending",
    "oscillators": "https://www.tradingview.com/scripts/oscillators/",
    "trend_analysis": "https://www.tradingview.com/scripts/trendanalysis/",
    "volume": "https://www.tradingview.com/scripts/volume/",
    "moving_averages": "https://www.tradingview.com/scripts/movingaverage/",
    "volatility": "https://www.tradingview.com/scripts/volatility/",
    "momentum": "https://www.tradingview.com/scripts/momentum/",
}


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:80]


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"scraped": [], "failed": []}


def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def collect_script_urls(page, category: str, limit: int = 0) -> list[dict]:
    """Scroll through a category page and collect all script URLs."""
    url = CATEGORY_URLS[category]
    print(f"\nCollecting scripts from {category}: {url}")
    page.goto(url, wait_until="networkidle", timeout=30000)
    time.sleep(2)

    # Dismiss any popups
    try:
        dont_need = page.locator("button:has-text('Don\\'t need')")
        if dont_need.is_visible(timeout=3000):
            dont_need.click()
            time.sleep(1)
    except Exception:
        pass

    # Scroll to load more scripts — detect when no new content loads
    max_scrolls = 50
    no_new_count = 0
    prev_height = 0
    for i in range(max_scrolls):
        current_height = page.evaluate("document.body.scrollHeight")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)
        new_height = page.evaluate("document.body.scrollHeight")
        if new_height == current_height:
            no_new_count += 1
            if no_new_count >= 3:
                print(f"    Scroll stopped after {i+1} scrolls (no new content)")
                break
        else:
            no_new_count = 0

    # Extract script links
    scripts = page.evaluate("""() => {
        const links = document.querySelectorAll('a[href*="/script/"]');
        const seen = new Set();
        const results = [];
        for (const link of links) {
            const href = link.getAttribute('href');
            const name = link.textContent?.trim();
            if (!href || seen.has(href) || !name || name.length < 5) continue;
            if (href.includes('/script/')) {
                seen.add(href);
                results.push({
                    name: name.substring(0, 100),
                    url: href.startsWith('/') ? 'https://www.tradingview.com' + href : href
                });
            }
        }
        return results;
    }""")

    if limit > 0:
        scripts = scripts[:limit]

    print(f"  Found {len(scripts)} scripts")
    return scripts


def extract_pine_source(page, script_url: str) -> str | None:
    """Navigate to a script page and extract Pine Script source code."""
    try:
        page.goto(script_url, wait_until="networkidle", timeout=20000)
        time.sleep(1)

        # Check if it's open source
        is_open = page.evaluate("""() => {
            return document.body.textContent.includes('OPEN-SOURCE SCRIPT') ||
                   document.body.textContent.includes('Open-source script');
        }""")

        if not is_open:
            return None  # Closed source

        # Click "Source code" tab
        try:
            source_tab = page.locator('button:has-text("Source code"), [role="tab"]:has-text("Source code")')
            if source_tab.is_visible(timeout=3000):
                source_tab.click()
                time.sleep(2)
        except Exception:
            pass

        # Extract code from the code container
        code = page.evaluate("""() => {
            // Find the smallest element containing //@version
            let bestMatch = null;
            let bestSize = Infinity;

            const walker = document.createTreeWalker(
                document.body, NodeFilter.SHOW_ELEMENT, null
            );

            let node;
            while (node = walker.nextNode()) {
                const text = node.innerText;
                if (!text || !text.includes('//@version')) continue;
                if (text.length > 500000) continue;

                if (text.includes('indicator(') || text.includes('strategy(') || text.includes('library(')) {
                    // Make sure it doesn't include nav elements
                    const hasNav = text.includes('Products') && text.includes('Brokers');
                    if (!hasNav && text.length < bestSize) {
                        bestSize = text.length;
                        bestMatch = text;
                    }
                }
            }

            return bestMatch;
        }""")

        if code:
            # Clean up non-breaking spaces
            code = code.replace("\u00a0", " ")
            return code

        return None

    except Exception as e:
        print(f"    Error: {e}")
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", choices=list(CATEGORY_URLS.keys()))
    parser.add_argument("--all", action="store_true", help="Scrape all categories")
    parser.add_argument("--urls", type=str, help="JSON file with script URLs")
    parser.add_argument("--save-category", type=str, default="custom", help="Category folder when using --urls")
    parser.add_argument("--limit", type=int, default=0, help="Max scripts per category")
    parser.add_argument("--headed", action="store_true", help="Show browser")
    parser.add_argument("--incremental", action="store_true", help="Skip scripts already in state file or on disk")
    args = parser.parse_args()

    # Load cookies
    if not COOKIES_FILE.exists():
        print(f"ERROR: No cookies file at {COOKIES_FILE}")
        print("Export cookies from the MCP browser session first.")
        sys.exit(1)

    cookies = json.loads(COOKIES_FILE.read_text())
    state = load_state()

    print("DeepStack TradingView Batch Scraper")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        )

        # Set cookies
        context.add_cookies(cookies)
        page = context.new_page()

        # Determine what to scrape
        if args.urls:
            # Load pre-collected URLs
            with open(args.urls) as f:
                script_lists = {args.save_category: json.load(f)}
        elif args.all:
            script_lists = {}
            for cat in CATEGORY_URLS:
                script_lists[cat] = collect_script_urls(page, cat, limit=args.limit)
        elif args.category:
            script_lists = {args.category: collect_script_urls(page, args.category, limit=args.limit)}
        else:
            print("Specify --category, --all, or --urls")
            sys.exit(1)

        # Save collected URLs for reference
        for cat, scripts in script_lists.items():
            urls_file = PROJECT_ROOT / "scripts" / f"urls_{cat}.json"
            urls_file.write_text(json.dumps(scripts, indent=2))
            print(f"Saved {len(scripts)} URLs to {urls_file.name}")

        # Process each script
        total_saved = 0
        total_skipped = 0
        total_closed = 0

        for category, scripts in script_lists.items():
            print(f"\n{'='*60}")
            print(f"Category: {category} ({len(scripts)} scripts)")
            print(f"{'='*60}")

            cat_dir = PINE_DIR / category
            cat_dir.mkdir(parents=True, exist_ok=True)

            for i, script in enumerate(scripts, 1):
                name = script["name"]
                url = script["url"]
                slug = slugify(name)

                pine_path = cat_dir / f"{slug}.pine"

                # Skip if already scraped (state or file on disk)
                if args.incremental:
                    if url in state["scraped"] or pine_path.exists():
                        if pine_path.exists() and url not in state["scraped"]:
                            state["scraped"].append(url)
                            save_state(state)
                        total_skipped += 1
                        continue

                print(f"\n  [{i}/{len(scripts)}] {name[:60]}")

                code = extract_pine_source(page, url)

                if code:
                    pine_path.write_text(code, encoding="utf-8")
                    lines = code.count("\n") + 1
                    print(f"    Saved: {slug}.pine ({lines} lines)")
                    state["scraped"].append(url)
                    total_saved += 1
                else:
                    print(f"    Skipped (closed source or extraction failed)")
                    state["scraped"].append(url)
                    total_closed += 1

                save_state(state)
                time.sleep(0.5)  # Rate limit

        browser.close()

    print(f"\n{'='*60}")
    print(f"Scraping complete:")
    print(f"  Saved: {total_saved}")
    print(f"  Skipped (already done): {total_skipped}")
    print(f"  Closed source / failed: {total_closed}")


if __name__ == "__main__":
    main()
