#!/bin/bash
# 快速启动脚本 - 优化版 OpenClaw TradingView
# 策略：并发爬取 + 去重 + 批量处理

set -e

PROJECT_DIR="/root/.openclaw/workspace/openclaw-tradingview"
cd "$PROJECT_DIR"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置参数
LIMIT_PER_CATEGORY=25      # 每个分类爬取的脚本数量
MAX_WORKERS=4               # 并发爬取的分类数
TARGET_TOTAL=200           # 目标总脚本数
USE_AGGRESSIVE=true        # 使用激进滚动模式

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}OpenClaw TradingView - 快速启动${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查环境
echo -e "${YELLOW}[1/6] 检查环境...${NC}"
if [ ! -f "./venv/bin/python" ]; then
    echo -e "❌ Python 虚拟环境不存在"
    exit 1
fi
echo -e "✅ Python 环境: $(./venv/bin/python --version)"

# 检查配置
echo -e "${YELLOW}[2/6] 检查配置...${NC}"
if [ -f "./results/.tv_cookies.json" ]; then
    COOKIE_COUNT=$(cat ./results/.tv_cookies.json | jq '. | length')
    echo -e "✅ TradingView Cookies: ${COOKIE_COUNT} 个 cookies"
else
    echo -e "❌ TradingView Cookies 不存在"
    exit 1
fi

if grep -q "ZHIPU_API_KEY=" .env 2>/dev/null && ! grep "ZHIPU_API_KEY=你的" .env 2>/dev/null; then
    echo -e "✅ 智谱 AI API Key 已配置"
else
    echo -e "❌ 智谱 AI API Key 未配置"
    exit 1
fi

# 统计当前脚本数量
echo -e "${YELLOW}[3/6] 统计当前脚本...${NC}"
CURRENT_TOTAL=$(find pinescript -name "*.pine" 2>/dev/null | wc -l)
echo -e "📊 当前脚本总数: ${CURRENT_TOTAL}"

# 计算需要爬取的数量
NEEDED=$((TARGET_TOTAL - CURRENT_TOTAL))
if [ $NEEDED -le 0 ]; then
    echo -e "${GREEN}已达到目标 ${TARGET_TOTAL} 个脚本！${NC}"
    echo ""
    echo -e "${YELLOW}[4/6] 开始转换和回测...${NC}"
    ./venv/bin/python scripts/run_pipeline.py
    echo -e "${GREEN}✅ 转换和回测完成！${NC}"
    exit 0
fi

echo -e "🎯 目标: ${TARGET_TOTAL} 个脚本"
echo -e "📊 当前: ${CURRENT_TOTAL} 个脚本"
echo -e "🔄 需要: ${NEEDED} 个脚本"
echo ""

# 菜单
echo -e "${BLUE}请选择操作模式：${NC}"
echo -e ""
echo -e "  ${GREEN}1${NC} - 快速爬取模式（推荐）"
echo -e "      并发爬取所有分类，各 ${LIMIT_PER_CATEGORY} 个"
echo -e "      预计约 ${LIMIT_PER_CATEGORY} * 8 = $((LIMIT_PER_CATEGORY * 8)) 个新脚本"
echo ""
echo -e "  ${GREEN}2${NC} - 激进爬取模式"
echo -e "      并发爬取所有分类，各 50 个（激进滚动）"
echo -e "      预计约 50 * 8 = 400 个新脚本"
echo ""
echo -e "  ${GREEN}3${NC} - 目标爬取模式"
echo -e "      爬取直到达到 ${TARGET_TOTAL} 个脚本"
echo -e "      预计需要 $(( (NEEDED / (LIMIT_PER_CATEGORY * 8)) + 1 )) 轮次"
echo ""
echo -e "  ${MAGENTA}4${NC} - 爬取到指定数量"
echo -e "      输入需要爬取的脚本数量"
echo ""
echo -e "  ${CYAN}5${NC} - 转换并回测（不爬取）"
echo -e "      处理当前所有脚本"
echo ""
echo -e "  ${CYAN}6${NC} - 完整流程（爬取+转换+回测）"
echo -e "      先爬取到 ${TARGET_TOTAL} 个，再转换和回测"
echo ""
echo -e "  ${YELLOW}0${NC} - 退出"
echo ""

read -p "请输入选项 [0-6]: " choice

case $choice in
    1)
        echo -e "${YELLOW}执行：快速爬取模式...${NC}"
        echo ""

        ./venv/bin/python scripts/batch_scraper_optimized.py \
            --all \
            --limit ${LIMIT_PER_CATEGORY} \
            --aggressive \
            --workers ${MAX_WORKERS}

        echo ""
        echo -e "${GREEN}✅ 快速爬取完成！${NC}"

        # 统计结果
        NEW_TOTAL=$(find pinescript -name "*.pine" 2>/dev/null | wc -l)
        NEW_SCRIPTS=$((NEW_TOTAL - CURRENT_TOTAL))
        echo -e "📊 新增: ${NEW_SCRIPTS} 个脚本"
        echo -e "📊 总计: ${NEW_TOTAL} 个脚本"

        # 询问是否转换
        echo ""
        read -p "是否开始转换和回测？(y/n): " convert_choice
        if [ "$convert_choice" = "y" ] || [ "$convert_choice" = "Y" ]; then
            echo -e "${YELLOW}执行：转换和回测...${NC}"
            ./venv/bin/python scripts/run_pipeline.py --limit 50
            echo -e "${GREEN}✅ 转换和回测完成！${NC}"
        fi
        ;;

    2)
        echo -e "${YELLOW}执行：激进爬取模式...${NC}"
        echo ""
        echo -e "⚠️  激进模式可能错过一些脚本，但速度更快${NC}"
        echo ""

        ./venv/bin/python scripts/batch_scraper_optimized.py \
            --all \
            --limit 50 \
            --aggressive \
            --workers ${MAX_WORKERS}

        echo ""
        echo -e "${GREEN}✅ 激进爬取完成！${NC}"

        # 统计结果
        NEW_TOTAL=$(find pinescript -name "*.pine" 2>/dev/null | wc -l)
        NEW_SCRIPTS=$((NEW_TOTAL - CURRENT_TOTAL))
        echo -e "📊 新增: ${NEW_SCRIPTS} 个脚本"
        echo -e "📊 总计: ${NEW_TOTAL} 个脚本"
        ;;

    3)
        echo -e "${YELLOW}执行：目标爬取模式（达到 ${TARGET_TOTAL} 个脚本）...${NC}"
        echo ""

        # 轮次计数
        ROUND=0

        while [ $(find pinescript -name "*.pine" 2>/dev/null | wc -l) -lt $TARGET_TOTAL ]; do
            ROUND=$((ROUND + 1))
            CURRENT=$(find pinescript -name "*.pine" 2>/dev/null | wc -l)
            REMAINING=$((TARGET_TOTAL - CURRENT))

            echo -e "${CYAN}========================================${NC}"
            echo -e "${CYAN}第 ${ROUND} 轮：当前 ${CURRENT} / 目标 ${TARGET_TOTAL} (剩余 ${REMAINING})${NC}"
            echo -e "${CYAN}========================================${NC}"

            # 并发爬取所有分类
            ./venv/bin/python scripts/batch_scraper_optimized.py \
                --all \
                --limit ${LIMIT_PER_CATEGORY} \
                --aggressive \
                --workers ${MAX_WORKERS}

            echo ""
        done

        NEW_TOTAL=$(find pinescript -name "*.pine" 2>/dev/null | wc -l)
        echo -e "${GREEN}✅ 已达到目标 ${TARGET_TOTAL} 个脚本！实际: ${NEW_TOTAL} 个${NC}"
        ;;

    4)
        read -p "请输入需要爬取的脚本数量: " custom_limit
        if [ -z "$custom_limit" ] || [ $custom_limit -le 0 ]; then
            echo -e "❌ 无效的数量"
            exit 1
        fi

        echo -e "${YELLOW}执行：爬取 ${custom_limit} 个脚本...${NC}"
        echo ""

        ./venv/bin/python scripts/batch_scraper_optimized.py \
            --all \
            --limit $((custom_limit / 8)) \
            --aggressive \
            --workers ${MAX_WORKERS}

        echo ""
        echo -e "${GREEN}✅ 爬取完成！${NC}"
        ;;

    5)
        echo -e "${YELLOW}执行：转换并回测当前所有脚本...${NC}"
        echo ""

        ./venv/bin/python scripts/run_pipeline.py

        echo ""
        echo -e "${GREEN}✅ 转换和回测完成！${NC}"
        ;;

    6)
        echo -e "${YELLOW}执行：完整流程（爬取到 ${TARGET_TOTAL} 个 + 转换 + 回测）...${NC}"
        echo ""

        # 爬取到目标数量
        echo -e "${CYAN}[步骤 1/3] 爬取到 ${TARGET_TOTAL} 个脚本...${NC}"

        ROUND=0
        while [ $(find pinescript -name "*.pine" 2>/dev/null | wc -l) -lt $TARGET_TOTAL ]; do
            ROUND=$((ROUND + 1))
            CURRENT=$(find pinescript -name "*.pine" 2>/dev/null | wc -l)
            REMAINING=$((TARGET_TOTAL - CURRENT))

            echo ""
            echo -e "${CYAN}第 ${ROUND} 轮：${CURRENT}/${TARGET_TOTAL} (剩余 ${REMAINING})${NC}"

            ./venv/bin/python scripts/batch_scraper_optimized.py \
                --all \
                --limit ${LIMIT_PER_CATEGORY} \
                --aggressive \
                --workers ${MAX_WORKERS}
        done

        NEW_TOTAL=$(find pinescript -name "*.pine" 2>/dev/null | wc -l)
        echo ""
        echo -e "${GREEN}✅ 爬取完成：${NEW_TOTAL} 个脚本${NC}"

        # 转换和回测
        echo ""
        echo -e "${CYAN}[步骤 2/3] 转换并回测...${NC}"
        ./venv/bin/python scripts/run_pipeline.py

        echo ""
        echo -e "${GREEN}✅ 转换和回测完成！${NC}"

        # 更新排名
        echo ""
        echo -e "${CYAN}[步骤 3/3] 更新排名...${NC}"
        ./venv/bin/python scripts/update_rankings.py

        echo ""
        echo -e "${GREEN}✅ 排名更新完成！${NC}"
        echo ""
        echo -e "${MAGENTA}🎉 完整流程执行完成！${NC}"
        ;;

    0)
        echo "退出"
        exit 0
        ;;

    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}操作完成${NC}"
echo -e "${BLUE}========================================${NC}"

# 最终统计
echo ""
echo -e "${YELLOW}[最终统计]${NC}"
FINAL_TOTAL=$(find pinescript -name "*.pine" 2>/dev/null | wc -l)
echo -e "📊 总脚本数: ${FINAL_TOTAL}"

if [ -f "./results/.pipeline_state.json" ]; then
    PROCESSED=$(cat ./results/.pipeline_state.json | jq '.processed | length')
    FAILED=$(cat ./results/.pipeline_state.json | jq '.failed | length')
    echo -e "🤖 已转换: ${PROCESSED} 个"
    echo -e "❌ 转换失败: ${FAILED} 个"
fi

echo ""
echo -e "${GREEN}💰 成本: $0.00 (智谱 glm-4-flash 完全免费)${NC}"
echo ""
echo -e "${CYAN}下一步：${NC}"
echo -e "1. 查看转换结果: cat results/pipeline_results.csv"
echo -e "2. 查看回测代码: ls -lh backtests/*/"
echo -e "3. 继续爬取更多: 重新运行此脚本，选择选项 1、2 或 3"
