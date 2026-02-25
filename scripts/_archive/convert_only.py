"""Pine Script to Python converter (no backtesting).

This script only converts Pine Scripts to Python, without running backtests.

Usage:
    python scripts/convert_only.py --limit 50
    python scripts/convert_only.py --category oscillators
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional
import hashlib

PROJECT_ROOT = Path(__file__).parent.parent
PINE_DIR = PROJECT_ROOT / "pinescript"
PYTHON_DIR = PROJECT_ROOT / "backtests"  # Still save Python files here
ENV_FILE = PROJECT_ROOT / ".env"
HASHES_FILE = PROJECT_ROOT / "results" / ".script_hashes.json"
STATE_FILE = PROJECT_ROOT / "results" / ".conversion_state.json"

# Load environment variables
if ENV_FILE.exists():
    for line in ENV_FILE.read_text().splitlines():
        if line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        os.environ[key.strip()] = value.strip()

# Configuration
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'zhipu')  # Default to zhipu
DEFAULT_MODEL = os.getenv('OPENCLAW_DEFAULT_MODEL', 'glm-4.7')

# API Keys
ZHIPU_API_KEY = os.getenv('ZHIPU_API_KEY', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# Provider configurations
MODELS = {
    "openai": {
        "default": "gpt-4o-mini",
        "api_key_env": "OPENAI_API_KEY"
    },
    "anthropic": {
        "default": "claude-haiku-4-5-20251001",
        "api_key_env": "ANTHROPIC_API_KEY"
    },
    "gemini": {
        "default": "gemini-1.5-flash",
        "api_key_env": "GEMINI_API_KEY"
    },
    "zhipu": {
        "default": "glm-4.7",
        "api_key_env": "ZHIPU_API_KEY"
    }
}

# Conversion Prompt (IMPROVED - No backtesting)
CONVERSION_PROMPT = """You are a Pine Script to Python converter for algorithmic trading strategies.

Given the following Pine Script indicator or strategy from TradingView, generate a COMPLETE Python trading class that implements the same logic.

REQUIREMENTS:
1. Import from backtesting: `from backtesting import Strategy`
2. Import from backtesting.lib: `from backtesting.lib import crossover` (if needed)
3. Use `pandas_ta` for indicator calculations (import as `import pandas_ta as pta`)
4. Import pandas and numpy as needed
5. Define a Strategy class with `__init__()` and `next()` methods
6. The Strategy class MUST be named `TvStrategy`

TRADING RULES:
- If Pine Script IS a strategy (has strategy.entry/exit), replicate its entry/exit logic
- If Pine Script is ONLY an indicator, create reasonable trading rules:
  - For moving averages: buy on fast crossing above slow, sell on fast crossing below slow
  - For oscillators (RSI, Stochastic): buy when oversold and turning up, sell when overbought and turning down
  - For bands (Bollinger, Keltner): buy on lower band touch with reversal, sell on upper band touch
  - For volume indicators: use as confirmation with price trend
  - For custom indicators: analyze signal logic and create appropriate entry/exit rules

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
- Use self.I() wrapper for ALL indicator calculations in __init__()
- Access data via self.data.Close, self.data.Open, self.data.High, self.data.Low, self.data.Volume
- In __init__(), pass pandas Series: pd.Series(self.data.Close)
- In next(), access current values via self.indicator_name[-1] (last value)
- For crossover detection, use backtesting.lib.crossover()
- Use self.buy() and self.sell() for entries (no position sizing needed)
- DO NOT use self.position.close() — use self.sell() to exit longs, self.buy() to exit shorts
- Keep it simple — no optimization parameters, just raw indicator logic
- If indicator requires Volume data, access via self.data.Volume
- Never use `len(self)`. Always use `len(self.data)` or `len(self.data.Close)` to get the number of bars.
- pandas_ta does NOT have `highest()` or `lowest()` functions. Instead use: `df['High'].rolling(n).max()` for highest high, and `df['Low'].rolling(n).min()` for lowest low. Wrap these in self.I() lambda calls.
- Always check if indicator calculation returns None before using it. Some pandas_ta functions return None for insufficient data. Use `if result is not None:` guards, and for self.I() wrappers, provide a fallback: `self.I(lambda: pta.rsi(close, length=14) or pd.Series(50, index=close.index))`
- Do NOT use pta.supertrend() as it may not exist in all versions. Instead implement supertrend manually using ATR. Also avoid pta.ichimoku() — use manual calculation with rolling means.
- **CRITICAL**: All indicator functions MUST return numpy arrays or pandas Series, NEVER return None. Use self.I() with proper fallback values.
- **CRITICAL**: Never use `lambda` keyword inside self.I() wrappers. Instead define helper functions in __init__() and call them.

TEMPLATE:
```python
import numpy as np
import pandas as pd
import pandas_ta as pta
from backtesting import Strategy
from backtesting.lib import crossover


class TvStrategy(Strategy):
    # Default parameters from Pine Script
    param1 = 14  # example

    def __init__(self):
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

Return ONLY of Python code. No explanations, no markdown fences, no comments about the conversion.

PINE SCRIPT:
{pine_code}
"""


def _get_model_name() -> str:
    """Get model name based on provider and configuration."""
    # Check if user specified a model
    if DEFAULT_MODEL:
        return DEFAULT_MODEL

    # Use default for provider
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
        messages=[{"role": "user", "content": prompt}],
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
        raise RuntimeError("Gemini package not installed. Run: pip install google-generativeai")

    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set in .env")

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(_get_model_name())

    response = model.generate_content(prompt)
    return response.text


def _call_zhipu(prompt: str) -> str:
    """Call Zhipu AI API (GLM models)."""
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
    previous_error: Optional[str] = None,
) -> str:
    """Convert Pine Script to a Python trading Strategy file.

    Args:
        pine_code: Raw Pine Script source code
        script_name: Name of TradingView script (for docstring)
        previous_error: If retrying, error from previous attempt

    Returns:
        Complete Python source code string
    """
    prompt_content = CONVERSION_PROMPT.replace("{pine_code}", pine_code)
    if previous_error:
        prompt_content += f"\n\nPREVIOUS ATTEMPT FAILED WITH ERROR: {previous_error}\nPlease fix the issue and try again."

    # Call appropriate API based on provider
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
            raise RuntimeError(f"Unknown LLM provider: {LLM_PROVIDER}")

    except Exception as e:
        raise RuntimeError(f"LLM API call failed: {e}")

    return raw_code


def load_hashes() -> dict:
    """Load script content hashes for deduplication."""
    if HASHES_FILE.exists():
        return json.loads(HASHES_FILE.read_text())
    return {}


def save_hashes(hashes: dict):
    """Save script content hashes."""
    HASHES_FILE.parent.mkdir(parents=True, exist_ok=True)
    HASHES_FILE.write_text(json.dumps(hashes, indent=2))


def compute_content_hash(pine_code: str) -> str:
    """Compute SHA256 hash of Pine Script content."""
    return hashlib.sha256(pine_code.encode('utf-8')).hexdigest()


def is_duplicate(pine_code: str, hashes: dict) -> bool:
    """Check if script content is a duplicate."""
    content_hash = compute_content_hash(pine_code)
    return content_hash in hashes.values()


def load_conversion_state() -> dict:
    """Load conversion state."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"converted": [], "failed": [], "last_run": None}


def save_conversion_state(state: dict):
    """Save conversion state."""
    from datetime import datetime
    state["last_run"] = datetime.now().isoformat()
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def convert_single_script(pine_file: Path) -> tuple[Path, str]:
    """Convert a single Pine Script file to Python.

    Args:
        pine_file: Path to Pine Script file

    Returns:
        Tuple of (python_file_path, error_message)
    """
    try:
        # Read Pine Script
        pine_code = pine_file.read_text(encoding='utf-8')

        # Check for duplicates
        hashes = load_hashes()
        if is_duplicate(pine_code, hashes):
            return (pine_file, "Duplicate script (already converted)")

        # Get script name
        script_name = pine_file.stem
        category = pine_file.parent.name

        # Convert to Python
        raw_python_code = convert_pine_to_python(pine_code, script_name)

        # Save Python file
        category_dir = PYTHON_DIR / category
        category_dir.mkdir(parents=True, exist_ok=True)

        safe_name = script_name.lower().replace(' ', '-').replace('/', '-')[:80]
        python_file = category_dir / f"{safe_name}.py"
        python_file.write_text(raw_python_code, encoding='utf-8')

        # Update state and hashes
        state = load_conversion_state()
        state["converted"].append(script_name)
        save_conversion_state(state)

        content_hash = compute_content_hash(pine_code)
        hashes[script_name] = content_hash
        save_hashes(hashes)

        return (python_file, "")

    except Exception as e:
        state = load_conversion_state()
        state["failed"].append(script_name)
        save_conversion_state(state)

        return (pine_file, str(e))


def main():
    parser = argparse.ArgumentParser(description="Convert Pine Scripts to Python (no backtesting)")
    parser.add_argument("--category", type=str, help="Specific category to convert")
    parser.add_argument("--limit", type=int, default=0, help="Max scripts to convert")
    args = parser.parse_args()

    print("=" * 60)
    print("Pine Script to Python Converter (No Backtesting)")
    print("=" * 60)
    print(f"\nLLM Provider: {LLM_PROVIDER}")
    print(f"Model: {_get_model_name()}")

    # Find Pine Scripts to convert
    if args.category:
        pine_files = list((PINE_DIR / args.category).glob("*.pine")))
    else:
        pine_files = list(PINE_DIR.rglob("*.pine"))

    # Load state and filter already converted scripts
    state = load_conversion_state()
    converted_set = set(state.get("converted", []))
    pine_files = [f for f in pine_files if f.stem not in converted_set]

    if args.limit > 0:
        pine_files = pine_files[:args.limit]

    print(f"\nFound {len(pine_files)} Pine Scripts to convert")

    if not pine_files:
        print("No scripts to convert!")
        return

    # Convert scripts
    success_count = 0
    failed_count = 0

    for i, pine_file in enumerate(pine_files, 1):
        script_name = pine_file.stem
        category = pine_file.parent.name

        print(f"\n[{i}/{len(pine_files)}] {script_name} ({category})")

        # Check if Python file already exists
        category_dir = PYTHON_DIR / category
        safe_name = script_name.lower().replace(' ', '-').replace('/', '-')[:80]
        python_file = category_dir / f"{safe_name}.py"

        if python_file.exists():
            print("  Skipped (Python file already exists)")
            continue

        # Convert
        python_file, error = convert_single_script(pine_file)

        if error:
            print(f"  ✗ Failed: {error}")
            failed_count += 1
        else:
            print(f"  ✓ Converted: {python_file.name}")
            success_count += 1

        # Small delay to avoid rate limiting
        if i % 10 == 0:
            time.sleep(2)

    # Summary
    print("\n" + "=" * 60)
    print("CONVERSION SUMMARY")
    print("=" * 60)
    print(f"\nSuccess: {success_count}")
    print(f"Failed: {failed_count}")
    print(f"Total: {len(pine_files)}")
    print(f"\nState file: {STATE_FILE}")


if __name__ == "__main__":
    main()
