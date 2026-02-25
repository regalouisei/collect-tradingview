"""Batch scraper v6 - Memory-optimized page-based scraping.

Memory Optimizations:
- Close browser after each page to free memory
- Process scripts in smaller batches
- Use lighter browser mode
- Longer delays between pages
- Reduced viewport size

Usage:
    python scripts/batch_scraper_v6.py --all
    python scripts/batch_scraper_v6.py --category oscillators --pages 1-5
"""

import argparse
import json
import re
import sys
import time
import random
import gc
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).parent.parent
PINE_DIR = PROJECT_ROOT / "pinescript"
COOKIES_FILE = PROJECT_ROOT / "results" / ".tv_cookies.json"
STATE_FILE = PROJECT_ROOT / "results" / ".scrape_state_v6.json"
HASHES_FILE = PROJECT_ROOT / "results" / ".script_hashes_v6.json"
PROGRESS_FILE = PROJECT_ROOT / "results" / ".scrape_progress_v6.json"

CATEGORY_URLS = {
    "editors_picks": "https://www.tradingview.com/scripts/editors-picks/",
    "top": "https://www.tradingview.com/scripts/?sort=top",
    "trending": "https://www.tradingview.com/scripts/?sort=trending",
    "oscillators": "https://www.tradingview.com/scripts/oscillator/",
    "trend_analysis": "https://www.tradingview.com/scripts/trendanalysis/",
    "volume": "https://www.tradingview.com/scripts/volume/",
    "moving_averages": "https://www.tradingview.com/scripts/movingaverage/",
    "volatility": "https://www.tradingview.com/scripts/volatility/",
    "momentum": "https://www.tradingview.com/scripts/momentum/",
}

PRIORITY_CATEGORIES = {
    "high": ["editors_picks", "top", "trending"],
    "medium": ["oscillators", "trend_analysis", "momentum"],
    "low": ["volume", "moving_averages", "volatility"],
}


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:80]


def load_hashes() -> dict:
    if not HASHES_FILE.exists():
        print(f"Hashes file not found, creating new one: {HASHES_FILE}")
        return {}

    try:
        content = HASHES_FILE.read_text()
        if not content.strip():
            return {}

        data = json.loads(content)

        if isinstance(data, list):
            print(f"⚠️  Converting list to dict...")
            hashes = {}
            for item in data:
                if isinstance(item, dict):
                    hashes.update(item)
                elif isinstance(item, str):
                    hashes[item] = item
            save_hashes(hashes)
            return hashes
        elif isinstance(data, dict):
            print(f"✅ Hashes loaded: {len(data)} entries")
            return data
        else:
            return {}

    except Exception as e:
        print(f"❌ Error loading hashes: {e}")
        return {}


def save_hashes(hashes: dict):
    if not isinstance(hashes, dict):
        hashes = {}

    HASHES_FILE.parent.mkdir(parents=True, exist_ok=True)
    HASHES_FILE.write_text(json.dumps(hashes, indent=2))


def compute_content_hash(pine_code: str) -> str:
    import hashlib
    return hashlib.sha256(pine_code.encode('utf-8')).hexdigest()


def is_duplicate(pine_code: str, hashes: dict) -> bool:
    if not isinstance(hashes, dict):
        return False

    content_hash = compute_content_hash(pine_code)
    return content_hash in hashes.values()


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"scraped": [], "failed": [], "last_run": None, "total_scraped": 0}


def save_state(state: dict):
    state["last_run"] = datetime.now().isoformat()
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def update_progress(category: str, page: int, total_pages: int, script_num: int, total_scripts: int, status: str = "running"):
    progress = {
        "category": category,
        "page": page,
        "total_pages": total_pages,
        "script_num": script_num,
        "total_scripts": total_scripts,
        "status": status,
        "timestamp": datetime.now().isoformat()
    }

    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2))


def detect_total_pages(page) -> int:
    """Detect total number of pages from pagination."""
    try:
        total_pages = page.evaluate("""() => {
            const pagination = document.querySelector('nav[aria-label="Pagination"]');
            if (!pagination) return 0;

            const links = pagination.querySelectorAll('a[href*="page-"]');
            let maxPage = 0;
            links.forEach(link => {
                const href = link.getAttribute('href');
                const match = href.match(/page-(\\d+)/);
                if (match) {
                    const pageNum = parseInt(match[1]);
                    if (pageNum > maxPage) maxPage = pageNum;
                }
            });

            return maxPage;
        }""")

        if total_pages > 0:
            print(f"  Detected {total_pages} pages")
            return total_pages

        has_next = page.evaluate("""() => {
            const nextBtn = document.querySelector('button[aria-label="Next page"]');
            return nextBtn && !nextBtn.disabled;
        }""")

        if has_next:
            print("  Has pagination, using default 50 pages.")
            return 50

        print("  No pagination found")
        return 1

    except Exception as e:
        print(f"  Error detecting pages: {e}")
        return 1


def collect_scripts_from_page(page, url: str) -> list[dict]:
    """Collect scripts from a single page."""
    page.goto(url, wait_until="networkidle", timeout=30000)
    time.sleep(random.uniform(0.5, 1.0))

    scripts = page.evaluate("""() => {
        const results = [];
        const articles = document.querySelectorAll('article');

        articles.forEach(article => {
            const link = article.querySelector('a[href*="/script/"]');
            if (!link) return;

            const href = link.getAttribute('href');
            const name = link.textContent?.trim();

            if (!href || !name || name.length < 5) return;

            results.push({
                name: name.substring(0, 100),
                url: href.startsWith('/') ? 'https://www.tradingview.com' + href : href
            });
        });

        return results;
    }""")

    return scripts


def extract_pine_source(page, script_url: str, max_retries: int = 2) -> str | None:
    """Navigate to a script page and extract Pine Script source code."""
    for attempt in range(max_retries):
        try:
            page.goto(script_url, wait_until="networkidle", timeout=20000)
            time.sleep(random.uniform(0.3, 0.8))

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
                    time.sleep(0.5)
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
                time.sleep(random.uniform(1, 2))
            continue

    return None


def scrape_category(
    category: str,
    max_pages: int = 0,
    skip_already_scraped: bool = True,
    cookies: list = None
) -> dict:
    """Scrape all pages of a category (memory-optimized)."""
    print(f"\n{'='*60}")
    print(f"Category: {category}")
    print(f"{'='*60}")

    base_url = CATEGORY_URLS[category]

    # First visit to detect total pages
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            # Reduced viewport for less memory
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},  # Reduced from 1920x1080
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        )
        if cookies:
            context.add_cookies(cookies)
        page = context.new_page()

        try:
            print(f"\nDetecting total pages for {category}...")
            page.goto(base_url, wait_until="networkidle", timeout=30000)
            time.sleep(random.uniform(1, 2))

            try:
                dont_need = page.locator("button:has-text('Don\\'t need')")
                if dont_need.is_visible(timeout=3000):
                    dont_need.click()
                    time.sleep(1)
            except Exception:
                pass

            total_pages = detect_total_pages(page)

            if max_pages > 0 and max_pages < total_pages:
                total_pages = max_pages

            print(f"  Will scrape {total_pages} pages")

        finally:
            browser.close()
            # Force garbage collection
            gc.collect()

    # Now scrape pages one by one, closing browser after each page
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

    total_scripts = 0
    total_processed = 0

    for page_num in range(1, total_pages + 1):
        # Build page URL
        if page_num == 1:
            page_url = base_url
        else:
            if '?' in base_url:
                page_url = f"{base_url}&page={page_num}"
            else:
                page_url = f"{base_url.rstrip('/')}/page-{page_num}/"

        print(f"\n  [Page {page_num}/{total_pages}] {page_url}")

        # Open browser for this page only
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            )
            if cookies:
                context.add_cookies(cookies)
            page = context.new_page()

            try:
                # Collect scripts from this page
                scripts = collect_scripts_from_page(page, page_url)
                print(f"    Found {len(scripts)} scripts")
                total_scripts += len(scripts)

                # Process each script
                for i, script in enumerate(scripts, 1):
                    total_processed += 1
                    name = script["name"]
                    url = script["url"]
                    slug = slugify(name)
                    pine_path = category_dir / f"{slug}.pine"

                    # Update progress
                    update_progress(category, page_num, total_pages, total_processed, total_scripts)

                    if i % 3 == 0 or i == len(scripts):
                        print(f"    [{i}/{len(scripts)}] {name[:50]}")

                    if skip_already_scraped and (url in state["scraped"] or pine_path.exists()):
                        results["skipped"] += 1
                        results["scripts"].append({"name": name, "url": url, "status": "skipped"})
                        continue

                    code = extract_pine_source(page, url)
                    if code is None:
                        print(f"      Skipped (closed source)")
                        results["closed"] += 1
                        results["scripts"].append({"name": name, "url": url, "status": "closed"})
                        continue

                    if is_duplicate(code, hashes):
                        print(f"      Skipped (duplicate)")
                        results["duplicate"] += 1
                        results["scripts"].append({"name": name, "url": url, "status": "duplicate"})
                        continue

                    lines = code.count("\n") + 1
                    pine_path.write_text(code, encoding='utf-8')
                    print(f"      Saved: {slug}.pine ({lines} lines)")

                    content_hash = compute_content_hash(code)
                    hashes[slug] = content_hash
                    save_hashes(hashes)

                    state["scraped"].append(url)
                    state["total_scraped"] = state.get("total_scraped", 0) + 1

                    results["saved"] += 1
                    results["scripts"].append({"name": name, "url": url, "status": "saved"})

            finally:
                browser.close()
                # Force garbage collection after each page
                gc.collect()

        # Longer delay between pages
        time.sleep(random.uniform(2, 4))

        # Every 10 pages, force an extra GC
        if page_num % 10 == 0:
            gc.collect()
            print(f"    Memory cleanup after {page_num} pages")

    # Mark as completed
    update_progress(category, total_pages, total_pages, total_processed, total_scripts, "completed")

    return results


def scrape_categories(
    categories: list[str],
    max_pages_per_category: int = 0,
    skip_already_scraped: bool = True
) -> dict:
    """Scrape multiple categories."""
    print("=" * 60)
    print("Batch Scraper v6 - Memory-Optimized")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  Categories: {', '.join(categories)}")
    print(f"  Max pages per category: {max_pages_per_category if max_pages_per_category > 0 else 'ALL'}")
    print(f"  Skip already scraped: {skip_already_scraped}")
    print(f"  Memory mode: OPTIMIZED (close browser each page)")

    if not COOKIES_FILE.exists():
        print(f"\nERROR: No cookies file at {COOKIES_FILE}")
        return {"error": "No cookies file"}

    cookies = json.loads(COOKIES_FILE.read_text())
    print(f"\n✅ Cookies loaded ({len(cookies)} cookies)")

    state = load_state()
    hashes = load_hashes()
    print(f"✅ State loaded (total scraped: {state.get('total_scraped', 0)})")

    all_results = {}

    for cat in categories:
        print(f"\nProcessing: {cat}")

        try:
            results = scrape_category(
                category=cat,
                max_pages=max_pages_per_category,
                skip_already_scraped=skip_already_scraped,
                cookies=cookies
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

    # Clear progress
    update_progress("all", 0, 0, 0, 0, "completed")

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
    parser = argparse.ArgumentParser(description="Batch scraper v6 - Memory-optimized")
    parser.add_argument("--category", choices=list(CATEGORY_URLS.keys()))
    parser.add_argument("--all", action="store_true", help="Scrape all categories")
    parser.add_argument("--categories", nargs="+", choices=list(CATEGORY_URLS.keys()))
    parser.add_argument("--pages", type=int, default=0, help="Max pages per category (0 = all)")
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
        max_pages_per_category=args.pages,
        skip_already_scraped=True,
    )


if __name__ == "__main__":
    main()
