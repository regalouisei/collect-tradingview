"""Telegram notification module for DeepStack TradingView pipeline.

Sends formatted alerts to Telegram when notable events occur:
- Daily pipeline summary (scraped, converted, backtested counts)
- High Sharpe discoveries (Sharpe > 2.0 on any ticker)
- Top-10 indicator discoveries (new high composite score)

Uses the OpenClaw bot token from .env (NOT HYDRA's bot).
"""

import os
from pathlib import Path
from typing import Optional

import httpx

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent

# Load .env from project root
_env_path = PROJECT_ROOT / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

TELEGRAM_API = "https://api.telegram.org"


def _get_bot_token() -> str:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set in environment or .env")
    return token


def _get_chat_id() -> str:
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not chat_id:
        raise RuntimeError("TELEGRAM_CHAT_ID not set in environment or .env")
    return chat_id


# ---------------------------------------------------------------------------
# Core send function
# ---------------------------------------------------------------------------

def send_telegram(message: str) -> bool:
    """Send an HTML-formatted message to Telegram.

    Args:
        message: HTML-formatted message text.

    Returns:
        True if sent successfully, False otherwise.
    """
    token = _get_bot_token()
    chat_id = _get_chat_id()

    url = f"{TELEGRAM_API}/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        resp = httpx.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except (httpx.HTTPError, RuntimeError) as e:
        print(f"  Telegram send failed: {e}")
        return False


# ---------------------------------------------------------------------------
# Notification templates
# ---------------------------------------------------------------------------

def notify_daily_summary(
    total_scraped: int,
    total_converted: int,
    total_failed: int,
    top_performer: Optional[str] = None,
    elapsed_seconds: Optional[float] = None,
) -> bool:
    """Send end-of-pipeline daily summary.

    Args:
        total_scraped: Number of Pine Scripts found to process.
        total_converted: Number successfully backtested.
        total_failed: Number that failed conversion or backtest.
        top_performer: Name of the best-performing script this run.
        elapsed_seconds: Total pipeline runtime in seconds.
    """
    elapsed_str = f" in {elapsed_seconds:.0f}s" if elapsed_seconds else ""

    lines = [
        "<b>DeepStack TV Pipeline</b> -- Daily Summary",
        "",
        f"Scripts processed: <b>{total_scraped}</b>",
        f"Converted + backtested: <b>{total_converted}</b>",
        f"Failed: <b>{total_failed}</b>",
    ]

    if top_performer:
        lines.append(f"Top performer: <code>{top_performer}</code>")

    if elapsed_str:
        lines.append(f"Runtime: {elapsed_str.strip()}")

    success_rate = (total_converted / total_scraped * 100) if total_scraped > 0 else 0
    lines.append(f"Success rate: {success_rate:.0f}%")

    return send_telegram("\n".join(lines))


def notify_high_sharpe(
    script_name: str,
    sharpe: float,
    ticker: str,
) -> bool:
    """Alert when an indicator achieves Sharpe > 2.0 on any ticker.

    Args:
        script_name: Name of the TradingView script.
        sharpe: The Sharpe ratio achieved.
        ticker: Which ticker (SPY, BTC, QQQ) hit the threshold.
    """
    message = (
        "<b>High Sharpe Discovery</b>\n"
        "\n"
        f"Script: <code>{script_name}</code>\n"
        f"Ticker: <b>{ticker}</b>\n"
        f"Sharpe Ratio: <b>{sharpe:.2f}</b>\n"
        "\n"
        "This indicator may be worth investigating for live signals."
    )
    return send_telegram(message)


def notify_top_discovery(
    script_name: str,
    composite_score: float,
    avg_sharpe: float,
) -> bool:
    """Alert when a new top-10 indicator is discovered.

    Args:
        script_name: Name of the TradingView script.
        composite_score: The composite ranking score.
        avg_sharpe: Average Sharpe ratio across tickers.
    """
    message = (
        "<b>New Top-10 Indicator</b>\n"
        "\n"
        f"Script: <code>{script_name}</code>\n"
        f"Composite Score: <b>{composite_score:.3f}</b>\n"
        f"Avg Sharpe: <b>{avg_sharpe:.2f}</b>\n"
        "\n"
        "Check the scoreboard for full rankings."
    )
    return send_telegram(message)
