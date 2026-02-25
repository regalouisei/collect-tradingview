#!/bin/bash
# Full automation pipeline: scrape -> deduplicate -> convert

WORKSPACE="/root/.openclaw/workspace/openclaw-tradingview"
VENV="$WORKSPACE/venv/bin/python"
LOG_DIR="$WORKSPACE/logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Main log
MAIN_LOG="$LOG_DIR/pipeline_$TIMESTAMP.log"

# Function to log
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S UTC')] $1" | tee -a "$MAIN_LOG"
}

# Function to send progress update
send_update() {
    local message="$1"
    echo "$message" | tee -a "$MAIN_LOG"
    # TODO: Integrate with Telegram or other notification system
}

# Step 1: Full site scraping
log "============================================================"
log "Step 1: Starting Full Site Scraping"
log "============================================================"

cd "$WORKSPACE"
nohup $VENV -u scripts/batch_scraper_full.py --all --aggressive \
    > "$LOG_DIR/scrape_full_$TIMESTAMP.log" 2>&1 &
SCRAPER_PID=$!

log "Scraper started with PID: $SCRAPER_PID"

# Wait for scraper to complete
log "Waiting for scraper to complete..."
while ps -p $SCRAPER_PID > /dev/null 2>&1; do
    sleep 60  # Check every minute
done

log "Scraper completed"

# Count scripts
PINE_COUNT=$(find "$WORKSPACE/pinescript" -name "*.pine" 2>/dev/null | wc -l)
log "Total Pine Scripts after scraping: $PINE_COUNT"

# Step 2: AI deduplication
log "============================================================"
log "Step 2: Starting AI Deduplication"
log "============================================================"

send_update "Starting AI-powered deduplication of $PINE_COUNT scripts..."

$VENV scripts/ai_deduplicate.py >> "$MAIN_LOG" 2>&1

log "Deduplication completed"

# Step 3: Python conversion
log "============================================================"
log "Step 3: Starting Python Conversion"
log "============================================================"

send_update "Starting Python conversion of deduplicated scripts..."

$VENV scripts/convert_to_python.py >> "$MAIN_LOG" 2>&1

log "Python conversion completed"

# Count Python scripts
PYTHON_COUNT=$(find "$WORKSPACE/backtests" -name "*.py" 2>/dev/null | wc -l)
log "Total Python Scripts after conversion: $PYTHON_COUNT"

# Final summary
log "============================================================"
log "Pipeline Complete"
log "============================================================"
log "Pine Scripts: $PINE_COUNT"
log "Python Scripts: $PYTHON_COUNT"
log "============================================================"

send_update "Pipeline complete! $PINE_COUNT Pine Scripts, $PYTHON_COUNT Python Scripts"

# Generate final report
cat << EOF > "$LOG_DIR/pipeline_summary_$TIMESTAMP.md"
# TradingView Automation Pipeline - Summary

**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S UTC')

## Pipeline Steps

### 1. Full Site Scraping
- **Status:** ✅ Complete
- **Scripts:** $PINE_COUNT
- **Log:** \`scrape_full_$TIMESTAMP.log\`

### 2. AI Deduplication
- **Status:** ✅ Complete
- **Analysis:** \`ai_analysis.json\`
- **Report:** \`deduplication_log.md\`

### 3. Python Conversion
- **Status:** ✅ Complete
- **Strategies:** $PYTHON_COUNT
- **Report:** \`conversion_log.md\`

## Statistics

- **Total Pine Scripts:** $PINE_COUNT
- **Python Strategies:** $PYTHON_COUNT
- **Conversion Rate:** $(awk "BEGIN {printf \"%.1f\", ($PYTHON_COUNT/$PINE_COUNT)*100}")%

## Next Steps

1. Review converted strategies
2. Backtest each strategy
3. Optimize parameters
4. Deploy to live trading

---

**Report generated:** $(date '+%Y-%m-%d %H:%M:%S UTC')
EOF

log "Summary report generated: pipeline_summary_$TIMESTAMP.md"
log "Pipeline complete!"
