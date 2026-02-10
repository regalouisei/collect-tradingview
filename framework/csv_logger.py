"""Log backtest results to a summary CSV."""

import csv
from pathlib import Path
from typing import Any

RESULTS_DIR = Path(__file__).parent.parent / "results"
CSV_FILE = RESULTS_DIR / "backtest_results.csv"

CSV_COLUMNS = [
    "script_name",
    "category",
    "ticker",
    "backtest_file",
    "pine_file",
    "roi_pct",
    "max_drawdown_pct",
    "sharpe_ratio",
    "sortino_ratio",
    "expectancy_pct",
    "num_trades",
    "win_rate_pct",
    "profit_factor",
    "error",
]


def init_csv() -> Path:
    """Create the CSV file with headers if it doesn't exist."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    if not CSV_FILE.exists():
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
    return CSV_FILE


def log_to_csv(
    script_name: str,
    category: str,
    ticker: str,
    backtest_file: str,
    pine_file: str,
    stats: dict[str, Any],
) -> None:
    """Append a single backtest result row to the CSV.

    Args:
        script_name: Name of the TradingView script
        category: editors_picks, top, or trending
        ticker: SPY, BTC, or QQQ
        backtest_file: Path to the Python backtest file
        pine_file: Path to the .pine file
        stats: Stats dict from backtest_engine
    """
    init_csv()

    row = {
        "script_name": script_name,
        "category": category,
        "ticker": ticker,
        "backtest_file": backtest_file,
        "pine_file": pine_file,
        "roi_pct": stats.get("Return [%]"),
        "max_drawdown_pct": stats.get("Max. Drawdown [%]"),
        "sharpe_ratio": stats.get("Sharpe Ratio"),
        "sortino_ratio": stats.get("Sortino Ratio"),
        "expectancy_pct": stats.get("Expectancy [%]"),
        "num_trades": stats.get("# Trades"),
        "win_rate_pct": stats.get("Win Rate [%]"),
        "profit_factor": stats.get("Profit Factor"),
        "error": stats.get("error", ""),
    }

    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writerow(row)


def log_multi_ticker_results(
    script_name: str,
    category: str,
    backtest_file: str,
    pine_file: str,
    multi_stats: dict[str, dict[str, Any]],
) -> None:
    """Log results for all tickers from a multi-ticker backtest run."""
    for ticker, stats in multi_stats.items():
        log_to_csv(
            script_name=script_name,
            category=category,
            ticker=ticker,
            backtest_file=backtest_file,
            pine_file=pine_file,
            stats=stats,
        )
