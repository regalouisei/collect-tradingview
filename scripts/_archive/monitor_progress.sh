#!/bin/bash
# Progress monitoring script - reports every 10 minutes

WORKSPACE="/root/.openclaw/workspace/openclaw-tradingview"
PROGRESS_FILE="$WORKSPACE/results/.scrape_progress.json"
LOG_DIR="$WORKSPACE/logs"
MONITOR_LOG="$LOG_DIR/monitor_$(date +%Y%m%d).log"

# Function to send progress report
report_progress() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S UTC')
    echo "============================================================" >> "$MONITOR_LOG"
    echo "[$timestamp] Progress Report" >> "$MONITOR_LOG"
    echo "============================================================" >> "$MONITOR_LOG"

    # Check scraper process
    local scraper_pid=$(ps aux | grep "batch_scraper_full" | grep -v grep | awk '{print $2}')
    
    if [ -n "$scraper_pid" ]; then
        echo "✅ Scraper running (PID: $scraper_pid)" >> "$MONITOR_LOG"
    else
        echo "⚠️  Scraper not running" >> "$MONITOR_LOG"
    fi

    # Check progress
    if [ -f "$PROGRESS_FILE" ]; then
        local progress=$(cat "$PROGRESS_FILE")
        local category=$(echo "$progress" | jq -r '.category // "N/A"')
        local current=$(echo "$progress" | jq -r '.current // 0')
        local total=$(echo "$progress" | jq -r '.total // 0')
        local status=$(echo "$progress" | jq -r '.status // "unknown"')

        echo "Category: $category" >> "$MONITOR_LOG"
        echo "Progress: $current / $total" >> "$MONITOR_LOG"
        echo "Status: $status" >> "$MONITOR_LOG"

        if [ "$total" -gt 0 ]; then
            local percent=$(awk "BEGIN {printf \"%.1f\", ($current/$total)*100}")
            echo "Percentage: $percent%" >> "$MONITOR_LOG"
        fi
    else
        echo "No progress file found" >> "$MONITOR_LOG"
    fi

    # Count scripts
    local pine_count=$(find "$WORKSPACE/pinescript" -name "*.pine" 2>/dev/null | wc -l)
    local python_count=$(find "$WORKSPACE/backtests" -name "*.py" 2>/dev/null | wc -l)

    echo "" >> "$MONITOR_LOG"
    echo "Total Pine Scripts: $pine_count" >> "$MONITOR_LOG"
    echo "Total Python Scripts: $python_count" >> "$MONITOR_LOG"
    echo "" >> "$MONITOR_LOG"
}

# Main loop
echo "Starting progress monitoring..." | tee -a "$MONITOR_LOG"
echo "Will report every 10 minutes" | tee -a "$MONITOR_LOG"

while true; do
    report_progress
    sleep 600  # 10 minutes
done
