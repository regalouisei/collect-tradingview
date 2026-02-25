"""Orchestrator: Process scraped Pine Scripts into backtests and log results.

Usage:
    python scripts/run_pipeline.py                    # Process all unprocessed .pine files
    python scripts/run_pipeline.py --category top     # Process only 'top' category
    python scripts/run_pipeline.py --limit 10         # Process max 10 scripts
    python scripts/run_pipeline.py --rerun             # Re-run all (even already processed)
"""

import argparse
import json
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from framework.backtest_engine import run_multi_ticker_backtest
from framework.csv_logger import init_csv, log_multi_ticker_results
from framework.data_fetcher import fetch_all_tickers
from framework.pine_converter import convert_pine_to_python
from framework.stats_formatter import format_stats_header

CATEGORIES = [
    "editors_picks", "popular", "top", "trending",
    "oscillators", "trend_analysis", "volume",
    "moving_averages", "volatility", "momentum",
]
PIPELINE_STATE_FILE = PROJECT_ROOT / "results" / ".pipeline_state.json"


def load_pipeline_state() -> dict:
    if PIPELINE_STATE_FILE.exists():
        return json.loads(PIPELINE_STATE_FILE.read_text())
    return {"processed": [], "failed": [], "last_run": None}


def save_pipeline_state(state: dict) -> None:
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    PIPELINE_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    PIPELINE_STATE_FILE.write_text(json.dumps(state, indent=2))


def get_unprocessed_pines(category: str | None = None, rerun: bool = False) -> list[Path]:
    """Find .pine files that don't have a corresponding backtest .py file."""
    pine_dir = PROJECT_ROOT / "pinescript"
    backtest_dir = PROJECT_ROOT / "backtests"

    categories = [category] if category else CATEGORIES
    unprocessed = []

    for cat in categories:
        cat_pine_dir = pine_dir / cat
        cat_bt_dir = backtest_dir / cat

        if not cat_pine_dir.exists():
            continue

        for pine_file in sorted(cat_pine_dir.glob("*.pine")):
            bt_file = cat_bt_dir / f"{pine_file.stem}.py"
            if rerun or not bt_file.exists():
                unprocessed.append(pine_file)

    return unprocessed


def process_single_pine(pine_file: Path) -> bool:
    """Convert a single .pine file to a backtest, run it, and log results.

    Returns True on success, False on failure.
    """
    category = pine_file.parent.name
    script_name = pine_file.stem
    backtest_dir = PROJECT_ROOT / "backtests" / category
    backtest_file = backtest_dir / f"{script_name}.py"

    print(f"\n{'='*60}")
    print(f"Processing: {script_name} ({category})")
    print(f"{'='*60}")

    # Step 1: Read Pine Script
    pine_code = pine_file.read_text(encoding="utf-8")
    print(f"  Pine Script: {len(pine_code)} chars")

    # Step 2: Convert to Python (with retry on failure)
    print("  Converting Pine Script to Python...")
    try:
        python_code = convert_pine_to_python(pine_code, script_name)
    except Exception as e:
        first_error = str(e)
        print(f"  CONVERSION FAILED (attempt 1): {first_error}")
        print("  Retrying with error context...")
        try:
            python_code = convert_pine_to_python(pine_code, script_name, previous_error=first_error)
        except Exception as e2:
            print(f"  CONVERSION FAILED (attempt 2): {e2}")
            _write_error_backtest(backtest_file, script_name, f"Conversion failed after retry: {e2}")
            log_multi_ticker_results(
                script_name, category, str(backtest_file), str(pine_file),
                {"SPY": {"error": str(e2)}, "BTC": {"error": str(e2)}, "QQQ": {"error": str(e2)}},
            )
            return False

    # Step 3: Write initial backtest file (without stats — we'll update after running)
    backtest_dir.mkdir(parents=True, exist_ok=True)
    _write_backtest_file(backtest_file, script_name, python_code, stats_header="Running...")
    print(f"  Wrote backtest: {backtest_file.name}")

    # Step 4: Run backtest across all tickers
    print("  Running backtests...")
    try:
        multi_stats = run_multi_ticker_backtest(backtest_file)
    except Exception as e:
        print(f"  BACKTEST FAILED: {e}")
        traceback.print_exc()
        multi_stats = {
            "SPY": {"error": str(e)},
            "BTC": {"error": str(e)},
            "QQQ": {"error": str(e)},
        }

    # Step 5: Update backtest file with stats in docstring
    stats_header = format_stats_header(script_name, multi_stats)
    _write_backtest_file(backtest_file, script_name, python_code, stats_header=stats_header)
    print(f"  Updated backtest with stats")

    # Step 6: Log to CSV
    log_multi_ticker_results(
        script_name, category, str(backtest_file), str(pine_file), multi_stats,
    )
    print(f"  Logged to CSV")

    # Sync to Supabase (non-blocking — log errors but don't fail pipeline)
    try:
        from framework.supabase_sync import sync_pipeline_run
        sync_pipeline_run(script_name, category, multi_stats)
        print(f"  Synced to Supabase")
    except Exception as e:
        print(f"  Supabase sync skipped: {e}")

    # Notify on high Sharpe discoveries (non-blocking)
    for ticker, stats in multi_stats.items():
        if "error" not in stats:
            sharpe = stats.get("Sharpe Ratio")
            if isinstance(sharpe, (int, float)) and sharpe > 2.0:
                try:
                    from framework.notifications import notify_high_sharpe
                    notify_high_sharpe(script_name, sharpe, ticker)
                except Exception:
                    pass

    # Print summary
    for ticker, stats in multi_stats.items():
        if "error" in stats:
            print(f"    {ticker}: ERROR - {stats['error']}")
        else:
            roi = stats.get("Return [%]", "N/A")
            sharpe = stats.get("Sharpe Ratio", "N/A")
            trades = stats.get("# Trades", "N/A")
            roi_str = f"{roi:.2f}%" if isinstance(roi, (int, float)) else roi
            sharpe_str = f"{sharpe:.2f}" if isinstance(sharpe, (int, float)) else sharpe
            print(f"    {ticker}: ROI={roi_str}  Sharpe={sharpe_str}  Trades={trades}")

    return True


def _write_backtest_file(
    filepath: Path,
    script_name: str,
    python_code: str,
    stats_header: str = "",
) -> None:
    """Write a backtest .py file with stats in the docstring."""
    header = f'"""\n{stats_header}\n\nSource: TradingView Community Script — {script_name}\nGenerated by DeepStack TradingView Pipeline\n"""\n\n'
    filepath.write_text(header + python_code, encoding="utf-8")


def _write_error_backtest(filepath: Path, script_name: str, error: str) -> None:
    """Write a placeholder backtest file for a failed conversion."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    content = f'"""\nERROR: {error}\n\nSource: TradingView Community Script — {script_name}\n"""\n\n# Conversion failed — see error above\n'
    filepath.write_text(content, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="DeepStack TradingView Backtest Pipeline")
    parser.add_argument("--category", choices=CATEGORIES, help="Process only this category")
    parser.add_argument("--limit", type=int, default=0, help="Max scripts to process (0=all)")
    parser.add_argument("--rerun", action="store_true", help="Re-run even if backtest exists")
    args = parser.parse_args()

    print("DeepStack TradingView Backtest Pipeline")
    print("=" * 60)

    # Init CSV
    csv_path = init_csv()
    print(f"CSV log: {csv_path}")

    # Load pipeline state for resumable runs
    pipeline_state = load_pipeline_state()
    if pipeline_state["last_run"]:
        print(f"Resuming from previous run ({pipeline_state['last_run']})")
        print(f"  Previously processed: {len(pipeline_state['processed'])}, failed: {len(pipeline_state['failed'])}")

    # Pre-fetch data for all tickers (cached)
    print("\nFetching market data...")
    ticker_data = fetch_all_tickers()
    if not ticker_data:
        print("ERROR: Could not fetch any market data. Exiting.")
        sys.exit(1)

    # Find unprocessed Pine Scripts
    pines = get_unprocessed_pines(category=args.category, rerun=args.rerun)
    if args.limit > 0:
        pines = pines[: args.limit]

    # Filter out already-processed scripts (unless --rerun)
    if not args.rerun:
        already_done = set(pipeline_state["processed"] + pipeline_state["failed"])
        before = len(pines)
        pines = [p for p in pines if p.stem not in already_done]
        skipped = before - len(pines)
        if skipped > 0:
            print(f"Skipped {skipped} scripts from previous pipeline run")

    print(f"\nFound {len(pines)} Pine Scripts to process")

    if not pines:
        print("Nothing to do. Scrape some Pine Scripts first!")
        return

    # Process each
    success = 0
    failed = 0
    start = time.time()

    for i, pine_file in enumerate(pines, 1):
        print(f"\n[{i}/{len(pines)}]", end="")
        try:
            ok = process_single_pine(pine_file)
            if ok:
                success += 1
                pipeline_state["processed"].append(pine_file.stem)
            else:
                failed += 1
                pipeline_state["failed"].append(pine_file.stem)
        except Exception as e:
            print(f"  UNEXPECTED ERROR: {e}")
            traceback.print_exc()
            failed += 1
            pipeline_state["failed"].append(pine_file.stem)
        save_pipeline_state(pipeline_state)

    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"Pipeline complete: {success} OK, {failed} failed, {elapsed:.1f}s")
    print(f"Results: {csv_path}")
    print(f"State: {PIPELINE_STATE_FILE}")

    # Send Telegram daily summary (non-blocking)
    try:
        from framework.notifications import notify_daily_summary
        notify_daily_summary(
            total_scraped=len(pines),
            total_converted=success,
            total_failed=failed,
            elapsed_seconds=elapsed,
        )
        print("  Telegram summary sent")
    except Exception as e:
        print(f"  Telegram notification skipped: {e}")


if __name__ == "__main__":
    main()
