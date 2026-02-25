#!/bin/bash
# 10-minute progress reporter with crash detection

WORKSPACE="/root/.openclaw/workspace/openclaw-tradingview"
CHECK_SCRIPT="$WORKSPACE/scripts/check_progress.sh"
REPORT_LOG="$WORKSPACE/logs/10min_reports_$(date +%Y%m%d).md"
SCRAPER_V6_PID_FILE="$WORKSPACE/results/.scraper_v6.pid"

# Check if scraper is running
check_scraper_status() {
    local pid=$(ps aux | grep "batch_scraper_v6" | grep -v grep | awk '{print $2}')
    if [ -z "$pid" ]; then
        echo "❌ 爬虫未运行"
        return 1
    else
        echo "✅ 爬虫运行中 (PID: $pid, CPU: $(ps aux | grep $pid | grep -v grep | awk '{print $3}')%, MEM: $(ps aux | grep $pid | grep -v grep | awk '{print $4}')%)"
        # Save PID
        echo "$pid" > "$SCRAPER_V6_PID_FILE"
        return 0
    fi
}

# Check progress
check_progress() {
    if [ -f "$WORKSPACE/results/.scrape_progress_v6.json" ]; then
        CATEGORY=$(cat "$WORKSPACE/results/.scrape_progress_v6.json" | jq -r '.category // "N/A"')
        PAGE=$(cat "$WORKSPACE/results/.scrape_progress_v6.json" | jq -r '.page // 0')
        TOTAL_PAGES=$(cat "$WORKSPACE/results/.scrape_progress_v6.json" | jq -r '.total_pages // 0')
        STATUS=$(cat "$WORKSPACE/results/.scrape_progress_v6.json" | jq -r '.status // "unknown"')

        echo "📊 分类: $CATEGORY, 页面: $PAGE/$TOTAL_PAGES"

        if [ "$TOTAL_PAGES" -gt 0 ]; then
            PERCENT=$(awk "BEGIN {printf \"%.1f\", ($PAGE/$TOTAL_PAGES)*100}")
            echo "   进度: $PERCENT%"
        fi

        echo "   状态: $STATUS"
    else
        echo "📊 无进度文件"
    fi
}

# Count scripts
count_scripts() {
    local pine_count=$(find "$WORKSPACE/pinescript" -name "*.pine" 2>/dev/null | wc -l)
    echo "📁 Pine Scripts: $pine_count"
}

# Main reporting
echo "📊 10分钟进度报告 - $(date '+%Y-%m-%d %H:%M:%S UTC')" >> "$REPORT_LOG"
echo "" >> "$REPORT_LOG"

# Check scraper status
SCRAPER_RUNNING=0
if check_scraper_status >> "$REPORT_LOG" 2>&1; then
    SCRAPER_RUNNING=1
    echo "" >> "$REPORT_LOG"
else
    echo "" >> "$REPORT_LOG"
    echo "⚠️  爬虫可能已崩溃！" >> "$REPORT_LOG"
    echo "" >> "$REPORT_LOG"
fi

# Check progress
check_progress >> "$REPORT_LOG" 2>&1
echo "" >> "$REPORT_LOG"

# Count scripts
count_scripts >> "$REPORT_LOG" 2>&1
echo "" >> "$REPORT_LOG"

echo "---" >> "$REPORT_LOG"
echo "" >> "$REPORT_LOG"

echo "✅ 报告已保存到: $REPORT_LOG"

# Return status
if [ $SCRAPER_RUNNING -eq 0 ]; then
    exit 1  # Scraper not running
else
    exit 0  # Scraper running
fi
