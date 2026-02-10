"""Update indicator rankings based on composite score.

Fetches all indicators from ds_tv_indicators, assigns rank by composite_score
(descending), updates the rank column via PostgREST, and prints a summary.

Usage:
    python scripts/update_rankings.py
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from framework.supabase_sync import _get, _patch


def update_rankings() -> list[dict]:
    """Fetch indicators, assign ranks, update in Supabase, return ranked list."""
    indicators = _get(
        "ds_tv_indicators",
        "select=id,script_name,category,composite_score,avg_sharpe,avg_roi,avg_win_rate,num_tickers_tested"
        "&order=composite_score.desc.nullslast"
    )

    if not indicators:
        print("No indicators found in ds_tv_indicators.")
        return []

    for rank, ind in enumerate(indicators, 1):
        _patch(
            "ds_tv_indicators",
            f"id=eq.{ind['id']}",
            {"rank": rank},
        )
        ind["rank"] = rank

    return indicators


def print_summary(indicators: list[dict], top_n: int = 20) -> None:
    """Print a formatted table of the top N indicators."""
    show = indicators[:top_n]

    print(f"\n{'='*90}")
    print(f"  DeepStack TradingView Indicator Rankings (Top {min(top_n, len(indicators))} of {len(indicators)})")
    print(f"{'='*90}")
    print(f"  {'Rank':<6}{'Script':<45}{'Cat':<16}{'Score':>8}{'Sharpe':>8}{'ROI%':>8}")
    print(f"  {'-'*6}{'-'*45}{'-'*16}{'-'*8}{'-'*8}{'-'*8}")

    for ind in show:
        score = ind.get("composite_score")
        sharpe = ind.get("avg_sharpe")
        roi = ind.get("avg_roi")
        score_str = f"{score:.3f}" if score is not None else "N/A"
        sharpe_str = f"{sharpe:.2f}" if sharpe is not None else "N/A"
        roi_str = f"{roi:.1f}" if roi is not None else "N/A"
        name = ind["script_name"][:43]

        print(f"  {ind['rank']:<6}{name:<45}{ind['category']:<16}{score_str:>8}{sharpe_str:>8}{roi_str:>8}")

    print(f"{'='*90}\n")


def main():
    print("Updating indicator rankings...")
    indicators = update_rankings()
    if indicators:
        print(f"Updated {len(indicators)} indicator ranks.")
        print_summary(indicators)
    else:
        print("Nothing to rank.")


if __name__ == "__main__":
    main()
