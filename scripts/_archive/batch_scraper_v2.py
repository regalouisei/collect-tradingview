"""Batch scraper v2 - Fixed hash loading bug.

Bug Fix:
- Fixed: load_hashes() now properly handles both list and dict formats
- Fixed: is_duplicate() safely checks hash existence
- Added: Hash file validation and auto-correction

Usage:
    python scripts/batch_scraper_v2.py --all --limit 200 --aggressive
    python scripts/batch_scraper_v2.py --category editors_picks --limit 100
"""

import argparse
import json
import re
import sys
import time
import random
from pathlib import Path
from datetime import datetime

from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).parent.parent
PINE_DIR = PROJECT_ROOT / "pinescript"
COOKIES_FILE = PROJECT_ROOT / "results" / ".tv_cookies.json"
STATE_FILE = PROJECT_ROOT / "results" / ".scrape_state_v2.json"
HASHES_FILE = PROJECT_ROOT / "results" / ".script_hashes_v2.json"

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

# 分类优先级
PRIORITY_CATEGORIES = {
    "high": ["editors_picks", "top", "trending"],
    "medium": ["momentum", "oscillators", "trend_analysis"],
    "low": ["volume", "moving_averages", "volatility"],
}


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:80]


def load_hashes() -> dict:
    """Load script content hashes for deduplication (FIXED)."""
    if not HASHES_FILE.exists():
        print(f"Hashes file not found, creating new one: {HASHES_FILE}")
        return {}

    try:
        content = HASHES_FILE.read_text()
        if not content.strip():
            print(f"Hashes file is empty, creating new one")
            return {}

        data = json.loads(content)

        # Fix: Handle both list and dict formats
        if isinstance(data, list):
            print(f"⚠️  Hashes file is a list (should be dict). Converting...")
            # Convert list to dict
            hashes = {}
            for item in data:
                if isinstance(item, dict):
                    hashes.update(item)
                elif isinstance(item, str):
                    hashes[item] = item  # Simple hash
            print(f"   Converted {len(hashes)} hashes from list to dict")
            # Save corrected version
            save_hashes(hashes)
            return hashes
        elif isinstance(data, dict):
            print(f"✅ Hashes loaded: {len(data)} entries")
            return data
        else:
            print(f"⚠️  Unknown hashes format: {type(data)}. Resetting...")
            return {}

    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse hashes file: {e}")
        return {}
    except Exception as e:
        print(f"❌ Error loading hashes: {e}")
        return {}


def save_hashes(hashes: dict):
    """Save script content hashes."""
    if not isinstance(hashes, dict):
        print(f"⚠️  Warning: hashes is not a dict, got {type(hashes)}")
        hashes = {}

    HASHES_FILE.parent.mkdir(parents=True, exist_ok=True)
    HASHES_FILE.write_text(json.dumps(hashes, indent=2))
    print(f"💾 Saved {len(hashes)} hashes to {HASHES_FILE}")


def compute_content_hash(pine_code: str) -> str:
    """Compute SHA256 hash of Pine Script content."""
    import hashlib
    return hashlib.sha256(pine_code.encode('utf-8')).hexdigest()


def is_duplicate(pine_code: str, hashes: dict) -> bool:
    """Check if script content is a duplicate (FIXED)."""
    if not isinstance(hashes, dict):
        print(f"⚠️  Warning: hashes is not a dict, got {type(hashes)}")
        return False

    content_hash = compute_content_hash(pine_code)
    return content_hash in hashes.values()


def load_state() -> dict:
    """Load scraping state."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"scraped": [], "failed": [], "last_run": None, "total_scraped": 0}


def save_state(state: dict):
    """Save scraping state."""
    state["last_run"] = datetime.now().isoformat()
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def collect_script_urls(page, category: str, limit: int = 0, aggressive: bool = False,
                        random_delay: tuple = (1, 2)) -> list[dict]:
    """Scroll through a category page and collect all script URLs."""
    url = CATEGORY_URLS[category]
    print(f"\nCollecting scripts from {category}: {url}")
    page.goto(url, wait_until="networkidle", timeout=30000)
    time.sleep(random.choice(random_delay))

    # Dismiss any popups
    try:
        dont_need = page.locator("button:has-text('Don\\'t need')")
        if dont_need.is_visible(timeout=3000):
            dont_need.click()
            time.sleep(1)
    except Exception:
        pass

    max_scrolls = 200 if aggressive else 120
    no_new_threshold = 7 if aggressive else 5
    scroll_delay = 1 if aggressive else 2

    print(f"    Aggressive mode: {aggressive} (max_scrolls={max_scrolls}, threshold={no_new_threshold})")
    print(f"    Scroll delay: {scroll_delay} seconds")
    print(f"    Random delay: {random_delay} seconds")

    prev_height = 0
    no_new_count = 0
    prev_script_count = 0

    for i in range(max_scrolls):
        current_height = page.evaluate("document.body.scrollHeight")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(scroll_delay)
        time.sleep(random.choice(random_delay))
        new_height = page.evaluate("document.body.scrollHeight")

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
                        url: (typeof href === 'string' \&\& href.startsWith('/')) ? 'https://www.tradingview.com' + href : href
                    });
                }
            }
            return results;
        }""")

        current_script_count = len(scripts)

        if new_height == current_height:
            no_new_count += 1
            if no_new_count >= no_new_threshold:
                print(f"    Scroll stopped after {i+1} scrolls (no new content for {no_new_threshold} consecutive scrolls)")
                break
        elif current_script_count == prev_script_count:
            no_new_count = 0

        prev_height = new_height
        prev_script_count = current_script_count

    print(f"  Found {len(scripts)} scripts")

    if limit > 0:
        scripts = scripts[:limit]

    return scripts


def extract_pine_source(page, script_url: str, max_retries: int = 2) -> str | None:
    """Navigate to a script page and extract Pine Script source code."""
    for attempt in range(max_retries):
        try:
            page.goto(script_url, wait_until="networkidle", timeout=20000)
            time.sleep(random.uniform(0.5, 1.5))

            is_open = page.evaluate("""() => {
                return document.body.textContent.includes('OPEN-SOURCE SCRIPT') ||
                       document.body.textContent.includes('Open-source script');
            }""")

            if not is_open:
                return None

            try:
                source_tab = page.locator('button:has-text("Source code"), [role="tab"]:has-text("Source code")')
                if source_tab.is_visible(timeout=2000):
                    source_tab.click()
                    time.sleep(1)
            except Exception:
                pass

            code = page.evaluate("""() => {
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
                code = code.replace("\u00a0", " ")
                return code

            return None

        except Exception as e:
            print(f"    Retry {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                time.sleep(random.uniform(2, 5))
            continue

    return None


def scrape_category(
    category: str,
    limit: int,
    aggressive: bool,
    cookies: list,
    skip_already_scraped: bool = True,
    random_delay: tuple = (1, 2)
) -> dict:
    """Scrape a single category."""
    print(f"\n{'='*60}")
    print(f"Category: {category}")
    print(f"{'='*60}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        )
        context.add_cookies(cookies)
        page = context.new_page()

        try:
            scripts = collect_script_urls(page, category, limit, aggressive, random_delay)

            state = load_state()
            hashes = load_hashes()
            category_dir = PINE_DIR / category
            category_dir.mkdir(parents=True, exist_ok=True)

            results = {
                "saved": 0,
                "skipped": 0,
                "duplicate": 0,
                "closed": 0,
                "failed": 0,
                "scripts": []
            }

            for i, script in enumerate(scripts, 1):
                name = script["name"]
                url = script["url"]
                slug = slugify(name)
                pine_path = category_dir / f"{slug}.pine"

                print(f"\n  [{i}/{len(scripts)}] {name[:60]}")

                if skip_already_scraped and (url in state["scraped"] or pine_path.exists()):
                    print(f"    Skipped (already done)")
                    results["skipped"] += 1
                    results["scripts"].append({"name": name, "url": url, "status": "skipped"})
                    continue

                code = extract_pine_source(page, url)
                if code is None:
                    print(f"    Skipped (closed source or extraction failed)")
                    results["closed"] += 1
                    results["scripts"].append({"name": name, "url": url, "status": "closed"})
                    continue

                if is_duplicate(code, hashes):
                    print(f"    Skipped (duplicate content)")
                    results["duplicate"] += 1
                    results["scripts"].append({"name": name, "url": url, "status": "duplicate"})
                    continue

                lines = code.count("\n") + 1
                pine_path.write_text(code, encoding='utf-8')
                print(f"    Saved: {slug}.pine ({lines} lines)")

                content_hash = compute_content_hash(code)
                hashes[slug] = content_hash
                save_hashes(hashes)

                state["scraped"].append(url)
                state["total_scraped"] = state.get("total_scraped", 0) + 1

                results["saved"] += 1
                results["scripts"].append({"name": name, "url": url, "status": "saved"})

            return results

        finally:
            browser.close()


def scrape_categories(
    categories: list[str],
    limit_per_category: int,
    aggressive: bool,
    skip_already_scraped: bool = True,
    random_delay: tuple = (1, 2)
) -> dict:
    """Scrape multiple categories with priority."""
    print("=" * 60)
    print("Batch Scraper v2 - Fixed Hash Loading")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  Categories: {', '.join(categories)}")
    print(f"  Limit per category: {limit_per_category}")
    print(f"  Aggressive mode: {aggressive}")
    print(f"  Skip already scraped: {skip_already_scraped}")
    print(f"  Random delay: {random_delay}")

    high_priority_cats = []
    medium_priority_cats = []
    low_priority_cats = []

    for cat in categories:
        if cat in PRIORITY_CATEGORIES["high"]:
            high_priority_cats.append(cat)
        elif cat in PRIORITY_CATEGORIES["medium"]:
            medium_priority_cats.append(cat)
        elif cat in PRIORITY_CATEGORIES["low"]:
            low_priority_cats.append(cat)

    print(f"\nPriority Distribution:")
    print(f"  High: {', '.join(high_priority_cats)}")
    print(f"  Medium: {', '.join(medium_priority_cats)}")
    print(f"  Low: {', '.join(low_priority_cats)}")

    if not COOKIES_FILE.exists():
        print(f"\nERROR: No cookies file at {COOKIES_FILE}")
        return {"error": "No cookies file"}

    cookies = json.loads(COOKIES_FILE.read_text())
    print(f"\n✅ Cookies loaded ({len(cookies)} cookies)")

    state = load_state()
    hashes = load_hashes()
    print(f"✅ State loaded (total scraped: {state.get('total_scraped', 0)})")

    all_results = {}

    for priority, cat_list in [("high", high_priority_cats), ("medium", medium_priority_cats), ("low", low_priority_cats)]:
        print(f"\n{'='*60}")
        print(f"Priority: {priority.upper()} ({len(cat_list)} categories)")
        print(f"{'='*60}")

        for cat in cat_list:
            print(f"\nProcessing: {cat}")

            try:
                results = scrape_category(
                    category=cat,
                    limit=limit_per_category,
                    aggressive=aggressive,
                    cookies=cookies,
                    skip_already_scraped=skip_already_scraped,
                    random_delay=random_delay
                )
                all_results[cat] = results
                save_state(state)

                print(f"\n  Summary for {cat}:")
                print(f"    Saved: {results['saved']}")
                print(f"    Skipped: {results['skipped']}")
                print(f"    Duplicate: {results['duplicate']}")
                print(f"    Closed: {results['closed']}")
                print(f"    Failed: {results['failed']}")

            except Exception as e:
                print(f"\n❌ ERROR in {cat}: {e}")
                import traceback
                traceback.print_exc()
                all_results[cat] = {"error": str(e)}

    print("\n" + "=" * 60)
    print("SCRAPING COMPLETE")
    print("=" * 60)

    total_saved = sum(r.get("saved", 0) for r in all_results.values() if isinstance(r, dict))
    total_skipped = sum(r.get("skipped", 0) for r in all_results.values() if isinstance(r, dict))
    total_duplicate = sum(r.get("duplicate", 0) for r in all_results.values() if isinstance(r, dict))
    total_closed = sum(r.get("closed", 0) for r in all_results.values() if isinstance(r, dict))
    total_failed = sum(r.get("failed", 0) for r in all_results.values() if isinstance(r, dict))

    print(f"\nTotal across all categories:")
    print(f"  Saved (new):     {total_saved}")
    print(f"  Skipped (done):  {total_skipped}")
    print(f"  Duplicate:       {total_duplicate}")
    print(f"  Closed source:   {total_closed}")
    print(f"  Failed:          {total_failed}")
    print(f"  Total in state:  {state.get('total_scraped', 0)}")

    return all_results


def main():
    parser = argparse.ArgumentParser(description="Batch scraper v2 for TradingView")
    parser.add_argument("--category", choices=list(CATEGORY_URLS.keys()))
    parser.add_argument("--all", action="store_true", help="Scrape all categories")
    parser.add_argument("--categories", nargs="+", choices=list(CATEGORY_URLS.keys()))
    parser.add_argument("--limit", type=int, default=0, help="Max scripts per category")
    parser.add_argument("--aggressive", action="store_true", help="Faster scrolling")
    args = parser.parse_args()

    if args.all:
        categories = list(CATEGORY_URLS.keys())
    elif args.categories:
        categories = args.categories
    elif args.category:
        categories = [args.category]
    else:
        print("Please specify --category, --categories, or --all")
        sys.exit(1)

    results = scrape_categories(
        categories=categories,
        limit_per_category=args.limit,
        aggressive=args.aggressive,
        skip_already_scraped=True,
        random_delay=(1, 2),
    )


if __name__ == "__main__":
    main()
