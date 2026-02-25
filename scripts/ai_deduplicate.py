"""AI-powered deduplication and analysis of Pine Scripts.

This script:
1. Analyzes Pine Script code structure
2. Identifies duplicate logic
3. Categorizes scripts by type (indicator, strategy, library)
4. Extracts core logic for conversion

Usage:
    python scripts/ai_deduplicate.py
"""

import hashlib
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
PINE_DIR = PROJECT_ROOT / "pinescript"
RESULTS_DIR = PROJECT_ROOT / "results"
ANALYSIS_FILE = RESULTS_DIR / "ai_analysis.json"
DEDUP_LOG = RESULTS_DIR / "deduplication_log.md"

# Keywords for different script types
TYPE_KEYWORDS = {
    "strategy": ["strategy(", "strategy.entry", "strategy.exit"],
    "indicator": ["indicator(", "plot(", "plotshape(", "plotchar("],
    "library": ["library("]
}

# Keywords for common indicators
INDICATOR_KEYWORDS = {
    "RSI": ["rsi(", "relative strength"],
    "MACD": ["macd(", "signal line"],
    "MA": ["sma(", "ema(", "wma(", "vwma(", "hull("],
    "BB": ["bb(", "bollinger bands"],
    "Volume": ["volume", "vwap", "obv"],
    "ATR": ["atr(", "average true range"],
    "Stochastic": ["stoch(", "stochastic"]
}


def extract_script_type(code: str) -> str:
    """Extract script type (strategy, indicator, library)."""
    for script_type, keywords in TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in code:
                return script_type
    return "unknown"


def extract_indicators(code: str) -> List[str]:
    """Extract indicator types used in the script."""
    found = []
    code_lower = code.lower()
    for indicator, keywords in INDICATOR_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in code_lower:
                found.append(indicator)
                break
    return found


def extract_core_logic(code: str) -> str:
    """Extract core logic from Pine Script."""
    # Remove comments
    code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)

    # Remove inputs
    code = re.sub(r'inputs?\([^)]*\)', '', code, flags=re.DOTALL)

    # Remove version line
    code = re.sub(r'//@version\s+\d+', '', code)

    # Remove extra whitespace
    code = re.sub(r'\s+', ' ', code).strip()

    return code


def compute_logic_hash(code: str) -> str:
    """Compute hash of core logic for deduplication."""
    core_logic = extract_core_logic(code)
    return hashlib.sha256(core_logic.encode('utf-8')).hexdigest()


def analyze_script(pine_path: Path) -> Dict:
    """Analyze a single Pine Script."""
    try:
        code = pine_path.read_text(encoding='utf-8')

        return {
            "path": str(pine_path),
            "filename": pine_path.name,
            "type": extract_script_type(code),
            "indicators": extract_indicators(code),
            "lines": code.count('\n') + 1,
            "logic_hash": compute_logic_hash(code),
            "original_hash": hashlib.sha256(code.encode('utf-8')).hexdigest()
        }
    except Exception as e:
        print(f"Error analyzing {pine_path}: {e}")
        return None


def deduplicate_scripts(analyses: List[Dict]) -> Tuple[List[Dict], Dict]:
    """Deduplicate scripts based on logic and content."""
    logic_groups = defaultdict(list)
    content_groups = defaultdict(list)

    # Group by logic hash
    for analysis in analyses:
        logic_groups[analysis['logic_hash']].append(analysis)
        content_groups[analysis['original_hash']].append(analysis)

    # Find duplicates
    logic_duplicates = []
    content_duplicates = []

    # Find logic duplicates
    for logic_hash, scripts in logic_groups.items():
        if len(scripts) > 1:
            logic_duplicates.append({
                'logic_hash': logic_hash,
                'scripts': [s['path'] for s in scripts],
                'count': len(scripts)
            })

    # Find exact content duplicates
    for content_hash, scripts in content_groups.items():
        if len(scripts) > 1:
            content_duplicates.append({
                'content_hash': content_hash,
                'scripts': [s['path'] for s in scripts],
                'count': len(scripts)
            })

    return logic_duplicates, content_duplicates


def generate_report(analyses: List[Dict], logic_duplicates: List[Dict],
                   content_duplicates: List[Dict]) -> str:
    """Generate analysis report."""
    report = "# AI-Powered Pine Script Analysis\n\n"
    report += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"

    # Overview
    report += "## Overview\n\n"
    report += f"- **Total Scripts:** {len(analyses)}\n"

    script_types = defaultdict(int)
    for analysis in analyses:
        script_types[analysis['type']] += 1

    report += "- **By Type:**\n"
    for script_type, count in sorted(script_types.items()):
        report += f"  - {script_type}: {count}\n"

    # Indicators
    all_indicators = defaultdict(int)
    for analysis in analyses:
        for indicator in analysis['indicators']:
            all_indicators[indicator] += 1

    report += "\n- **Top Indicators:**\n"
    for indicator, count in sorted(all_indicators.items(), key=lambda x: x[1], reverse=True)[:10]:
        report += f"  - {indicator}: {count}\n"

    # Duplicates
    report += "\n## Duplicates\n\n"

    report += f"### Logic Duplicates ({len(logic_duplicates)} groups)\n\n"
    for dup in logic_duplicates[:5]:  # Show first 5
        report += f"- **Group:** {dup['count']} scripts with same logic\n"
        for script in dup['scripts'][:2]:
            report += f"  - {script}\n"
        report += "\n"

    if len(logic_duplicates) > 5:
        report += f"... and {len(logic_duplicates) - 5} more groups\n\n"

    report += f"### Exact Content Duplicates ({len(content_duplicates)} groups)\n\n"
    for dup in content_duplicates[:5]:  # Show first 5
        report += f"- **Group:** {dup['count']} identical scripts\n"
        for script in dup['scripts'][:2]:
            report += f"  - {script}\n"
        report += "\n"

    if len(content_duplicates) > 5:
        report += f"... and {len(content_duplicates) - 5} more groups\n\n"

    # Recommendations
    report += "## Recommendations\n\n"
    report += "1. **Remove Exact Duplicates**: " \
              f"{sum(d['count'] - 1 for d in content_duplicates)} files\n"
    report += "2. **Review Logic Duplicates**: " \
              f"{len(logic_duplicates)} groups with similar logic\n"
    report += "3. **Priority for Conversion**: Focus on strategies first\n\n"

    return report


def main():
    print("=" * 60)
    print("AI-Powered Pine Script Analysis & Deduplication")
    print("=" * 60)

    # Find all Pine Scripts
    pine_files = list(PINE_DIR.rglob("*.pine"))
    print(f"\nFound {len(pine_files)} Pine Scripts")

    # Analyze each script
    print("\nAnalyzing scripts...")
    analyses = []
    for i, pine_file in enumerate(pine_files, 1):
        if i % 100 == 0:
            print(f"  Progress: {i}/{len(pine_files)}")
        analysis = analyze_script(pine_file)
        if analysis:
            analyses.append(analysis)

    print(f"  Analyzed {len(analyses)} scripts")

    # Deduplicate
    print("\nDeduplicating...")
    logic_duplicates, content_duplicates = deduplicate_scripts(analyses)
    print(f"  Found {len(logic_duplicates)} logic duplicate groups")
    print(f"  Found {len(content_duplicates)} content duplicate groups")

    # Generate report
    print("\nGenerating report...")
    report = generate_report(analyses, logic_duplicates, content_duplicates)

    # Save results
    print("\nSaving results...")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(ANALYSIS_FILE, 'w') as f:
        json.dump({
            "analyses": analyses,
            "logic_duplicates": logic_duplicates,
            "content_duplicates": content_duplicates,
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)

    with open(DEDUP_LOG, 'w') as f:
        f.write(report)

    print(f"  Analysis saved to: {ANALYSIS_FILE}")
    print(f"  Report saved to: {DEDUP_LOG}")

    # Summary
    print("\n" + "=" * 60)
    print("Analysis Complete")
    print("=" * 60)
    print(f"Total Scripts: {len(analyses)}")
    print(f"Logic Duplicates: {len(logic_duplicates)} groups")
    print(f"Content Duplicates: {len(content_duplicates)} groups")
    print(f"Unique Scripts: {len(analyses) - sum(d['count'] - 1 for d in content_duplicates)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
