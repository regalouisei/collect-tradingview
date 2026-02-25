#!/bin/bash
# OpenClaw TradingView - 自动化启动脚本
# 用途：快速启动 TradingView 爬取和转换任务

set -e

PROJECT_DIR="/root/.openclaw/workspace/openclaw-tradingview"
cd "$PROJECT_DIR"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}OpenClaw TradingView 自动化${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查环境
echo -e "${YELLOW}[1/5] 检查环境...${NC}"
if [ ! -f "./venv/bin/python" ]; then
    echo -e "❌ Python 虚拟环境不存在"
    exit 1
fi
echo -e "✅ Python 环境: $(./venv/bin/python --version)"

if [ ! -f "./.env" ]; then
    echo -e "⚠️  .env 文件不存在"
fi

# 检查 API Key
echo -e "${YELLOW}[2/5] 检查 API Key...${NC}"
if grep -q "ZHIPU_API_KEY=" ./.env 2>/dev/null && ! grep "ZHIPU_API_KEY=你的" .env 2>/dev/null; then
    echo -e "✅ 智谱 AI API Key 已配置"
elif grep -q "OPENAI_API_KEY=sk-" ./.env 2>/dev/null; then
    echo -e "✅ OpenAI API Key 已配置"
elif grep -q "GEMINI_API_KEY=AIzaSyD" ./.env 2>/dev/null; then
    echo -e "✅ Gemini API Key 已配置"
elif grep -q "ANTHROPIC_API_KEY=sk-ant-" ./.env 2>/dev/null; then
    echo -e "✅ Anthropic API Key 已配置"
else
    echo -e "⚠️  没有 API Key 配置"
fi

# 检查 TradingView Cookies
echo -e "${YELLOW}[3/5] 检查 TradingView Cookies...${NC}"
if [ -f "./results/.tv_cookies.json" ]; then
    COOKIE_COUNT=$(cat ./results/.tv_cookies.json | jq '. | length')
    echo -e "✅ Cookies 存在 ($COOKIE_COUNT 个)"
else
    echo -e "❌ Cookies 文件不存在：./results/.tv_cookies.json"
    echo -e "   请手动导出 TradingView Cookies 并保存"
fi

echo ""

# 菜单
echo -e "${BLUE}请选择操作：${NC}"
echo -e "  ${GREEN}1${NC} - 增量爬取所有分类（推荐）"
echo -e "  ${GREEN}2${NC} - 爬取特定分类"
echo -e "  ${GREEN}3${NC} - 转换并回测所有新脚本"
echo -e "  ${GREEN}4${NC} - 完整自动化流程（爬取+转换+回测）"
echo -e "  ${YELLOW}5${NC} - 查看系统状态"
echo -e "  ${YELLOW}6${NC} - 配置 Cron 任务"
echo -e "  ${YELLOW}0${NC} - 退出"
echo ""

read -p "请输入选项 [0-6]: " choice

case $choice in
    1)
        echo -e "${YELLOW}执行：增量爬取所有分类...${NC}"
        echo ""
        ./venv/bin/python scripts/batch_scraper.py --all --incremental
        ;;
    2)
        echo "可用分类："
        echo "  editors_picks, popular, top, trending"
        echo "  oscillators, trend_analysis, volume"
        echo "  moving_averages, volatility, momentum"
        echo ""
        read -p "请输入分类名称: " category
        read -p "请输入数量限制 (默认 50): " limit
        limit=${limit:-50}
        echo ""
        echo -e "${YELLOW}执行：爬取 $category (limit $limit)...${NC}"
        ./venv/bin/python scripts/batch_scraper.py --category "$category" --limit "$limit"
        ;;
    3)
        echo -e "${YELLOW}执行：转换并回测所有新脚本...${NC}"
        echo ""
        ./venv/bin/python scripts/run_pipeline.py
        ;;
    4)
        echo -e "${YELLOW}执行：完整自动化流程...${NC}"
        echo ""
        echo "1. 爬取所有分类（增量模式）"
        ./venv/bin/python scripts/batch_scraper.py --all --incremental

        echo ""
        echo "2. 转换并回测所有新脚本"
        ./venv/bin/python scripts/run_pipeline.py

        echo ""
        echo "3. 更新排名"
        ./venv/bin/python scripts/update_rankings.py

        echo ""
        echo -e "${GREEN}✅ 完整流程执行完成！${NC}"
        ;;
    5)
        echo -e "${YELLOW}系统状态：${NC}"
        echo ""

        # 爬取状态
        if [ -f "./results/.scrape_state.json" ]; then
            SCRAPED=$(cat ./results/.scrape_state.json | jq '.scraped | length')
            echo "已爬取脚本: $SCRAPED"
        fi

        # 流水线状态
        if [ -f "./results/.pipeline_state.json" ]; then
            PROCESSED=$(cat ./results/.pipeline_state.json | jq '.processed | length')
            FAILED=$(cat ./results/.pipeline_state.json | jq '.failed | length')
            echo "已处理脚本: $PROCESSED"
            echo "失败转换: $FAILED"
        fi

        # CSV 结果
        if [ -f "./results/pipeline_results.csv" ]; then
            TOTAL=$(wc -l < ./results/pipeline_results.csv)
            echo "CSV 总记录: $TOTAL"
        fi

        # 最近日志
        if [ -d "./logs" ]; then
            echo ""
            echo "最近日志："
            ls -lt ./logs/ | head -5
        fi
        ;;
    6)
        echo "配置 Cron 任务："
        echo ""
        echo "请手动执行以下命令配置 crontab："
        echo ""
        echo -e "${YELLOW}crontab -e${NC}"
        echo ""
        echo "然后添加以下内容："
        echo ""
        echo -e "${GREEN}# 每天凌晨 2:00 增量爬取${NC}"
        echo "0 2 * * * cd /root/.openclaw/workspace/openclaw-tradingview && /root/.openclaw/workspace/openclaw-tradingview/venv/bin/python scripts/batch_scraper.py --all --incremental >> /root/.openclaw/workspace/openclaw-tradingview/logs/cron-scrape.log 2>&1"
        echo ""
        echo -e "${GREEN}# 每天凌晨 5:00 转换和回测${NC}"
        echo "0 5 * * * cd /root/.openclaw/workspace/openclaw-tradingview && /root/.openclaw/workspace/openclaw-tradingview/venv/bin/python scripts/run_pipeline.py >> /root/.openclaw/workspace/openclaw-tradingview/logs/cron-pipeline.log 2>&1"
        echo ""
        echo "保存并退出 crontab"
        ;;
    0)
        echo "退出"
        exit 0
        ;;
    *)
        echo "无效选项"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}操作完成${NC}"
echo -e "${BLUE}========================================${NC}"
