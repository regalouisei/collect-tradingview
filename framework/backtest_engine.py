"""Run backtests using backtesting.py and collect stats."""

import importlib.util
import sys
import traceback
from pathlib import Path
from typing import Any

import pandas as pd
from backtesting import Backtest

from .data_fetcher import fetch_ohlcv, TICKERS


def load_strategy_from_file(filepath: str | Path):
    """Dynamically load a Strategy class from a Python backtest file.

    The file must define a class that inherits from backtesting.Strategy.
    """
    filepath = Path(filepath)
    spec = importlib.util.spec_from_file_location(filepath.stem, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[filepath.stem] = module
    spec.loader.exec_module(module)

    # Find the Strategy subclass
    from backtesting import Strategy as BaseStrategy

    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if (
            isinstance(attr, type)
            and issubclass(attr, BaseStrategy)
            and attr is not BaseStrategy
        ):
            return attr

    raise ValueError(f"No Strategy subclass found in {filepath}")


def run_backtest(
    strategy_class,
    data: pd.DataFrame,
    cash: float = 100_000,
    commission: float = 0.001,
) -> dict[str, Any]:
    """Run a single backtest and return stats as a dict.

    Args:
        strategy_class: A backtesting.Strategy subclass
        data: OHLCV DataFrame
        cash: Starting capital
        commission: Commission rate (0.001 = 0.1%)

    Returns:
        Dict of stats from backtesting.py
    """
    try:
        bt = Backtest(
            data,
            strategy_class,
            cash=cash,
            commission=commission,
            exclusive_orders=True,
        )
        stats = bt.run()
        return _stats_to_dict(stats)
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


def run_multi_ticker_backtest(
    strategy_file: str | Path,
    cash: float = 100_000,
    commission: float = 0.001,
) -> dict[str, dict[str, Any]]:
    """Run a backtest across all configured tickers (SPY, BTC, QQQ).

    Args:
        strategy_file: Path to the Python backtest file
        cash: Starting capital per ticker
        commission: Commission rate

    Returns:
        Dict mapping ticker_key -> stats_dict
    """
    strategy_class = load_strategy_from_file(strategy_file)
    results = {}

    for ticker_key in TICKERS:
        try:
            data = fetch_ohlcv(ticker_key)
            stats = run_backtest(strategy_class, data, cash=cash, commission=commission)
            stats["ticker"] = ticker_key
            results[ticker_key] = stats
            status = "OK" if "error" not in stats else f"ERROR: {stats['error']}"
            print(f"    {ticker_key}: {status}")
        except Exception as e:
            results[ticker_key] = {"error": str(e), "ticker": ticker_key}
            print(f"    {ticker_key}: ERROR - {e}")

    return results


def _stats_to_dict(stats) -> dict[str, Any]:
    """Convert backtesting.py Stats object to a plain dict."""
    keys = [
        "Start",
        "End",
        "Duration",
        "Exposure Time [%]",
        "Equity Final [$]",
        "Equity Peak [$]",
        "Return [%]",
        "Buy & Hold Return [%]",
        "Return (Ann.) [%]",
        "Volatility (Ann.) [%]",
        "Sharpe Ratio",
        "Sortino Ratio",
        "Calmar Ratio",
        "Max. Drawdown [%]",
        "Avg. Drawdown [%]",
        "Max. Drawdown Duration",
        "Avg. Drawdown Duration",
        "# Trades",
        "Win Rate [%]",
        "Best Trade [%]",
        "Worst Trade [%]",
        "Avg. Trade [%]",
        "Max. Trade Duration",
        "Avg. Trade Duration",
        "Profit Factor",
        "Expectancy [%]",
        "SQN",
    ]
    result = {}
    for key in keys:
        try:
            val = stats[key]
            # Convert non-serializable types
            if hasattr(val, "total_seconds"):
                val = str(val)
            elif hasattr(val, "item"):
                val = val.item()
            result[key] = val
        except (KeyError, IndexError):
            result[key] = None
    return result
