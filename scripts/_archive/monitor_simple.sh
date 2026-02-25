#!/bin/bash
# 简单的监控脚本 - 不依赖输出重定向

echo "=== 监控检查 ===" && echo ""

# 1. 脚本数量
echo "1. Pine Scripts 数量:"
find /root/.openclaw/workspace/openclaw-tradingview/pinescript -name "*.pine" 2>/dev/null | wc -l
echo ""

# 2. Python 策略数量
echo "2. Python 策略数量:"
find /root/.openclaw/workspace/openclaw-tradingview/backtests -name "*.py" 2>/dev/null | wc -l
echo ""

# 3. 进程检查
echo "3. 进程状态:"
ps aux | grep -E "batch_scraper|python.*scr" | grep -v grep | head -5
echo ""

# 4. 日志文件大小
echo "4. 日志文件状态:"
ls -lh /root/.openclaw/workspace/openclaw-tradingview/logs/*.log 2>/dev/null | tail -5
echo ""

# 5. 状态文件
echo "5. 状态文件状态:"
ls -lh /root/.openclaw/workspace/openclaw-tradingview/results/.scrape*.json 2>/dev/null | tail -5
echo ""

echo "=== 检查完成 ==="
