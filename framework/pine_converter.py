"""Convert Pine Script to Python backtesting.py Strategy using OpenClaw's AI models.

Supports multiple AI providers configured in .env:
- OPENAI_API_KEY: GPT models (gpt-4, gpt-3.5-turbo)
- GEMINI_API_KEY: Google Gemini (gemini-pro)
- ZHIPU_API_KEY: zhipu AI (glm-4-flash)
- ANTHROPIC_API_KEY: Anthropic Claude (claude-haiku, fallback)
"""

import os
import re

# Load .env file if it exists
def load_env():
    """Load environment variables from .env file."""
    env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # Set environment variable if not already set
                    if key not in os.environ:
                        os.environ[key] = value

load_env()

# Configuration from environment (now loaded from .env)
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic").lower()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
ZHIPU_API_KEY = os.environ.get("ZHIPU_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# OpenClaw model configuration
DEFAULT_MODEL = os.environ.get("OPENCLAW_DEFAULT_MODEL", "gpt-4o-mini")

# Model mapping for each provider
MODELS = {
    "openai": {
        "default": "gpt-4o-mini",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
    },
    "anthropic": {
        "default": "claude-haiku-4-5-20251001",
        "models": ["claude-haiku-4-5-20251001", "claude-3-5-haiku-20241022"]
    },
    "gemini": {
        "default": "gemini-1.5-flash",
        "models": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
    },
    "zhipu": {
        "default": "glm-4-flash",
        "models": ["glm-4-flash", "glm-4-air", "glm-4"]
    }
}

CONVERSION_PROMPT = """You are a Pine Script to Python converter for algorithmic trading backtests.

Given the following Pine Script indicator or strategy from TradingView, generate a COMPLETE, RUNNABLE Python backtest file using `backtesting.py` library.

REQUIREMENTS:
1. Import from backtesting: `from backtesting import Backtest, Strategy`
2. Import from backtesting.lib: `from backtesting.lib import crossover` (if needed)
3. Use `pandas_ta` for indicator calculations (import as `import pandas_ta as pta`)
4. Import pandas and numpy as needed
5. Define a Strategy class with `init()` and `next()` methods
6. The Strategy class MUST be named `TvStrategy`

TRADING RULES:
- If Pine Script IS a strategy (has strategy.entry/exit), replicate its entry/exit logic
- If Pine Script is ONLY an indicator, create reasonable trading rules:
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
- Never use `len(self)`. Always use `len(self.data)` or `len(self.data.Close)` to get the number of bars.
- pandas_ta does NOT have `highest()` or `lowest()` functions. Instead use: `df['High'].rolling(n).max()` for highest high, and `df['Low'].rolling(n).min()` for lowest low. Wrap these in self.I() lambda calls.
- Always check if indicator calculation returns None before using it. Some pandas_ta functions return None for insufficient data. Use `if result is not None:` guards, and for self.I() wrappers, provide a fallback: `self.I(lambda: pta.rsi(close, length=14) or pd.Series(50, index=close.index))`
- Do NOT use pta.supertrend() as it may not exist in all versions. Instead implement supertrend manually using ATR. Also avoid pta.ichimoku() — use manual calculation with rolling means.

TEMPLATE:
```python
import numpy as np
import pandas as pd
import pandas_ta as pta
from backtesting import Backtest, Strategy
from backtesting.lib import crossover


class TvStrategy(Strategy):
    # Default parameters from Pine Script
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


def _get_model_name() -> str:
    """Get the model name based on provider and configuration."""
    # Check if user specified a model
    if DEFAULT_MODEL:
        return DEFAULT_MODEL

    # Use default for the provider
    provider_config = MODELS.get(LLM_PROVIDER, MODELS["anthropic"])
    return provider_config["default"]


def _call_openai(prompt: str) -> str:
    """Call OpenAI API (GPT models)."""
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("OpenAI package not installed. Run: pip install openai")

    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set in .env")

    client = OpenAI(api_key=OPENAI_API_KEY)
    model = _get_model_name()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert at converting Pine Script to Python code."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=4096,
        temperature=0.7,
    )

    return response.choices[0].message.content


def _call_anthropic(prompt: str) -> str:
    """Call Anthropic API (Claude models)."""
    try:
        from anthropic import Anthropic
    except ImportError:
        raise RuntimeError("Anthropic package not installed. Run: pip install anthropic")

    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set in .env")

    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    model = _get_model_name()

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text


def _call_gemini(prompt: str) -> str:
    """Call Google Gemini API."""
    try:
        import google.generativeai as genai
    except ImportError:
        raise RuntimeError("Google Generative AI package not installed. Run: pip install google-generativeai")

    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set in .env")

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(_get_model_name())

    response = model.generate_content(prompt)
    return response.text


def _call_zhipu(prompt: str) -> str:
    """Call zhipu AI API (GLM models)."""
    try:
        from zhipuai import ZhipuAI
    except ImportError:
        raise RuntimeError("ZhipuAI package not installed. Run: pip install zhipuai")

    if not ZHIPU_API_KEY:
        raise RuntimeError("ZHIPU_API_KEY not set in .env")

    client = ZhipuAI(api_key=ZHIPU_API_KEY)
    model = _get_model_name()

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096,
        temperature=0.7,
    )

    return response.choices[0].message.content


def convert_pine_to_python(
    pine_code: str,
    script_name: str = "unknown",
    previous_error: str | None = None,
) -> str:
    """Convert Pine Script to a Python backtesting.py Strategy file.

    Args:
        pine_code: Raw Pine Script source code
        script_name: Name of the TradingView script (for docstring)
        previous_error: If retrying, error from the previous attempt

    Returns:
        Complete Python source code string
    """
    prompt_content = CONVERSION_PROMPT.replace("{pine_code}", pine_code)
    if previous_error:
        prompt_content += f"\n\nPREVIOUS ATTEMPT FAILED WITH ERROR: {previous_error}\nPlease fix the issue and try again."

    # Call the appropriate API based on provider
    try:
        if LLM_PROVIDER == "openai":
            raw_code = _call_openai(prompt_content)
        elif LLM_PROVIDER == "anthropic":
            raw_code = _call_anthropic(prompt_content)
        elif LLM_PROVIDER == "gemini":
            raw_code = _call_gemini(prompt_content)
        elif LLM_PROVIDER == "zhipu":
            raw_code = _call_zhipu(prompt_content)
        else:
            raise RuntimeError(f"Unsupported LLM provider: {LLM_PROVIDER}. Choose from: openai, anthropic, gemini, zhipu")
    except Exception as e:
        # Fallback to Anthropic if configured
        if ANTHROPIC_API_KEY and LLM_PROVIDER != "anthropic":
            print(f"[pine_converter] Primary provider ({LLM_PROVIDER}) failed: {e}")
            print(f"[pine_converter] Falling back to Anthropic...")
            raw_code = _call_anthropic(prompt_content)
        else:
            raise

    raw_code = raw_code.strip()

    # Strip markdown fences if present
    raw_code = _strip_code_fences(raw_code)

    # Validate it at least has a Strategy class
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
