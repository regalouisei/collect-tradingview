"""Top & Trending category scraper for TradingView.

Specialized script for handling the generic script listing pages:
- top: https://www.tradingview.com/scripts/?sort=top
- trending: https://www.tradingview.com/scripts/?sort=trending

These pages have a different structure than category-specific pages.
"""

import json
import re
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).parent.parent
PINE_DIR = PROJECT_ROOT / "pinescript"
COOKIES_FILE = PROJECT_ROOT / "results" / ".tv_cookies.json"
STATE_FILE = PROJECT_ROOT / "results" / ".scrape_state_optimized.json"
HASHES_FILE = PROJECT_ROOT / "results" / ".script_hashes.json"

CATEGORY_URLS = {
    "top": "https://www.tradingview.com/scripts/?sort=top",
    "trending": "https://www.tradingview.com/scripts/?sort=trending",
}


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:80]


def load_hashes() -> dict:
    """Load script content hashes for deduplication."""
    if HASHES_FILE.exists():
        return json.loads(HASHES_FILE.read_text())
    return {}


def save_hashes(hashes: dict):
    """Save script content hashes."""
    HASHES_FILE.parent.mkdir(parents=True, exist_ok=True)
    HASHES_FILE.write_text(json.dumps(hashes, indent=2))


def compute_content_hash(pine_code: str) -> str:
    """Compute SHA256 hash of Pine Script content."""
    import hashlib
    return hashlib.sha256(pine_code.encode('utf-8')).hexdigest()


def is_duplicate(pine_code: str, hashes: dict) -> bool:
    """Check if script content is a duplicate."""
    content_hash = compute_content_hash(pine_code)
    return content_hash in hashes.values()


def load_state() -> dict:
    """Load scraping state."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"scraped": [], "failed": [], "last_run": None, "total_scraped": 0}


def save_state(state: dict):
    """Save scraping state."""
    from datetime import datetime
    state["last_run"] = datetime.now().isoformat()
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def extract_pine_source(page, script_url: str, max_retries: int = 2) -> str | None:
    """Navigate to a script page and extract Pine Script source code."""
    for attempt in range(max_retries):
        try:
            page.goto(script_url, wait_until="networkidle", timeout=20000)
            time.sleep(0.5)

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
                if source_tab.is_visible(timeout=2000):
                    source_tab.click()
                    time.sleep(1)
            except Exception:
                pass

            # Extract code
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
            print(f"    Retry {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            continue

    return None


def scrape_category(
    category: str,
    limit: int,
    aggressive: bool,
    cookies: list,
    skip_already_scraped: bool = True
) -> dict:
    """Scrape top or trending category."""
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
            url = CATEGORY_URLS[category]
            print(f"\nCollecting scripts from {category}: {url}")
            page.goto(url, wait_until="networkidle", timeout=30000)
            time.sleep(2)

            # Dismiss any popups
            try:
                dont_need = page.locator('button:has-text("Don\\'t need")')
                if dont_need.is_visible(timeout=3000):
                    dont_need.click()
                    time.sleep(1)
            except Exception:
                pass

            # Aggressive scrolling
            max_scrolls = 80 if aggressive else 50
            no_new_count = 0
            no_new_threshold = 2 if aggressive else 3
            prev_height = 0

            print(f"    Aggressive mode: {aggressive} (max_scrolls={max_scrolls}, threshold={no_new_threshold})")

            for i in range(max_scrolls):
                current_height = page.evaluate("document.body.scrollHeight")
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(0.5 if aggressive else 1)
                new_height = page.evaluate("document.body.scrollHeight")

                if new_height == current_height:
                    no_new_count += 1
                    if no_new_count >= no_new_threshold:
                        print(f"    Scroll stopped after {i+1} scrolls (no new content)")
                        break
                else:
                    no_new_count = 0

            # Extract script links - improved selector
            scripts = page.evaluate("""() => {
                const links = document.querySelectorAll('a[href*="/script/"]');
                const seen = new Set();
                const results = [];
                for (const link of links) {
                    const href = link.getAttribute('href');
                    const name = link.textContent?.trim();
                    if (!href || seen.has(href) || !name || name.length < 5) continue;
                    if (href.includes('/script/')) {
                        // Skip sub-pages
                        if (href.includes('?') || href.includes('#')) continue;

                        // Skip duplicate names
                        const lowerName = name.toLowerCase();
                        if (Array.from(results).some(r => r.name.toLowerCase() === lowerName)) continue;

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

            # Load state and hashes
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

                # Skip if already scraped
                if skip_already_scraped and (url in state["scraped"] or pine_path.exists()):
                    print(f"    Skipped (already done)")
                    results["skipped"] += 1
                    results["scripts"].append({"name": name, "url": url, "status": "skipped"})
                    continue

                # Extract source code
                code = extract_pine_source(page, url)
                if code is None:
                    print(f"    Skipped (closed source or extraction failed)")
                    results["closed"] += 1
                    results["scripts"].append({"name": name, "url": url, "status": "closed"})
                    continue

                # Check for duplicates
                if is_duplicate(code, hashes):
                    print(f"    Skipped (duplicate content)")
                    results["duplicate"] += 1
                    results["scripts"].append({"name": name, "url": url, "status": "duplicate"})
                    continue

                # Save script
                lines = code.count("\n") + 1
                pine_path.write_text(code, encoding="utf-8")
                print(f"    Saved: {slug}.pine ({lines} lines)")

                # Update state and hashes
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


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Scrape top & trending categories")
    parser.add_argument("--category", choices=["top", "trending"])
    parser.add_argument("--limit", type=int, default=50, help="Max scripts")
    parser.add_argument("--aggressive", action="store_true", help="Faster scrolling")
    args = parser.parse_args()

    # Load cookies
    if not COOKIES_FILE.exists():
        print(f"ERROR: No cookies file at {COOKIES_FILE}")
        return

    cookies = json.loads(COOKIES_FILE.read_text())
    print(f"\n✅ Cookies loaded ({len(cookies)} cookies)")

    # Scrape
    results = scrape_category(
        category=args.category,
        limit=args.limit,
        aggressive=args.aggressive,
        cookies=cookies,
    )

    # Summary
    print(f"\n  Summary for {args.category}:")
    print(f"    Saved: {results['saved']}")
    print(f"    Skipped: {results['skipped']}")
    print(f"    Duplicate: {results['duplicate']}")
    print(f"    Closed: {results['closed']}")
    print(f"    Failed: {results['failed']}")


if __name__ == "__main__":
    main()
