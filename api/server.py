"""DeepStack TradingView — Backtest API Server

Exposes the scrape -> convert -> backtest pipeline as an HTTP API.
POST /backtest with {"url": "https://www.tradingview.com/script/..."}
returns JSON backtest results.

Usage:
    uvicorn api.server:app --port 8100
    # or: python -m api.server
"""

import asyncio
import math
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class BacktestRequest(BaseModel):
    url: str


class TickerResult(BaseModel):
    ticker: str
    roi_pct: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    win_rate_pct: Optional[float] = None
    max_drawdown_pct: Optional[float] = None
    profit_factor: Optional[float] = None
    num_trades: Optional[int] = None
    error: Optional[str] = None


class BacktestResponse(BaseModel):
    script_name: str
    category: str
    composite_score: Optional[float] = None
    tickers: list[TickerResult]
    scoreboard_avg: Optional[float] = None
    saved_to_scoreboard: bool


# ---------------------------------------------------------------------------
# Rate limiter (in-memory)
# ---------------------------------------------------------------------------

MAX_CONCURRENT = 5
MAX_PER_HOUR = 20

_active_count = 0
_hourly_counts: dict[str, list[float]] = defaultdict(list)


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate_limit(ip: str) -> None:
    global _active_count

    if _active_count >= MAX_CONCURRENT:
        raise HTTPException(
            status_code=429,
            detail=f"Too many concurrent requests (max {MAX_CONCURRENT}). Try again shortly.",
        )

    now = time.time()
    hour_ago = now - 3600
    _hourly_counts[ip] = [t for t in _hourly_counts[ip] if t > hour_ago]

    if len(_hourly_counts[ip]) >= MAX_PER_HOUR:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded ({MAX_PER_HOUR}/hour). Try again later.",
        )

    _hourly_counts[ip].append(now)


def _clean_numeric(value) -> Optional[float]:
    """Convert NaN/Inf to None for JSON serialization."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if math.isnan(value) or math.isinf(value):
            return None
        return float(value)
    return None


# Stat key mapping from backtest engine output to response fields
_STAT_KEY_MAP = {
    "Return [%]": "roi_pct",
    "Sharpe Ratio": "sharpe_ratio",
    "Win Rate [%]": "win_rate_pct",
    "Max. Drawdown [%]": "max_drawdown_pct",
    "Profit Factor": "profit_factor",
    "# Trades": "num_trades",
}


# ---------------------------------------------------------------------------
# Background task: Supabase sync
# ---------------------------------------------------------------------------

def _sync_to_supabase(script_name: str, category: str, multi_stats: dict) -> None:
    """Sync results to Supabase (runs as background task)."""
    try:
        from framework.supabase_sync import sync_pipeline_run
        sync_pipeline_run(script_name, category, multi_stats)
    except Exception as e:
        print(f"  Background Supabase sync failed: {e}")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="DeepStack TradingView Backtest API",
    description="Scrape, convert, and backtest TradingView Pine Scripts via HTTP.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://milo.deepstack.trade",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "active_backtests": _active_count}


@app.post("/backtest", response_model=BacktestResponse)
async def run_backtest(
    body: BacktestRequest,
    request: Request,
    background_tasks: BackgroundTasks,
):
    global _active_count

    # Validate URL
    if "tradingview.com/script/" not in body.url:
        raise HTTPException(
            status_code=400,
            detail="URL must be a TradingView script page (contains 'tradingview.com/script/').",
        )

    # Rate limit
    ip = _get_client_ip(request)
    _check_rate_limit(ip)

    _active_count += 1
    try:
        # Step 1: Scrape Pine Script (sync Playwright — run in thread pool)
        from framework.single_scraper import scrape_single_url

        try:
            script_name, pine_code = await asyncio.to_thread(
                scrape_single_url, body.url
            )
        except FileNotFoundError as e:
            raise HTTPException(status_code=503, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

        # Step 2: Convert Pine Script to Python
        from framework.pine_converter import convert_pine_to_python

        try:
            python_code = await asyncio.to_thread(
                convert_pine_to_python, pine_code, script_name
            )
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Pine Script conversion failed: {e}",
            )

        # Step 3: Write temporary backtest file
        backtest_dir = PROJECT_ROOT / "backtests" / "custom"
        backtest_dir.mkdir(parents=True, exist_ok=True)
        backtest_file = backtest_dir / f"{script_name}.py"

        header = (
            f'"""\nSource: TradingView Community Script — {script_name}\n'
            f'Generated by DeepStack TradingView Pipeline (API)\n"""\n\n'
        )
        backtest_file.write_text(header + python_code, encoding="utf-8")

        # Step 4: Run backtest across all tickers
        from framework.backtest_engine import run_multi_ticker_backtest

        try:
            multi_stats = await asyncio.to_thread(
                run_multi_ticker_backtest, backtest_file
            )
        except Exception as e:
            multi_stats = {
                "SPY": {"error": str(e)},
                "BTC": {"error": str(e)},
                "QQQ": {"error": str(e)},
            }

        # Step 5: Schedule Supabase sync as background task
        background_tasks.add_task(
            _sync_to_supabase, script_name, "custom", multi_stats
        )

        # Step 6: Build response
        ticker_results = []
        sharpe_values = []

        for ticker, stats in multi_stats.items():
            if "error" in stats:
                ticker_results.append(TickerResult(
                    ticker=ticker,
                    error=stats["error"],
                ))
            else:
                result = TickerResult(ticker=ticker)
                for engine_key, field_name in _STAT_KEY_MAP.items():
                    value = stats.get(engine_key)
                    cleaned = _clean_numeric(value)
                    if field_name == "num_trades" and cleaned is not None:
                        cleaned = int(cleaned)
                    setattr(result, field_name, cleaned)
                ticker_results.append(result)

                sharpe = _clean_numeric(stats.get("Sharpe Ratio"))
                if sharpe is not None:
                    sharpe_values.append(sharpe)

        # Calculate composite score (same formula as DB trigger)
        composite = None
        if sharpe_values:
            avg_sharpe = sum(sharpe_values) / len(sharpe_values)

            roi_vals = [
                _clean_numeric(s.get("Return [%]"))
                for s in multi_stats.values()
                if "error" not in s and _clean_numeric(s.get("Return [%]")) is not None
            ]
            wr_vals = [
                _clean_numeric(s.get("Win Rate [%]"))
                for s in multi_stats.values()
                if "error" not in s and _clean_numeric(s.get("Win Rate [%]")) is not None
            ]
            pf_vals = [
                _clean_numeric(s.get("Profit Factor"))
                for s in multi_stats.values()
                if "error" not in s and _clean_numeric(s.get("Profit Factor")) is not None
            ]

            avg_roi = sum(roi_vals) / len(roi_vals) if roi_vals else 0
            avg_wr = sum(wr_vals) / len(wr_vals) if wr_vals else 0
            avg_pf = sum(pf_vals) / len(pf_vals) if pf_vals else 0

            composite = (
                avg_sharpe * 0.3
                + avg_roi / 100 * 0.25
                + avg_wr / 100 * 0.25
                + avg_pf / 10 * 0.2
            )

        return BacktestResponse(
            script_name=script_name,
            category="custom",
            composite_score=round(composite, 4) if composite is not None else None,
            tickers=ticker_results,
            scoreboard_avg=None,
            saved_to_scoreboard=True,
        )

    finally:
        _active_count -= 1
