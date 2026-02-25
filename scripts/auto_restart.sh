#!/bin/bash
# Auto-restart script for scraper

WORKSPACE="/root/.openclaw/workspace/openclaw-tradingview"
SCRAPER_SCRIPT="$WORKSPACE/scripts/batch_scraper_v6.py"
LOG_DIR="$WORKSPACE/logs"

echo "=== 检查爬虫状态 ===" | tee -a "$LOG_DIR/auto_restart.log"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S UTC')" | tee -a "$LOG_DIR/auto_restart.log"

# Check if scraper is running
PID=$(ps aux | grep "batch_scraper_v6" | grep -v grep | awk '{print $2}')

if [ -z "$PID" ]; then
    echo "⚠️  爬虫未运行，正在启动..." | tee -a "$LOG_DIR/auto_restart.log"

    # Start scraper
    cd "$WORKSPACE"
    nohup ./venv/bin/python -u "$SCRAPER_SCRIPT" --all \
        > "$LOG_DIR/scrape_v6_auto_$(date +%Y%m%d_%H%M%S).log" 2>&1 &

    NEW_PID=$!
    echo "✅ 爬虫已启动 (PID: $NEW_PID)" | tee -a "$LOG_DIR/auto_restart.log"
else
    echo "✅ 爬虫运行中 (PID: $PID)" | tee -a "$LOG_DIR/auto_restart.log"

    # Check if it's stuck (no progress in last 30 minutes)
    PROGRESS_FILE="$WORKSPACE/results/.scrape_progress_v6.json"
    if [ -f "$PROGRESS_FILE" ]; then
        LAST_UPDATE=$(stat -c %Y "$PROGRESS_FILE" 2>/dev/null || stat -f %m "$PROGRESS_FILE" 2>/dev/null)
        CURRENT=$(date +%s)
        ELAPSED=$((CURRENT - LAST_UPDATE))

        # If no progress for 30 minutes (1800 seconds), restart
        if [ $ELAPSED -gt 1800 ]; then
            echo "⚠️  爬虫无响应超过 30 分钟，正在重启..." | tee -a "$LOG_DIR/auto_restart.log"

            # Kill old scraper
            kill $PID 2>/dev/null
            sleep 3

            # Start new scraper
            cd "$WORKSPACE"
            nohup ./venv/bin/python -u "$SCRAPER_SCRIPT" --all \
                > "$LOG_DIR/scrape_v6_auto_$(date +%Y%m%d_%H%M%S).log" 2>&1 &

            NEW_PID=$!
            echo "✅ 爬虫已重启 (PID: $NEW_PID)" | tee -a "$LOG_DIR/auto_restart.log"
        else
            MINUTES=$((ELAPSED / 60))
            echo "   最后更新: ${MINUTES} 分钟前" | tee -a "$LOG_DIR/auto_restart.log"
        fi
    fi
fi

echo "" | tee -a "$LOG_DIR/auto_restart.log"
