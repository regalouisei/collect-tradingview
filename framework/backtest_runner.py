"""Python backtesting engine with multi-ticker support.

Supports:
- Multi-ticker backtesting (SPY, BTC-USD, QQQ)
- Robust error handling for syntax errors
- Compatibility with Python 3.12

Usage:
    python framework/backtest_runner.py
"""

import json
import os
import sys
from pathlib import Path
import traceback

PROJECT_ROOT = Path(__file__).parent.parent
PINE_DIR = PROJECT_ROOT / "pinescript"
BACKTEST_DIR = PROJECT_ROOT / "backtests"
RESULTS_FILE = PROJECT_ROOT / "results" / "backtest_results.csv"

# Import backtesting
try:
    from backtesting import Backtest, Strategy
    from backtesting.lib import crossover
except ImportError:
    raise RuntimeError("backtesting package not installed. Run: pip install backtesting")

# Import data fetching
try:
    import yfinance as yf
    import pandas as pd
    import pandas_ta as pta
    from pandas_ta.overlap import hl2
except ImportError as e:
    raise RuntimeError(f"Required package not installed: {e}. Run: pip install {e.name}")

# Define tickers
TICKERS = {
    "SPY": "SPY",
    "BTC": "BTC-USD",
    "QQQ": "QQQ",
}


def fetch_market_data(ticker: str, period: str = "2y") -> pd.DataFrame:
    """Fetch OHLC data for a ticker.

    Args:
        ticker: Ticker symbol
        period: Data period (default: 2y)

    Returns:
        DataFrame with OHLCV data
    """
    try:
        data = yf.download(ticker, period=period, progress=False)

        # Validate data
        if data.empty or len(data) < 200:
            print(f"  ERROR: Insufficient data for {ticker}")
            return None

        # Check required columns
        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in data.columns for col in required):
            print(f"  ERROR: Missing required columns for {ticker}")
            return None

        # Clean data
        data = data.dropna()
        data = data.sort_index()

        return data

    except Exception as e:
        print(f"  ERROR: Failed to fetch {ticker}: {e}")
        return None


def load_strategy_from_file(strategy_file: Path) -> type[Strategy]:
    """Load Strategy class from file with robust error handling.

    Args:
        strategy_file: Path to Python strategy file

    Returns:
        Strategy class

    Raises:
        ValueError: If file doesn't contain a Strategy subclass
    """
    try:
        # Read file content
        code = strategy_file.read_text(encoding='utf-8')

        # Create a namespace for execution
        import types
        namespace = types.SimpleNamespace()

        # Execute the code in the namespace
        exec(code, namespace)

        # Find all classes in the namespace
        classes = [obj for name, obj in namespace.__dict__.items()
                  if isinstance(obj, type) and issubclass(obj, Strategy)]

        if not classes:
            raise ValueError(f"No Strategy subclass found in {strategy_file}")

        # Return the first Strategy class found
        return classes[0]

    except SyntaxError as e:
        raise ValueError(f"Syntax error in {strategy_file}: {e}")
    except Exception as e:
        raise ValueError(f"Failed to load {strategy_file}: {e}")


def run_single_ticker_backtest(strategy_file: Path, ticker: str) -> dict:
    """Run backtest for a single ticker.

    Args:
        strategy_file: Path to Python strategy file
        ticker: Ticker symbol

    Returns:
        Dict with backtest results
    """
    try:
        # Load strategy
        strategy_class = load_strategy_from_file(strategy_file)

        # Fetch data
        data = fetch_market_data(ticker)
        if data is None:
            return {
                "ticker": ticker,
                "error": "Failed to fetch data",
                "roi_pct": None,
                "max_drawdown_pct": None,
                "sharpe_ratio": None,
                "sortino_ratio": None,
                "expectancy_pct": None,
                "num_trades": None,
                "win_rate_pct": None,
                "profit_factor": None,
            }

        # Initialize backtest
        bt = Backtest(
            strategy_class,
            data=data,
            cash=10000.0,
            commission=0.0002,
            exclusive_orders=True,
        )

        # Run backtest
        stats = bt.run()

        # Calculate metrics
        roi_pct = (stats['Equity Final'][-1] / stats['Equity Final'][0] - 1) * 100
        max_drawdown_pct = stats['Max Drawdown [%]'][-1]
        sharpe_ratio = stats['Sharpe Ratio'][-1]
        sortino_ratio = stats['Sortino Ratio'][-1]
        num_trades = len(stats['# Trades']) - 1 if len(stats['# Trades']) > 0 else 0

        if num_trades > 0:
            wins = len(stats[stats['_trades']['Exit'] == 0]) if '# Trades' in stats else 0
            win_rate_pct = (wins / num_trades) * 100
        else:
            win_rate_pct = 0.0

        # Profit Factor
        gross_profit = 0.0
        gross_loss = 0.0
        if '# Trades' in stats:
            for trade in stats['_trades']:
                if trade['PnL'] is not None:
                    if trade['PnL'] > 0:
                        gross_profit += trade['PnL']
                    else:
                        gross_loss += abs(trade['PnL'])

        profit_factor = (gross_profit / abs(gross_loss)) if gross_loss != 0 else 0.0
        expectancy_pct = ((gross_profit - gross_loss) / abs(gross_loss)) * 100 if gross_loss != 0 else 0.0

        return {
            "ticker": ticker,
            "backtest_file": str(strategy_file),
            "pine_file": str(strategy_file).replace("backtests/", "pinescript/").replace(".py", ".pine"),
            "roi_pct": float(roi_pct) if roi_pct is not None else None,
            "max_drawdown_pct": float(max_drawdown_pct) if max_drawdown_pct is not None else None,
            "sharpe_ratio": float(sharpe_ratio) if sharpe_ratio is not None else None,
            "sortino_ratio": float(sortino_ratio) if sortino_ratio is not None else None,
            "expectancy_pct": float(expectancy_pct) if expectancy_pct is not None else None,
            "num_trades": num_trades,
            "win_rate_pct": float(win_rate_pct) if win_rate_pct is not None else None,
            "profit_factor": float(profit_factor) if profit_factor is not None else None,
            "error": None,
        }

    except Exception as e:
        return {
            "ticker": ticker,
            "backtest_file": str(strategy_file),
            "pine_file": str(strategy_file).replace("backtests/", "pinescript/").replace(".py", ".pine"),
            "error": str(e),
            "roi_pct": None,
            "max_drawdown_pct": None,
            "sharpe_ratio": None,
            "sortino_ratio": None,
            "expectancy_pct": None,
            "num_trades": None,
            "win_rate_pct": None,
            "profit_factor": None,
        }


def run_multi_ticker_backtest(strategy_file: Path) -> list[dict]:
    """Run backtest for multiple tickers.

    Args:
        strategy_file: Path to Python strategy file

    Returns:
        List of backtest results for each ticker
    """
    results = []

    for ticker in TICKERS.values():
        print(f"\n  Testing {ticker}...")
        result = run_single_ticker_backtest(strategy_file, ticker)
        results.append(result)

        if result['error']:
            print(f"    ❌ {result['error']}")
        else:
            print(f"    ✅ ROI: {result['roi_pct']:.2f}% | Sharpe: {result['sharpe_ratio']:.2f} | Trades: {result['num_trades']}")

    return results


def save_results(results: list[dict], strategy_file: Path):
    """Save backtest results to CSV file.

    Args:
        results: List of backtest results
        strategy_file: Path to Python strategy file
    """
    script_name = strategy_file.stem
    category = strategy_file.parent.name

    # CSV header
    csv_headers = [
        'script_name', 'category', 'ticker', 'backtest_file', 'pine_file',
        'roi_pct', 'max_drawdown_pct', 'sharpe_ratio', 'sortino_ratio',
        'expectancy_pct', 'num_trades', 'win_rate_pct', 'profit_factor', 'error'
    ]

    # Load existing results if file exists
    existing_results = []
    if RESULTS_FILE.exists():
        import csv
        with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            existing_results = [row for row in reader]

    # Combine results
    all_results = existing_results + results

    # Save to CSV
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=csv_headers)
        writer.writeheader()
        for result in all_results:
            # Ensure category is set
            if 'category' not in result:
                result['category'] = category
            writer.writerow(result)

    print(f"\nSaved {len(results)} results to {RESULTS_FILE}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Run backtests on all Python strategies")
    parser.add_argument("--strategy_file", type=str, help="Specific strategy file to backtest")
    parser.add_argument("--limit", type=int, default=0, help="Max strategies to backtest")
    args = parser.parse_args()

    # Find all Python strategy files
    if args.strategy_file:
        strategy_files = [Path(args.strategy_file)]
    else:
        strategy_files = list(BACKTEST_DIR.rglob("*.py"))

    if args.limit > 0:
        strategy_files = strategy_files[:args.limit]

    print("=" * 60)
    print("Multi-Ticker Backtest Runner")
    print("=" * 60)
    print(f"\nFound {len(strategy_files)} Python strategy files")
    print(f"Testing on tickers: {list(TICKERS.values())}")

    # Process each strategy
    all_results = []
    for i, strategy_file in enumerate(strategy_files, 1):
        script_name = strategy_file.stem
        category = strategy_file.parent.name

        print(f"\n[{i}/{len(strategy_files)}] {script_name} ({category})")

        try:
            results = run_multi_ticker_backtest(strategy_file)
            save_results(results, strategy_file)

            # Summary
            successful = sum(1 for r in results if not r['error'])
            print(f"  Successful: {successful}/{len(results)}")

        except Exception as e:
            print(f"  ❌ Failed: {e}")
            traceback.print_exc()

    # Overall summary
    print("\n" + "=" * 60)
    print("BACKTEST COMPLETE")
    print("=" * 60)
    print(f"\nTotal results: {len(all_results)}")
    print(f"Saved to: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
