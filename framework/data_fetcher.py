"""Fetch OHLCV data from Yahoo Finance for backtesting."""

import yfinance as yf
import pandas as pd
from pathlib import Path

TICKERS = {
    "SPY": "SPY",
    "BTC": "BTC-USD",
    "QQQ": "QQQ",
}

CACHE_DIR = Path(__file__).parent.parent / "results" / ".data_cache"


def fetch_ohlcv(
    ticker_key: str,
    period: str = "2y",
    interval: str = "1d",
    use_cache: bool = True,
) -> pd.DataFrame:
    """Fetch OHLCV data for a ticker.

    Args:
        ticker_key: Key from TICKERS dict (SPY, BTC, QQQ)
        period: yfinance period string (default 2y)
        interval: yfinance interval string (default 1d)
        use_cache: Cache data to disk to avoid repeated API calls

    Returns:
        DataFrame with columns: Open, High, Low, Close, Volume (capitalized)
    """
    yf_symbol = TICKERS.get(ticker_key, ticker_key)
    cache_file = CACHE_DIR / f"{ticker_key}_{period}_{interval}.parquet"

    if use_cache and cache_file.exists():
        df = pd.read_parquet(cache_file)
        if len(df) > 0:
            return df

    df = yf.download(yf_symbol, period=period, interval=interval, progress=False)

    if df.empty:
        raise ValueError(f"No data returned for {yf_symbol}")

    # Flatten multi-level columns if present (yfinance >= 0.2.30)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Keep only required columns, ensure capitalized names
    required = ["Open", "High", "Low", "Close", "Volume"]
    for col in required:
        if col not in df.columns:
            col_lower = col.lower()
            if col_lower in df.columns:
                df.rename(columns={col_lower: col}, inplace=True)

    df = df[required].copy()
    df.dropna(inplace=True)

    # Cache
    if use_cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache_file)

    return df


def fetch_all_tickers(period: str = "2y", interval: str = "1d") -> dict[str, pd.DataFrame]:
    """Fetch OHLCV data for all configured tickers."""
    data = {}
    for key in TICKERS:
        try:
            data[key] = fetch_ohlcv(key, period=period, interval=interval)
            print(f"  Fetched {key}: {len(data[key])} bars")
        except Exception as e:
            print(f"  Failed to fetch {key}: {e}")
    return data
