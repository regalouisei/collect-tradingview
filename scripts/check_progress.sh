#!/bin/bash
# Immediate progress check

WORKSPACE="/root/.openclaw/workspace/openclaw-tradingview"
# Check both v5 and v6 progress files
PROGRESS_FILE_V5="$WORKSPACE/results/.scrape_progress_v5.json"
PROGRESS_FILE_V6="$WORKSPACE/results/.scrape_progress_v6.json"

echo "============================================================"
echo "当前进度 - $(date '+%Y-%m-%d %H:%M:%S UTC')"
echo "============================================================"

# Check scraper process
SCRAPER_PID=$(ps aux | grep "batch_scraper_full" | grep -v grep | awk '{print $2}')
SCRAPER_MEM=$(ps aux | grep "batch_scraper_full" | grep -v grep | awk '{print $4}')

if [ -n "$SCRAPER_PID" ]; then
    echo "✅ 爬虫运行中"
    echo "   PID: $SCRAPER_PID"
    echo "   内存: ${SCRAPER_MEM}%"
else
    echo "❌ 爬虫未运行"
fi

# Check progress
if [ -f "$PROGRESS_FILE_V6" ]; then
    PROGRESS_FILE="$PROGRESS_FILE_V6"
elif [ -f "$PROGRESS_FILE_V5" ]; then
    PROGRESS_FILE="$PROGRESS_FILE_V5"
else
    echo ""
    echo "📊 爬取进度"
    echo "   (无进度文件)"
    PROGRESS_FILE=""
fi

if [ -n "$PROGRESS_FILE" ] && [ -f "$PROGRESS_FILE" ]; then
    CATEGORY=$(cat "$PROGRESS_FILE" | jq -r '.category // "N/A"')
    PAGE=$(cat "$PROGRESS_FILE" | jq -r '.page // 0')
    TOTAL_PAGES=$(cat "$PROGRESS_FILE" | jq -r '.total_pages // 0')
    STATUS=$(cat "$PROGRESS_FILE" | jq -r '.status // "unknown"')

    echo ""
    echo "📊 爬取进度"
    echo "   分类: $CATEGORY"

    if [ "$TOTAL_PAGES" -gt 0 ]; then
        PERCENT=$(awk "BEGIN {printf \"%.1f\", ($PAGE/$TOTAL_PAGES)*100}")
        echo "   页面进度: $PAGE / $TOTAL_PAGES ($PERCENT%)"
    fi

    echo "   状态: $STATUS"
fi

# Count scripts
PINE_COUNT=$(find "$WORKSPACE/pinescript" -name "*.pine" 2>/dev/null | wc -l)
PYTHON_COUNT=$(find "$WORKSPACE/backtests" -name "*.py" 2>/dev/null | wc -l)

echo ""
echo "📁 数据统计"
echo "   Pine Scripts: $PINE_COUNT"
echo "   Python Scripts: $PYTHON_COUNT"

# Check latest log
echo ""
echo "📝 最新日志 (最后 5 行)"
LATEST_LOG=$(ls -t "$WORKSPACE/logs/scrape_full_unlimited"*.log 2>/dev/null | head -1)
if [ -n "$LATEST_LOG" ]; then
    tail -5 "$LATEST_LOG"
else
    echo "   (未找到日志文件)"
fi

echo "============================================================"
