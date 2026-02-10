"""Convert Pine Script to Python backtesting.py Strategy using Claude Haiku."""

import os
import re

from anthropic import Anthropic

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

CONVERSION_PROMPT = """You are a Pine Script to Python converter for algorithmic trading backtests.

Given the following Pine Script indicator or strategy from TradingView, generate a COMPLETE, RUNNABLE Python backtest file using the `backtesting.py` library.

REQUIREMENTS:
1. Import from backtesting: `from backtesting import Backtest, Strategy`
2. Import from backtesting.lib: `from backtesting.lib import crossover` (if needed)
3. Use `pandas_ta` for indicator calculations (import as `import pandas_ta as pta`)
4. Import pandas and numpy as needed
5. Define a Strategy class with `init()` and `next()` methods
6. The Strategy class MUST be named `TvStrategy`

TRADING RULES:
- If the Pine Script IS a strategy (has strategy.entry/exit), replicate its entry/exit logic
- If the Pine Script is ONLY an indicator, create reasonable trading rules:
  - For moving averages: buy on fast crossing above slow, sell on fast crossing below slow
  - For oscillators (RSI, Stochastic): buy when oversold and turning up, sell when overbought and turning down
  - For bands (Bollinger, Keltner): buy on lower band touch with reversal, sell on upper band touch
  - For volume indicators: use as confirmation with price trend
  - For custom indicators: analyze the signal logic and create appropriate entry/exit rules

INDICATOR MAPPING (Pine Script -> pandas_ta):
- ta.sma(src, len) -> pta.sma(close, length=len)
- ta.ema(src, len) -> pta.ema(close, length=len)
- ta.rsi(src, len) -> pta.rsi(close, length=len)
- ta.macd(src, fast, slow, signal) -> pta.macd(close, fast=fast, slow=slow, signal=signal)
- ta.bb(src, len, mult) -> pta.bbands(close, length=len, std=mult)
- ta.stoch(high, low, close, k, d, smooth) -> pta.stoch(high, low, close, k=k, d=d, smooth_k=smooth)
- ta.atr(len) -> pta.atr(high, low, close, length=len)
- ta.adx(len) -> pta.adx(high, low, close, length=len)
- ta.cci(src, len) -> pta.cci(high, low, close, length=len)
- ta.supertrend(factor, atrPeriod) -> pta.supertrend(high, low, close, length=atrPeriod, multiplier=factor)
- ta.wma(src, len) -> pta.wma(close, length=len)
- ta.vwma(src, len) -> pta.vwma(close, volume, length=len)
- ta.dmi(len, smooth) -> pta.adx(high, low, close, length=len)

IMPORTANT RULES:
- Use self.I() wrapper for ALL indicator calculations in init()
- Access data via self.data.Close, self.data.Open, self.data.High, self.data.Low, self.data.Volume
- In init(), pass pandas Series: pd.Series(self.data.Close)
- In next(), access current values via self.indicator_name[-1] (last value)
- For crossover detection, use backtesting.lib.crossover()
- Use self.buy() and self.sell() for entries (no position sizing needed)
- DO NOT use self.position.close() — use self.sell() to exit longs, self.buy() to exit shorts
- Keep it simple — no optimization parameters, just the raw indicator logic
- If the indicator requires Volume data, access via self.data.Volume

TEMPLATE:
```python
import numpy as np
import pandas as pd
import pandas_ta as pta
from backtesting import Backtest, Strategy
from backtesting.lib import crossover


class TvStrategy(Strategy):
    # Default parameters from the Pine Script
    param1 = 14  # example

    def init(self):
        close = pd.Series(self.data.Close)
        # Calculate indicators using self.I() wrapper
        self.indicator = self.I(pta.rsi, close, length=self.param1)

    def next(self):
        # Trading logic
        if crossover(self.indicator, 30):
            self.buy()
        elif crossover(70, self.indicator):
            self.sell()
```

Return ONLY the Python code. No explanations, no markdown fences, no comments about the conversion.

PINE SCRIPT:
{pine_code}"""


def convert_pine_to_python(
    pine_code: str,
    script_name: str = "unknown",
) -> str:
    """Convert Pine Script to a Python backtesting.py Strategy file.

    Args:
        pine_code: Raw Pine Script source code
        script_name: Name of the TradingView script (for the docstring)

    Returns:
        Complete Python source code string
    """
    if not ANTHROPIC_API_KEY:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set. Export it or add to .env"
        )

    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": CONVERSION_PROMPT.replace("{pine_code}", pine_code),
            }
        ],
    )

    raw_code = response.content[0].text.strip()

    # Strip markdown fences if present
    raw_code = _strip_code_fences(raw_code)

    # Validate it at least has the Strategy class
    if "class TvStrategy" not in raw_code:
        # Try to find any Strategy subclass and rename it
        match = re.search(r"class (\w+)\(Strategy\)", raw_code)
        if match:
            raw_code = raw_code.replace(match.group(1), "TvStrategy")
        else:
            raise ValueError(
                f"Conversion failed for {script_name}: no Strategy class found in output"
            )

    return raw_code


def _strip_code_fences(code: str) -> str:
    """Remove markdown code fences from LLM output."""
    # Remove ```python ... ``` wrapping
    code = re.sub(r"^```(?:python)?\s*\n", "", code)
    code = re.sub(r"\n```\s*$", "", code)
    return code.strip()
