"""Supabase sync module for DeepStack TradingView pipeline.

Uploads pipeline results (indicators + backtests) to Supabase via PostgREST.
Designed to be called from run_pipeline.py after each script processes,
or standalone via upload_csv_results() to bulk-import existing CSV data.
"""

import csv
import math
import os
from pathlib import Path
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent

# Try loading .env from project root (for local dev)
_env_path = PROJECT_ROOT / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def _get_url() -> str:
    url = os.environ.get("SUPABASE_URL")
    if not url:
        raise RuntimeError("SUPABASE_URL environment variable is required")
    return url


def _get_key() -> str:
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not key:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY environment variable is required")
    return key


def _rest_url(table: str) -> str:
    return f"{_get_url()}/rest/v1/{table}"


def _headers(prefer: str = "return=representation") -> dict[str, str]:
    key = _get_key()
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": prefer,
    }


def _clean_numeric(value: Any) -> Any:
    """Convert NaN/Inf to None for JSON serialization."""
    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if isinstance(value, str):
        if value.lower() in ("nan", "inf", "-inf", ""):
            return None
        try:
            f = float(value)
            if math.isnan(f) or math.isinf(f):
                return None
            return f
        except ValueError:
            return None
    return value


# ---------------------------------------------------------------------------
# Core PostgREST operations
# ---------------------------------------------------------------------------

def _upsert(table: str, data: dict, on_conflict: str) -> dict | None:
    """Upsert a row via PostgREST. Returns the row or None on failure."""
    url = f"{_rest_url(table)}?on_conflict={on_conflict}"
    headers = _headers("return=representation,resolution=merge-duplicates")
    resp = httpx.post(url, json=data, headers=headers, timeout=15)
    if resp.status_code >= 400:
        print(f"  PostgREST error ({resp.status_code}): {resp.text[:500]}")
    resp.raise_for_status()
    rows = resp.json()
    return rows[0] if rows else None


def _get(table: str, params: str = "") -> list[dict]:
    """GET rows from PostgREST."""
    url = f"{_rest_url(table)}{('?' + params) if params else ''}"
    resp = httpx.get(url, headers=_headers(), timeout=15)
    resp.raise_for_status()
    return resp.json()


def _patch(table: str, filter_params: str, data: dict) -> dict | None:
    """PATCH (update) rows matching filter."""
    url = f"{_rest_url(table)}?{filter_params}"
    resp = httpx.patch(url, json=data, headers=_headers(), timeout=15)
    resp.raise_for_status()
    rows = resp.json()
    return rows[0] if rows else None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def sync_indicator(
    script_name: str,
    category: str,
    conversion_status: str = "completed",
) -> dict:
    """Upsert an indicator row. Returns the indicator record with id."""
    data = {
        "script_name": script_name,
        "category": category,
        "conversion_status": conversion_status,
    }
    row = _upsert("ds_tv_indicators", data, on_conflict="script_name")
    if not row:
        raise RuntimeError(f"Failed to upsert indicator: {script_name}")
    return row


def sync_backtest(
    script_name: str,
    ticker: str,
    stats_dict: dict[str, Any],
    category: str = "unknown",
) -> dict | None:
    """Sync a single backtest result.

    1. Ensures the parent indicator exists (upsert).
    2. Upserts the backtest row with the indicator_id FK.
    3. The DB trigger auto-recalculates composite score.
    """
    indicator = sync_indicator(script_name, category)
    indicator_id = indicator["id"]

    data = {
        "indicator_id": indicator_id,
        "script_name": script_name,
        "ticker": ticker,
        "roi_pct": _clean_numeric(stats_dict.get("roi_pct")),
        "max_drawdown_pct": _clean_numeric(stats_dict.get("max_drawdown_pct")),
        "sharpe_ratio": _clean_numeric(stats_dict.get("sharpe_ratio")),
        "sortino_ratio": _clean_numeric(stats_dict.get("sortino_ratio")),
        "win_rate_pct": _clean_numeric(stats_dict.get("win_rate_pct")),
        "profit_factor": _clean_numeric(stats_dict.get("profit_factor")),
        "num_trades": int(_clean_numeric(stats_dict.get("num_trades"))) if _clean_numeric(stats_dict.get("num_trades")) is not None else None,
        "expectancy_pct": _clean_numeric(stats_dict.get("expectancy_pct")),
        "error": stats_dict.get("error") or None,
        "backtest_file": stats_dict.get("backtest_file"),
    }

    return _upsert("ds_tv_backtests", data, on_conflict="script_name,ticker")


# Mapping from backtest engine stat keys to DB column names
_STAT_KEY_MAP = {
    "Return [%]": "roi_pct",
    "Max. Drawdown [%]": "max_drawdown_pct",
    "Sharpe Ratio": "sharpe_ratio",
    "Sortino Ratio": "sortino_ratio",
    "Win Rate [%]": "win_rate_pct",
    "Profit Factor": "profit_factor",
    "# Trades": "num_trades",
    "Expectancy [%]": "expectancy_pct",
}


def _translate_stats(stats: dict[str, Any]) -> dict[str, Any]:
    """Translate backtest engine stat keys to DB column names."""
    translated: dict[str, Any] = {}
    for engine_key, db_key in _STAT_KEY_MAP.items():
        if engine_key in stats:
            translated[db_key] = stats[engine_key]
    if "error" in stats:
        translated["error"] = stats["error"]
    return translated


def sync_pipeline_run(
    script_name: str,
    category: str,
    multi_stats: dict[str, dict[str, Any]],
) -> None:
    """Sync a complete pipeline run (all tickers for one script).

    Called from run_pipeline.py after each script processes.
    The multi_stats dict maps ticker -> stats_dict (using backtest engine keys).
    """
    has_success = any("error" not in s for s in multi_stats.values())
    status = "completed" if has_success else "error"
    indicator = sync_indicator(script_name, category, conversion_status=status)
    indicator_id = indicator["id"]

    for ticker, raw_stats in multi_stats.items():
        translated = _translate_stats(raw_stats)
        data = {
            "indicator_id": indicator_id,
            "script_name": script_name,
            "ticker": ticker,
            "roi_pct": _clean_numeric(translated.get("roi_pct")),
            "max_drawdown_pct": _clean_numeric(translated.get("max_drawdown_pct")),
            "sharpe_ratio": _clean_numeric(translated.get("sharpe_ratio")),
            "sortino_ratio": _clean_numeric(translated.get("sortino_ratio")),
            "win_rate_pct": _clean_numeric(translated.get("win_rate_pct")),
            "profit_factor": _clean_numeric(translated.get("profit_factor")),
            "num_trades": int(_clean_numeric(translated.get("num_trades"))) if _clean_numeric(translated.get("num_trades")) is not None else None,
            "expectancy_pct": _clean_numeric(translated.get("expectancy_pct")),
            "error": translated.get("error") or None,
        }
        _upsert("ds_tv_backtests", data, on_conflict="script_name,ticker")


def upload_csv_results(csv_path: str | Path | None = None) -> int:
    """Bulk-upload existing CSV backtest results to Supabase.

    Reads the CSV at the given path (defaults to results/backtest_results.csv),
    upserts each row as indicator + backtest, and returns the count uploaded.
    """
    if csv_path is None:
        csv_path = PROJECT_ROOT / "results" / "backtest_results.csv"
    csv_path = Path(csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    uploaded = 0
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            script_name = row["script_name"]
            category = row["category"]
            ticker = row["ticker"]

            has_error = bool(row.get("error", "").strip())
            has_results = bool(row.get("roi_pct", "").strip())
            if has_error:
                status = "error"
            elif has_results:
                status = "completed"
            else:
                status = "pending"

            stats = {
                "roi_pct": row.get("roi_pct"),
                "max_drawdown_pct": row.get("max_drawdown_pct"),
                "sharpe_ratio": row.get("sharpe_ratio"),
                "sortino_ratio": row.get("sortino_ratio"),
                "win_rate_pct": row.get("win_rate_pct"),
                "profit_factor": row.get("profit_factor"),
                "num_trades": row.get("num_trades"),
                "expectancy_pct": row.get("expectancy_pct"),
                "error": row.get("error"),
                "backtest_file": row.get("backtest_file"),
            }

            sync_backtest(script_name, ticker, stats, category=category)
            uploaded += 1

    return uploaded


# ---------------------------------------------------------------------------
# CLI entry point for manual testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--upload-csv":
        path = sys.argv[2] if len(sys.argv) > 2 else None
        count = upload_csv_results(path)
        print(f"Uploaded {count} rows to Supabase")
    else:
        print("Usage: python -m framework.supabase_sync --upload-csv [path/to/csv]")
