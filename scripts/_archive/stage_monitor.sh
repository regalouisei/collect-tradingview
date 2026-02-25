#!/bin/bash
# 三阶段任务监控脚本

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
echo -e "${BLUE}三阶段任务监控${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 阶段 1：爬取
echo -e "${CYAN}【阶段 1：爬取】${NC}"
echo ""

TOTAL_PINE=$(find pinescript -name "*.pine" 2>/dev/null | wc -l)
echo -e "  📊 总 Pine Scripts: ${TOTAL_PINE}"

# 检查爬取进程
SCRAPE_PID=$(pgrep -f "batch_scraper_optimized" -o | head -1)
if [ ! -z "$SCRAPE_PID" ]; then
    echo -e "  🔄 爬取中... (PID: ${SCRAPE_PID})"
else
    echo -e "  ${YELLOW}⚠️  爬取未运行${NC}"
fi
echo ""

# 阶段 2：转换
echo -e "${CYAN}【阶段 2：转换】${NC}"
echo ""

TOTAL_PYTHON=$(find backtests -name "*.py" 2>/dev/null | wc -l)
echo -e "  🐍 总 Python 文件: ${TOTAL_PYTHON}"

CONVERSION_RATE=$(echo "scale=1; ($TOTAL_PYTHON * 100) / $TOTAL_PINE" | bc 2>/dev/null || echo "N/A")
echo -e "  📈 转换率: ${CONVERSION_RATE}%"

# 检查智谱 AI 额度
echo ""
echo -e "  🤖 智谱 AI 额度检查..."
API_KEY="63c8b255a3fd48168a8dc5329f27c41c.jPgGCTA1yX1u9eEa"

./venv/bin/python -c "
import json
import sys
sys.path.insert(0, '.')

try:
    from zhipuai import ZhipuAI
    client = ZhipuAI(api_key='$API_KEY')
    
    # 简单测试
    response = client.chat.completions.create(
        model='glm-4.7',
        messages=[{'role': 'user', 'content': '测试'}],
        max_tokens=10,
    )
    
    print('  ${GREEN}✅ 智谱 AI 额度充足${NC}')
    print('  可以开始转换')
except Exception as e:
    error_msg = str(e)
    if '余额不足' in error_msg or '1113' in error_msg:
        print('  ${RED}❌ 智谱 AI 额度不足${NC}')
        print('  需要等待恢复或充值')
    else:
        print('  ${RED}❌ 智谱 AI 其他错误${NC}')
        print(f'  {error_msg}')
" 2>&1
echo ""

# 阶段 3：回测
echo -e "${CYAN}【阶段 3：回测】${NC}"
echo ""

# 检查回测结果
if [ -f "results/backtest_results.csv" ]; then
    TOTAL_RECORDS=$(wc -l < results/backtest_results.csv)
    echo -e "  📈 总回测记录: ${TOTAL_RECORDS}"
else
    echo -e "  ${YELLOW}⚠️  回测结果文件不存在${NC}"
fi
echo ""

# 总体进度
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}总体进度${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${MAGENTA}【当前状态】${NC}"
echo -e "  📊 Pine Scripts: ${TOTAL_PINE}"
echo -e "  🐍 Python 文件: ${TOTAL_PYTHON}"
echo -e "  📈 转换率: ${CONVERSION_RATE}%"
echo ""

# 待处理
PENDING=$((TOTAL_PINE - TOTAL_PYTHON))
echo -e "  🔄 待转换: ${PENDING} 个脚本"
echo ""

# 下一步建议
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}下一步建议${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ ${TOTAL_PINE} -lt 500 ]; then
    echo -e "${YELLOW}[建议]${NC}"
    echo -e "  📊 先爬取到 500 个脚本（阶段 1）"
    echo -e "  📈 然后进行转换（阶段 2）"
    echo -e "  📈 最后进行回测（阶段 3）"
elif [ ! -z "$SCRAPE_PID" ] && [ -n "$CONVERSION_RATE" ] && [ "$CONVERSION_RATE" != "N/A" ]; then
    echo -e "${GREEN}[就绪]${NC}"
    echo -e "  📊 爬取完成"
    echo -e "  🤖 智谱 AI 额度：${GREEN}充足${NC} (如果上面显示绿色)"
    echo -e "  🚀 可以开始转换（阶段 2）"
else
    echo -e "${YELLOW}[建议]${NC}"
    echo -e "  📊 先继续爬取到 500 个脚本（阶段 1）"
    echo -e "  📈 然后检查智谱 AI 额度"
    echo -e "  📈 额度恢复后开始转换（阶段 2）"
fi
echo ""
