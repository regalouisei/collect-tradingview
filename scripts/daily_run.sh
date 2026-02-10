#!/bin/bash
# DeepStack TradingView — Daily Pipeline Runner
# Called by launchd (com.deepstack.tv-scrape) at 2:00 AM daily.
#
# Steps:
#   1. Scrape new Pine Scripts from TradingView (incremental)
#   2. Convert + backtest all unprocessed scripts
#   3. Update Supabase rankings

set -euo pipefail

PROJ_DIR="$HOME/Development/deepstack-tradingview"
LOG_DIR="$HOME/Library/Logs/claude-automation/deepstack-tv"
VENV="$PROJ_DIR/venv/bin/python3"

mkdir -p "$LOG_DIR"

echo "=========================================="
echo "DeepStack TV Daily Pipeline"
echo "$(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# Load environment variables
if [ -f "$PROJ_DIR/.env" ]; then
    set -a
    source "$PROJ_DIR/.env"
    set +a
fi

cd "$PROJ_DIR"

# Use venv python if available, otherwise system python3
PYTHON="$VENV"
if [ ! -f "$PYTHON" ]; then
    PYTHON="python3"
fi

echo ""
echo "[Step 1/3] Scraping TradingView..."
$PYTHON scripts/batch_scraper.py --all --incremental 2>&1 || echo "Scraper exited with code $?"

echo ""
echo "[Step 2/3] Running backtest pipeline..."
$PYTHON scripts/run_pipeline.py 2>&1 || echo "Pipeline exited with code $?"

echo ""
echo "[Step 3/3] Updating rankings..."
$PYTHON scripts/update_rankings.py 2>&1 || echo "Rankings exited with code $?"

echo ""
echo "=========================================="
echo "Pipeline finished at $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
