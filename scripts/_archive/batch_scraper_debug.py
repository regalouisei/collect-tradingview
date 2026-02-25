"""Enhanced batch scraper with DEBUG LOGGING.

Features:
- Detailed debug logging at every step
- Progress tracking with timestamps
- Error logging with stack traces
- Status reporting to both stdout and file

Usage:
    python scripts/batch_scraper_debug.py --all --limit 100 --aggressive --workers 4
"""

import argparse
import json
import os
import re
import sys
import time
import random
import traceback
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).parent.parent
PINE_DIR = PROJECT_ROOT / "pinescript"
COOKIES_FILE = PROJECT_ROOT / "results" / ".tv_cookies.json"
STATE_FILE = PROJECT_ROOT / "results" / ".scrape_state_debug.json"
HASHES_FILE = PROJECT_ROOT / "results" / ".script_hashes_debug.json"
DEBUG_LOG_FILE = PROJECT_ROOT / "logs" / "scraper_debug.log"

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


def debug_log(message: str, level: str = "INFO"):
    """Write debug message to both stdout and log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {message}"

    # Print to stdout
    print(log_line)

    # Write to log file
    try:
        DEBUG_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(DEBUG_LOG_FILE, "a", encoding='utf-8') as f:
            f.write(log_line + "\n")
    except Exception as e:
        print(f"[ERROR] Failed to write to log file: {e}")


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:80]


def load_hashes() -> dict:
    """Load script content hashes for deduplication."""
    debug_log("Loading script hashes...")
    if HASHES_FILE.exists():
        try:
            hashes = json.loads(HASHES_FILE.read_text())
            debug_log(f"Loaded {len(hashes)} hashes from {HASHES_FILE}")
            return hashes
        except Exception as e:
            debug_log(f"Error loading hashes: {e}", "ERROR")
            return {}
    else:
        debug_log("No hashes file found, starting fresh", "WARNING")
        return {}


def save_hashes(hashes: dict):
    """Save script content hashes."""
    debug_log(f"Saving {len(hashes)} hashes to {HASHES_FILE}...")
    try:
        HASHES_FILE.parent.mkdir(parents=True, exist_ok=True)
        HASHES_FILE.write_text(json.dumps(hashes, indent=2))
        debug_log("Hashes saved successfully")
    except Exception as e:
        debug_log(f"Error saving hashes: {e}", "ERROR")


def compute_content_hash(pine_code: str) -> str:
    """Compute SHA256 hash of Pine Script content."""
    import hashlib
    return hashlib.sha256(pine_code.encode('utf-8')).hexdigest()


def is_duplicate(pine_code: str, hashes: dict) -> bool:
    """Check if script content is a duplicate."""
    content_hash = compute_content_hash(pine_code)
    is_dup = content_hash in hashes.values()
    if is_dup:
        debug_log(f"Content hash {content_hash[:16]}... is duplicate")
    return is_dup


def load_state() -> dict:
    """Load scraping state."""
    debug_log("Loading scrape state...")
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text())
            debug_log(f"Loaded state with {len(state.get('scraped', []))} scraped scripts, total: {state.get('total_scraped', 0)}")
            return state
        except Exception as e:
            debug_log(f"Error loading state: {e}", "ERROR")
            return {"scraped": [], "failed": [], "last_run": None, "total_scraped": 0}
    else:
        debug_log("No state file found, starting fresh", "INFO")
        return {"scraped": [], "failed": [], "last_run": None, "total_scraped": 0}


def save_state(state: dict):
    """Save scraping state."""
    debug_log(f"Saving state with {len(state.get('scraped', []))} scraped scripts, total: {state.get('total_scraped', 0)}...")
    try:
        state["last_run"] = datetime.now().isoformat()
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, indent=2))
        debug_log("State saved successfully")
    except Exception as e:
        debug_log(f"Error saving state: {e}", "ERROR")


def collect_script_urls(page, category: str, limit: int = 0, aggressive: bool = False, 
                            random_delay: tuple = (1, 2)) -> list[dict]:
    """Scroll through a category page and collect all script URLs (debugged)."""
    url = CATEGORY_URLS[category]
    debug_log(f"Navigating to {category}: {url}")

    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
        debug_log("Page loaded successfully")
        time.sleep(random.choice(random_delay))
    except Exception as e:
        debug_log(f"Error navigating to page: {e}", "ERROR")
        return []

    # Dismiss any popups
    try:
        dont_need = page.locator('button:has-text("Don\\'t need")')
        if dont_need.is_visible(timeout=3000):
            debug_log("Dismissing popup...")
            dont_need.click()
            time.sleep(1)
    except Exception as e:
        debug_log(f"No popup to dismiss: {e}", "DEBUG")

    # Enhanced scrolling parameters
    max_scrolls = 80 if aggressive else 50
    no_new_threshold = 2 if aggressive else 3
    scroll_delay = 0.5 if aggressive else 1

    debug_log(f"Scroll parameters: max_scrolls={max_scrolls}, no_new_threshold={no_new_threshold}, scroll_delay={scroll_delay}")

    prev_height = 0
    no_new_count = 0
    prev_script_count = 0

    for i in range(max_scrolls):
        current_height = page.evaluate("document.body.scrollHeight")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(scroll_delay)
        new_height = page.evaluate("document.body.scrollHeight")

        # Check for new scripts
        try:
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
        except Exception as e:
            debug_log(f"Error extracting scripts: {e}", "ERROR")
            scripts = []

        current_script_count = len(scripts)
        debug_log(f"Scroll {i+1}/{max_scrolls}: found {current_script_count} scripts (new: {current_script_count - prev_script_count})")

        if new_height == current_height:
            no_new_count += 1
            debug_log(f"No new content for {no_new_count} consecutive scrolls")
            if no_new_count >= no_new_threshold:
                debug_log(f"Stopping after {i+1} scrolls (no new content for {no_new_threshold} consecutive scrolls)")
                break
        elif current_script_count == prev_script_count:
            # New scripts detected, reset counter
            no_new_count = 0
            debug_log("New scripts detected, resetting no_new counter")

        prev_height = new_height
        prev_script_count = current_script_count

    debug_log(f"Collected {len(scripts)} scripts total")

    if limit > 0:
        scripts = scripts[:limit]

    return scripts


def extract_pine_source(page, script_url: str, max_retries: int = 2) -> str | None:
    """Navigate to a script page and extract Pine Script source code (debugged)."""
    debug_log(f"Extracting source from: {script_url}")

    for attempt in range(max_retries):
        try:
            debug_log(f"Attempt {attempt+1}/{max_retries}: navigating to {script_url}")
            page.goto(script_url, wait_until="networkidle", timeout=20000)
            debug_log("Page loaded successfully")
            time.sleep(random.uniform(0.5, 1.5))

            # Check if it's open source
            try:
                is_open = page.evaluate("""() => {
                    return document.body.textContent.includes('OPEN-SOURCE SCRIPT') ||
                           document.body.textContent.includes('Open-source script');
                }""")
                debug_log(f"Open source check: {is_open}")
            except Exception as e:
                debug_log(f"Error checking open source: {e}", "WARNING")
                is_open = False

            if not is_open:
                debug_log("Not open source, skipping")
                return None

            # Click "Source code" tab
            try:
                source_tab = page.locator('button:has-text("Source code"), [role="tab"]:has-text("Source code")')
                if source_tab.is_visible(timeout=2000):
                    debug_log("Clicking Source code tab...")
                    source_tab.click()
                    time.sleep(1)
            except Exception as e:
                debug_log(f"No Source code tab: {e}", "DEBUG")

            # Extract code
            debug_log("Extracting Pine Script code...")
            try:
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
                    lines = code.count("\n") + 1
                    debug_log(f"Successfully extracted code ({lines} lines)")
                    # Clean up non-breaking spaces
                    code = code.replace("\u00a0", " ")
                    return code
                else:
                    debug_log("No code extracted from page", "ERROR")
                    return None

            except Exception as e:
                debug_log(f"Error extracting code: {e}", "ERROR")
                return None

        except Exception as e:
            debug_log(f"Attempt {attempt+1}/{max_retries} failed: {e}", "ERROR")
            traceback.print_exc()

            if attempt < max_retries - 1:
                debug_log(f"Waiting {random.uniform(2, 5)} seconds before retry...", "WARNING")
                time.sleep(random.uniform(2, 5))
                continue

    debug_log(f"Failed to extract code after {max_retries} attempts", "ERROR")
    return None


def scrape_category(
    category: str,
    limit: int,
    aggressive: bool,
    cookies: list,
    skip_already_scraped: bool = True,
    random_delay: tuple = (1, 2)
) -> dict:
    """Scrape a single category (debugged)."""
    debug_log("=" * 80)
    debug_log(f"Scraping category: {category}")
    debug_log("=" * 80)
    debug_log(f"Parameters: limit={limit}, aggressive={aggressive}, skip_already_scraped={skip_already_scraped}")

    with sync_playwright() as p:
        try:
            debug_log("Starting Playwright...")
            browser = p.chromium.launch(headless=True)
            debug_log("Playwright started successfully")
        except Exception as e:
            debug_log(f"Failed to launch Playwright: {e}", "ERROR")
            traceback.print_exc()
            return {"error": f"Failed to launch Playwright: {e}"}

        try:
            debug_log("Creating browser context...")
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            )
            debug_log("Context created successfully")
        except Exception as e:
            debug_log(f"Failed to create context: {e}", "ERROR")
            traceback.print_exc()
            return {"error": f"Failed to create context: {e}"}

        try:
            debug_log(f"Adding {len(cookies)} cookies to context...")
            context.add_cookies(cookies)
            debug_log("Cookies added successfully")
        except Exception as e:
            debug_log(f"Failed to add cookies: {e}", "ERROR")
            traceback.print_exc()
            return {"error": f"Failed to add cookies: {e}"}

        try:
            debug_log("Creating new page...")
            page = context.new_page()
            debug_log("Page created successfully")
        except Exception as e:
            debug_log(f"Failed to create page: {e}", "ERROR")
            traceback.print_exc()
            return {"error": f"Failed to create page: {e}"}

        try:
            # Collect script URLs
            debug_log("Collecting script URLs...")
            scripts = collect_script_urls(page, category, limit, aggressive, random_delay)

            if not scripts:
                debug_log("No scripts found, skipping category", "WARNING")
                return {
                    "saved": 0,
                    "skipped": 0,
                    "duplicate": 0,
                    "closed": 0,
                    "failed": 0,
                    "scripts": []
                }

            # Load state and hashes
            debug_log("Loading state and hashes...")
            state = load_state()
            hashes = load_hashes()

            category_dir = PINE_DIR / category
            debug_log(f"Category directory: {category_dir}")
            category_dir.mkdir(parents=True, exist_ok=True)
            debug_log(f"Category directory created")

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

                debug_log(f"\n{'='*80}")
                debug_log(f"[{i}/{len(scripts)}] Processing: {name[:60]}")
                debug_log(f"[{i}/{len(scripts)}] URL: {url}")
                debug_log(f"[{i}/{len(scripts)}] Path: {pine_path}")

                # Skip if already scraped
                if skip_already_scraped and (url in state["scraped"] or pine_path.exists()):
                    debug_log("  Skipped (already done)")
                    results["skipped"] += 1
                    results["scripts"].append({"name": name, "url": url, "status": "skipped"})
                    continue

                # Extract source code
                debug_log("  Extracting source code...")
                code = extract_pine_source(page, url)

                if code is None:
                    debug_log("  Skipped (closed source or extraction failed)")
                    results["closed"] += 1
                    results["scripts"].append({"name": name, "url": url, "status": "closed"})
                    continue

                # Check for duplicates
                debug_log("  Checking for duplicates...")
                if is_duplicate(code, hashes):
                    debug_log("  Skipped (duplicate content)")
                    results["duplicate"] += 1
                    results["scripts"].append({"name": name, "url": url, "status": "duplicate"})
                    continue

                # Save script
                debug_log("  Saving script to file...")
                try:
                    pine_path.write_text(code, encoding='utf-8')
                    lines = code.count("\n") + 1
                    debug_log(f"  Saved: {slug}.pine ({lines} lines)")

                    # Update state and hashes
                    content_hash = compute_content_hash(code)
                    hashes[slug] = content_hash
                    save_hashes(hashes)

                    state["scraped"].append(url)
                    state["total_scraped"] = state.get("total_scraped", 0) + 1
                    save_state(state)

                    results["saved"] += 1
                    results["scripts"].append({"name": name, "url": url, "status": "saved"})
                except Exception as e:
                    debug_log(f"  Failed to save script: {e}", "ERROR")
                    results["failed"] += 1
                    results["scripts"].append({"name": name, "url": url, "status": "failed"})
                    continue

            debug_log(f"\n{'='*80}")
            debug_log(f"Category {category} completed")
            debug_log(f"  Saved: {results['saved']}")
            debug_log(f"  Skipped: {results['skipped']}")
            debug_log(f"  Duplicate: {results['duplicate']}")
            debug_log(f"  Closed: {results['closed']}")
            debug_log(f"  Failed: {results['failed']}")
            return results

        except Exception as e:
            debug_log(f"Failed to scrape category {category}: {e}", "ERROR")
            traceback.print_exc()
            return {"error": f"Failed to scrape category {category}: {e}"}

        finally:
            try:
                debug_log("Closing browser...")
                browser.close()
                debug_log("Browser closed successfully")
            except Exception as e:
                debug_log(f"Error closing browser: {e}", "ERROR")


def scrape_categories(
    categories: list[str],
    limit_per_category: int,
    aggressive: bool,
    max_workers: int = 8,
    skip_already_scraped: bool = True,
    random_delay: tuple = (1, 2)
) -> dict:
    """Scrape multiple categories concurrently with priority (debugged)."""
    debug_log("=" * 80)
    debug_log("ENHANCED BATCH SCRAPER - DEBUG MODE")
    debug_log("=" * 80)
    debug_log(f"\nConfiguration:")
    debug_log(f"  Categories: {', '.join(categories)}")
    debug_log(f"  Limit per category: {limit_per_category}")
    debug_log(f"  Aggressive mode: {aggressive}")
    debug_log(f"  Max workers: {max_workers}")
    debug_log(f"  Skip already scraped: {skip_already_scraped}")
    debug_log(f"  Random delay: {random_delay}")
    debug_log(f"\n")

    # Load cookies
    if not COOKIES_FILE.exists():
        debug_log(f"ERROR: No cookies file at {COOKIES_FILE}", "ERROR")
        return {"error": "No cookies file"}

    try:
        cookies = json.loads(COOKIES_FILE.read_text())
        debug_log(f"✅ Loaded {len(cookies)} cookies from {COOKIES_FILE}")
    except Exception as e:
        debug_log(f"ERROR: Failed to load cookies: {e}", "ERROR")
        return {"error": f"Failed to load cookies: {e}"}

    # Load state and hashes
    state = load_state()
    hashes = load_hashes()
    debug_log(f"✅ Loaded state (total scraped: {state.get('total_scraped', 0)})")
    debug_log(f"✅ Loaded hashes ({len(hashes)} scripts)")

    all_results = {}

    # Scrape categories one by one (for debugging)
    for cat in categories:
        debug_log(f"\n{'='*80}")
        debug_log(f"Processing category: {cat}")
        debug_log(f"{'='*80}\n")

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

            # Update state
            save_state(state)

            # Summary
            debug_log(f"\nSummary for {cat}:")
            debug_log(f"  Saved: {results['saved']}")
            debug_log(f"  Skipped: {results['skipped']}")
            debug_log(f"  Duplicate: {results['duplicate']}")
            debug_log(f"  Closed: {results['closed']}")
            debug_log(f"  Failed: {results.get('failed', 0)}")

        except Exception as e:
            debug_log(f"ERROR: Failed to scrape {cat}: {e}", "ERROR")
            traceback.print_exc()
            all_results[cat] = {"error": str(e)}

    # Overall summary
    debug_log("\n" + "=" * 80)
    debug_log("SCRAPING COMPLETE - OVERALL SUMMARY")
    debug_log("=" * 80)

    total_saved = sum(r.get("saved", 0) for r in all_results.values() if isinstance(r, dict))
    total_skipped = sum(r.get("skipped", 0) for r in all_results.values() if isinstance(r, dict))
    total_duplicate = sum(r.get("duplicate", 0) for r in all_results.values() if isinstance(r, dict))
    total_closed = sum(r.get("closed", 0) for r in all_results.values() if isinstance(r, dict))
    total_failed = sum(r.get("failed", 0) for r in all_results.values() if isinstance(r, dict))

    debug_log(f"\nTotal across all categories:")
    debug_log(f"  Saved (new):     {total_saved}")
    debug_log(f"  Skipped (done):  {total_skipped}")
    debug_log(f"  Duplicate:       {total_duplicate}")
    debug_log(f"  Closed source:   {total_closed}")
    debug_log(f"  Failed:          {total_failed}")
    debug_log(f"  Total in state:  {state.get('total_scraped', 0)}")
    debug_log(f"\n")

    return all_results


def main():
    parser = argparse.ArgumentParser(description="Enhanced batch scraper for TradingView (DEBUG MODE)")
    parser.add_argument("--category", choices=list(CATEGORY_URLS.keys()))
    parser.add_argument("--all", action="store_true", help="Scrape all categories")
    parser.add_argument("--categories", nargs="+", choices=list(CATEGORY_URLS.keys()), help="Scrape specific categories")
    parser.add_argument("--limit", type=int, default=0, help="Max scripts per category")
    parser.add_argument("--aggressive", action="store_true", help="Faster scrolling (may miss some scripts)")
    parser.add_argument("--workers", type=int, default=8, help="Max concurrent workers")
    args = parser.parse_args()

    # Determine categories to scrape
    if args.all:
        categories = list(CATEGORY_URLS.keys())
    elif args.categories:
        categories = args.categories
    elif args.category:
        categories = [args.category]
    else:
        debug_log("ERROR: Please specify --category, --categories, or --all", "ERROR")
        sys.exit(1)

    # Scrape
    results = scrape_categories(
        categories=categories,
        limit_per_category=args.limit,
        aggressive=args.aggressive,
        max_workers=args.workers,
        skip_already_scraped=True,
        random_delay=(1, 2),
    )

    debug_log("SCRAPER FINISHED")


if __name__ == "__main__":
    main()
