#!/bin/bash
# 快速回测运行器 - Python 3.12 兼容

set -e

PROJECT_DIR="/root/.openclaw/workspace/openclaw-tradingview"
cd "$PROJECT_DIR"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}快速回测运行器${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 统计信息
TOTAL_PYTHON=$(find backtests -name "*.py" -type f 2>/dev/null | wc -l)

echo -e "${YELLOW}[统计]${NC}"
echo -e "  Python 策略: ${TOTAL_PYTHON}"
echo ""

# 确认回测
read -p "开始回测 ${TOTAL_PYTHON} 个策略？(y/n): " backtest_choice
if [ "$backtest_choice" != "y" ] && [ "$backtest_choice" != "Y" ]; then
    echo "取消"
    exit 0
fi

echo ""
echo -e "${MAGENTA}开始回测...${NC}"
echo ""

# 启动回测
./venv/bin/python framework/backtest_runner.py

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}回测完成${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
