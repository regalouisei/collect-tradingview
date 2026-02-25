#!/bin/bash
# 10-minute progress reporter

WORKSPACE="/root/.openclaw/workspace/openclaw-tradingview"
CHECK_SCRIPT="$WORKSPACE/scripts/check_progress.sh"
REPORT_LOG="$WORKSPACE/logs/10min_reports_$(date +%Y%m%d).md"

echo "📊 10分钟进度报告 - $(date '+%Y-%m-%d %H:%M:%S UTC')" >> "$REPORT_LOG"
echo "" >> "$REPORT_LOG"

# Run check and append to report
bash "$CHECK_SCRIPT" >> "$REPORT_LOG" 2>&1

echo "" >> "$REPORT_LOG"
echo "---" >> "$REPORT_LOG"
echo "" >> "$REPORT_LOG"

echo "✅ 报告已保存到: $REPORT_LOG"
