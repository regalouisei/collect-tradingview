"""Single-URL Pine Script scraper.

Extracts Pine Script source code from a single TradingView URL
using Playwright. Reuses the same extraction logic as batch_scraper.py
but wrapped in a self-contained function.

This module uses the Playwright sync API — callers should run it
in a thread pool for async contexts (e.g., FastAPI).
"""

import json
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_COOKIES_FILE = PROJECT_ROOT / "results" / ".tv_cookies.json"


def slugify(name: str) -> str:
    """Convert a script name to a filesystem-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:80]


def _extract_script_name(page) -> str:
    """Extract script name from the page title or heading."""
    try:
        # Try the main title heading first
        title = page.evaluate("""() => {
            const h1 = document.querySelector('h1');
            if (h1) return h1.textContent.trim();
            const title = document.title;
            return title.split(' — ')[0].split(' - ')[0].trim();
        }""")
        return title or "unknown"
    except Exception:
        return "unknown"


def _extract_pine_source(page) -> str | None:
    """Extract Pine Script source from the current page.

    Assumes the page has already navigated to the script URL.
    Returns the Pine Script code or None if extraction fails.
    """
    # Check if it's open source
    is_open = page.evaluate("""() => {
        return document.body.textContent.includes('OPEN-SOURCE SCRIPT') ||
               document.body.textContent.includes('Open-source script');
    }""")

    if not is_open:
        return None

    # Click "Source code" tab if present
    try:
        source_tab = page.locator(
            'button:has-text("Source code"), [role="tab"]:has-text("Source code")'
        )
        if source_tab.is_visible(timeout=3000):
            source_tab.click()
            time.sleep(2)
    except Exception:
        pass

    # Extract code from the code container
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


def scrape_single_url(
    url: str,
    cookies_file: Path | None = None,
) -> tuple[str, str]:
    """Scrape Pine Script source from a single TradingView URL.

    Launches a headless browser, loads cookies, navigates to the URL,
    and extracts the Pine Script source code.

    Args:
        url: Full TradingView script URL.
        cookies_file: Path to exported cookies JSON. Defaults to
            results/.tv_cookies.json in the project root.

    Returns:
        Tuple of (script_name, pine_code).

    Raises:
        FileNotFoundError: If cookies file doesn't exist.
        ValueError: If script is closed-source or extraction fails.
    """
    if cookies_file is None:
        cookies_file = DEFAULT_COOKIES_FILE

    if not cookies_file.exists():
        raise FileNotFoundError(
            f"Cookies file not found: {cookies_file}. "
            "Export cookies from a logged-in TradingView session first."
        )

    cookies = json.loads(cookies_file.read_text())

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36"
            ),
        )
        context.add_cookies(cookies)
        page = context.new_page()

        try:
            page.goto(url, wait_until="networkidle", timeout=20000)
            time.sleep(1)

            script_name = _extract_script_name(page)
            pine_code = _extract_pine_source(page)

            if pine_code is None:
                raise ValueError(
                    f"Could not extract Pine Script from {url}. "
                    "The script may be closed-source or the page structure changed."
                )

            # Use slug as the canonical name
            slug = slugify(script_name)
            if not slug:
                slug = slugify(url.rstrip("/").split("/")[-1])

            return slug, pine_code

        finally:
            browser.close()
