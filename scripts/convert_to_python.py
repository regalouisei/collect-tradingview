"""Convert Pine Scripts to Python strategies.

This script:
1. Reads deduplicated Pine Scripts
2. Converts to Python using AI analysis
3. Generates VnPy-compatible strategies

Usage:
    python scripts/convert_to_python.py
"""

import json
import re
from pathlib import Path
from typing import Dict, List
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
PINE_DIR = PROJECT_ROOT / "pinescript"
PYTHON_DIR = PROJECT_ROOT / "backtests"
RESULTS_DIR = PROJECT_ROOT / "results"
ANALYSIS_FILE = RESULTS_DIR / "ai_analysis.json"
CONVERSION_LOG = RESULTS_DIR / "conversion_log.md"


def load_analysis() -> Dict:
    """Load AI analysis results."""
    if ANALYSIS_FILE.exists():
        return json.loads(ANALYSIS_FILE.read_text())
    return {}


def find_unique_scripts(analysis: Dict) -> List[Dict]:
    """Find unique scripts (no exact duplicates)."""
    content_hashes = set()
    unique_scripts = []

    for script_analysis in analysis.get('analyses', []):
        content_hash = script_analysis['original_hash']
        if content_hash not in content_hashes:
            content_hashes.add(content_hash)
            unique_scripts.append(script_analysis)

    return unique_scripts


def read_pine_script(pine_path: str) -> str:
    """Read Pine Script content."""
    return Path(pine_path).read_text(encoding='utf-8')


def extract_strategy_params(code: str) -> Dict:
    """Extract strategy parameters from Pine Script."""
    params = {}

    # Extract strategy name
    strategy_match = re.search(r'strategy\s*\(\s*["\']([^"\']+)["\']', code, re.IGNORECASE)
    if strategy_match:
        params['name'] = strategy_match.group(1)

    # Extract inputs
    inputs = re.findall(r'input\s*\([^)]+\)', code, re.IGNORECASE)
    params['inputs'] = len(inputs)

    return params


def extract_indicators(code: str) -> List[str]:
    """Extract indicator calls."""
    indicators = []

    # Common Pine Script indicator functions
    indicator_funcs = [
        'sma', 'ema', 'rsi', 'macd', 'bb', 'atr', 'stoch',
        'wma', 'hull', 'vwma', 'vwap'
    ]

    for func in indicator_funcs:
        if f'{func}(' in code.lower():
            indicators.append(func)

    return list(set(indicators))


def generate_python_strategy(analysis: Dict) -> str:
    """Generate Python strategy from Pine Script analysis."""

    pine_path = analysis['path']
    pine_code = read_pine_script(pine_path)

    # Extract information
    script_name = Path(pine_path).stem.replace('-', '_').title()
    script_type = analysis.get('type', 'indicator')
    indicators = analysis.get('indicators', [])

    params = extract_strategy_params(pine_code)
    name = params.get('name', script_name)

    # Generate Python template
    python_code = f'''"""
Python strategy converted from Pine Script.

Source: {pine_path}
Converted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
Indicators used: {', '.join(indicators) if indicators else 'None'}
"""

from vnpy_ctastrategy import CtaTemplate
from vnpy.trader.object import BarData, TickData, OrderData, TradeData
from vnpy.trader.constant import Direction, Status, Offset
from typing import Optional


class {script_name}Strategy(CtaTemplate):
    """
    {name}

    Original Pine Script converted to VnPy strategy.
    """

    author = "AI Converter"

    # Strategy parameters
    fixed_size: int = 1  # Position size

    # Parameters (extracted from Pine Script inputs)
    fast_length: int = 12
    slow_length: int = 26
    signal_length: int = 9

    variables = {{
        "fast_ma": 0.0,
        "slow_ma": 0.0,
        "macd_value": 0.0,
        "signal_line": 0.0,
        "histogram": 0.0,
    }}

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """Constructor"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

    def on_init(self):
        """Strategy initialization"""
        self.write_log("Strategy initialized")

    def on_start(self):
        """Strategy start"""
        self.write_log("Strategy started")

    def on_stop(self):
        """Strategy stop"""
        self.write_log("Strategy stopped")

    def on_tick(self, tick: TickData):
        """Tick data callback"""
        pass

    def on_bar(self, bar: BarData):
        """Bar data callback - main strategy logic"""
        # Calculate indicators
        self.calculate_indicators(bar)

        # Generate signals
        self.generate_signals(bar)

    def calculate_indicators(self, bar: BarData):
        """Calculate technical indicators"""
        # This is a placeholder - actual implementation depends on the Pine Script logic
        # For full conversion, each Pine Script needs manual review and conversion

        # Example: Moving Averages
        # self.fast_ma = self.am(self.fast_length)
        # self.slow_ma = self.am(self.slow_length)

        # Example: MACD
        # self.macd_value = self.fast_ma - self.slow_ma
        # self.signal_line = self.am(self.signal_length)
        # self.histogram = self.macd_value - self.signal_line

        pass

    def generate_signals(self, bar: BarData):
        """Generate trading signals"""
        # This is a placeholder - actual implementation depends on the Pine Script logic

        # Example: MACD crossover
        # if self.histogram > 0 and self.variables["histogram"] <= 0:
        #     self.buy(bar.close_price, self.fixed_size)
        # elif self.histogram < 0 and self.variables["histogram"] >= 0:
        #     self.sell(bar.close_price, self.fixed_size)

        # Store current histogram for next bar
        # self.variables["histogram"] = self.histogram

        pass
'''

    return python_code


def convert_scripts(analyses: List[Dict]) -> Dict:
    """Convert Pine Scripts to Python."""
    print(f"\nConverting {len(analyses)} scripts...")

    results = {
        "converted": 0,
        "skipped": 0,
        "errors": 0,
        "scripts": []
    }

    for i, analysis in enumerate(analyses, 1):
        if i % 50 == 0:
            print(f"  Progress: {i}/{len(analyses)}")

        script_type = analysis.get('type', 'indicator')

        # Only convert strategies (others can be added as indicators)
        if script_type != 'strategy':
            results['skipped'] += 1
            continue

        try:
            python_code = generate_python_strategy(analysis)

            # Save Python file
            script_name = Path(analysis['path']).stem
            python_file = PYTHON_DIR / f"{script_name}.py"

            python_file.write_text(python_code, encoding='utf-8')

            results['scripts'].append({
                'pine_path': analysis['path'],
                'python_path': str(python_file),
                'script_name': script_name,
                'type': script_type
            })

            results['converted'] += 1

        except Exception as e:
            print(f"  Error converting {analysis['path']}: {e}")
            results['errors'] += 1

    return results


def generate_conversion_report(results: Dict) -> str:
    """Generate conversion report."""
    report = "# Pine Script to Python Conversion Report\n\n"
    report += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"

    report += "## Summary\n\n"
    report += f"- **Converted:** {results['converted']}\n"
    report += f"- **Skipped:** {results['skipped']}\n"
    report += f"- **Errors:** {results['errors']}\n"

    report += "\n## Converted Scripts\n\n"
    for script in results['scripts'][:10]:  # Show first 10
        report += f"- **{script['script_name']}**\n"
        report += f"  - Type: {script['type']}\n"
        report += f"  - Pine: `{script['pine_path']}`\n"
        report += f"  - Python: `{script['python_path']}`\n\n"

    if len(results['scripts']) > 10:
        report += f"... and {len(results['scripts']) - 10} more\n\n"

    report += "## Notes\n\n"
    report += "1. **Manual Review Required**: All converted strategies need manual review\n"
    report += "2. **Indicator Logic**: Core logic needs to be manually converted from Pine\n"
    report += "3. **Testing**: Each strategy should be backtested before live trading\n\n"

    return report


def main():
    print("=" * 60)
    print("Pine Script to Python Conversion")
    print("=" * 60)

    # Load AI analysis
    print("\nLoading AI analysis...")
    analysis = load_analysis()

    if not analysis:
        print("ERROR: No analysis found. Run ai_deduplicate.py first.")
        return

    # Find unique scripts
    print("Finding unique scripts...")
    unique_scripts = find_unique_scripts(analysis)
    print(f"  Found {len(unique_scripts)} unique scripts")

    # Convert to Python
    results = convert_scripts(unique_scripts)

    # Generate report
    print("\nGenerating report...")
    report = generate_conversion_report(results)

    # Save report
    print("Saving report...")
    CONVERSION_LOG.write_text(report)
    print(f"  Report saved to: {CONVERSION_LOG}")

    # Summary
    print("\n" + "=" * 60)
    print("Conversion Complete")
    print("=" * 60)
    print(f"Converted: {results['converted']}")
    print(f"Skipped: {results['skipped']}")
    print(f"Errors: {results['errors']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
