#!/usr/bin/env python3
"""Test script for LLM provider configuration and Pine Script conversion."""

import os
import sys

# Add framework to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from framework.pine_converter import (
    LLM_PROVIDER,
    OPENAI_API_KEY,
    GEMINI_API_KEY,
    ZHIPU_API_KEY,
    ANTHROPIC_API_KEY,
    MODELS,
    _get_model_name,
    convert_pine_to_python,
)

# Simple Pine Script for testing
TEST_PINE_SCRIPT = """
//@version=5
strategy("Simple RSI Strategy")
length = input(14, title="RSI Length")
overbought = input(70, title="Overbought")
oversold = input(30, title="Oversold")

rsi = ta.rsi(close, length)

if rsi < oversold
    strategy.entry("Buy", strategy.long)

if rsi > overbought
    strategy.close("Buy")
"""


def test_configuration():
    """Test LLM provider configuration."""
    print("=" * 60)
    print("LLM PROVIDER CONFIGURATION TEST")
    print("=" * 60)

    print(f"\n📋 Provider: {LLM_PROVIDER}")
    print(f"🤖 Model: {_get_model_name()}")

    print("\n🔑 API Keys Status:")
    print(f"  OpenAI (GPT):      {'✅' if OPENAI_API_KEY else '❌ Not configured'}")
    print(f"  Gemini:           {'✅' if GEMINI_API_KEY else '❌ Not configured'}")
    print(f"  Zhipu (智谱):     {'✅' if ZHIPU_API_KEY else '❌ Not configured'}")
    print(f"  Anthropic (Claude): {'✅' if ANTHROPIC_API_KEY else '❌ Not configured'}")

    print("\n📚 Available Models:")
    for provider, config in MODELS.items():
        print(f"  {provider}: {', '.join(config['models'])}")

    print("\n" + "=" * 60)


def test_conversion():
    """Test Pine Script to Python conversion."""
    print("\n" + "=" * 60)
    print("PINE SCRIPT CONVERSION TEST")
    print("=" * 60)

    try:
        print("\n🔄 Converting test Pine Script...")
        print(f"   Provider: {LLM_PROVIDER}")
        print(f"   Model: {_get_model_name()}")

        python_code = convert_pine_to_python(TEST_PINE_SCRIPT, "test_rsi")

        print("\n✅ Conversion successful!")
        print(f"\n📄 Generated Python code ({len(python_code)} chars):")
        print("-" * 60)
        print(python_code)
        print("-" * 60)

        # Validate
        if "class TvStrategy" in python_code:
            print("\n✅ Strategy class found")
        else:
            print("\n❌ Strategy class NOT found")

        if "from backtesting import" in python_code:
            print("✅ backtesting import found")
        else:
            print("❌ backtesting import NOT found")

        if "pandas_ta as pta" in python_code:
            print("✅ pandas_ta import found")
        else:
            print("❌ pandas_ta import NOT found")

    except Exception as e:
        print(f"\n❌ Conversion failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_configuration()

    # Only test conversion if an API key is configured
    has_api_key = any([
        OPENAI_API_KEY,
        GEMINI_API_KEY,
        ZHIPU_API_KEY,
        ANTHROPIC_API_KEY,
    ])

    if has_api_key:
        test_conversion()
    else:
        print("\n⚠️  No API key configured. Skipping conversion test.")
        print("\n📝 To configure:")
        print("   1. Edit .env file")
        print("   2. Set LLM_PROVIDER (openai, gemini, zhipu, anthropic)")
        print("   3. Set corresponding API key:")
        print("      - For zhipu:  ZHIPU_API_KEY=xxx (推荐 免费)")
        print("      - For openai:  OPENAI_API_KEY=xxx")
        print("      - For gemini:  GEMINI_API_KEY=xxx")
        print("      - For anthropic: ANTHROPIC_API_KEY=xxx")
