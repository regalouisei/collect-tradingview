"""Format backtest stats for embedding in Python file docstrings."""

from typing import Any


def format_stats_header(
    script_name: str,
    multi_stats: dict[str, dict[str, Any]],
) -> str:
    """Generate a formatted stats block for the top of a backtest file.

    This goes inside triple-quotes at the top of each generated backtest .py file
    so you can open the file and immediately see performance.

    Args:
        script_name: Name of the TradingView indicator/strategy
        multi_stats: Dict mapping ticker -> stats dict

    Returns:
        Formatted multi-line string with full stats
    """
    lines = []
    lines.append(f"DS-TV Backtest Results: {script_name}")
    lines.append("=" * 60)
    lines.append("")

    for ticker, stats in multi_stats.items():
        lines.append(f"--- {ticker} ---")

        if "error" in stats:
            lines.append(f"  ERROR: {stats['error']}")
            lines.append("")
            continue

        stat_rows = [
            ("Return", "Return [%]", "%"),
            ("Buy & Hold Return", "Buy & Hold Return [%]", "%"),
            ("Max Drawdown", "Max. Drawdown [%]", "%"),
            ("Sharpe Ratio", "Sharpe Ratio", ""),
            ("Sortino Ratio", "Sortino Ratio", ""),
            ("Calmar Ratio", "Calmar Ratio", ""),
            ("Profit Factor", "Profit Factor", ""),
            ("Expectancy", "Expectancy [%]", "%"),
            ("SQN", "SQN", ""),
            ("# Trades", "# Trades", ""),
            ("Win Rate", "Win Rate [%]", "%"),
            ("Best Trade", "Best Trade [%]", "%"),
            ("Worst Trade", "Worst Trade [%]", "%"),
            ("Avg Trade", "Avg. Trade [%]", "%"),
            ("Exposure Time", "Exposure Time [%]", "%"),
            ("Equity Final", "Equity Final [$]", "$"),
            ("Equity Peak", "Equity Peak [$]", "$"),
            ("Avg Drawdown", "Avg. Drawdown [%]", "%"),
            ("Max Drawdown Duration", "Max. Drawdown Duration", ""),
            ("Max Trade Duration", "Max. Trade Duration", ""),
            ("Avg Trade Duration", "Avg. Trade Duration", ""),
            ("Ann. Return", "Return (Ann.) [%]", "%"),
            ("Ann. Volatility", "Volatility (Ann.) [%]", "%"),
        ]

        for label, key, suffix in stat_rows:
            val = stats.get(key)
            if val is None:
                continue
            if isinstance(val, float):
                formatted = f"{val:.2f}{suffix}"
            else:
                formatted = f"{val}{suffix}"
            lines.append(f"  {label:<25} {formatted}")

        lines.append("")

    lines.append("=" * 60)
    lines.append("Unoptimized run. No parameter tuning applied.")
    return "\n".join(lines)
