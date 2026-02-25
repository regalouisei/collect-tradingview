#!/bin/bash
# Cline-assisted Pine Script conversion script (AUTO MODE)
# 自动运行，无需用户输入

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

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Cline 自动转换脚本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 统计信息
TOTAL_PINE=$(find pinescript -name "*.pine" 2>/dev/null | wc -l)
TOTAL_PYTHON=$(find backtests -name "*.py" 2>/dev/null | wc -l)

echo -e "${YELLOW}[统计]${NC}"
echo -e "  Pine Scripts: ${TOTAL_PINE}"
echo -e "  Python 回测: ${TOTAL_PYTHON}"
echo -e "  待转换: $((TOTAL_PINE - TOTAL_PYTHON))"
echo ""

# 找出所有 Pine Script 文件
echo -e "${YELLOW}[1/2] 扫描 Pine Scripts...${NC}"
PINE_FILES=($(find pinescript -name "*.pine" -type f 2>/dev/null))
echo -e "  找到 ${#PINE_FILES[@]} 个 Pine Scripts"
echo ""

# 找出待转换的脚本（没有对应的 Python 回测文件）
echo -e "${YELLOW}[2/2] 识别待转换脚本...${NC}"
PENDING_SCRIPTS=()

for pine_file in "${PINE_FILES[@]}"; do
    category=$(basename $(dirname "$pine_file"))
    script_name=$(basename "$pine_file" .pine)
    python_file="backtests/${category}/${script_name}.py"

    if [ ! -f "$python_file" ]; then
        PENDING_SCRIPTS+=("$pine_file")
    fi
done

echo -e "  待转换: ${#PENDING_SCRIPTS[@]} 个脚本"
echo ""

if [ ${#PENDING_SCRIPTS[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ 所有脚本都已转换！${NC}"
    exit 0
fi

# 开始转换
echo ""
echo -e "${MAGENTA}开始自动转换...${NC}"
echo ""

SUCCESS_COUNT=0
FAILED_COUNT=0

for i in "${!PENDING_SCRIPTS[@]}"; do
    pine_file="${PENDING_SCRIPTS[$i]}"
    script_name=$(basename "$pine_file" .pine)
    category=$(basename $(dirname "$pine_file"))

    echo -e "${CYAN}[$((i+1))/${#PENDING_SCRIPTS[@]}]${NC} ${script_name} (${category})"

    # 读取 Pine Script
    pine_code=$(cat "$pine_file")

    # 构建 Cline 提示词
    cline_prompt="Convert this Pine Script to a Python backtest file using backtesting.py and pandas_ta libraries.

Script name: ${script_name}
Category: ${category}

Requirements:
1. Import from backtesting: \`from backtesting import Backtest, Strategy\`
2. Import from backtesting.lib: \`from backtesting.lib import crossover\` (if needed)
3. Use \`pandas_ta\` for indicator calculations (import as \`import pandas_ta as pta\`)
4. Import pandas and numpy as needed
5. Define a Strategy class with \`__init__()\` and \`next()\` methods
6. The Strategy class MUST be named \`TvStrategy\`

Trading rules:
- Create reasonable entry/exit rules based on indicator logic
- Use self.buy() and self.sell() for entries
- Use self.sell() to exit longs, self.buy() to exit shorts

IMPORTANT:
- Use self.I() wrapper for ALL indicator calculations in __init__()
- All indicator functions MUST return numpy arrays or pandas Series, NEVER return None
- Never use \`lambda\` keyword inside self.I() wrappers
- Always check if indicator calculation returns None before using it
- In next(), access current values via self.indicator_name[-1]

Return ONLY of Python code. No explanations, no markdown fences.

Pine Script:
\`\`\`pine
${pine_code}
\`\`\`"

    # 保存临时文件
    echo "$pine_code" > /tmp/temp_pine.pine

    # 使用 Cline 转换（自动模式，不询问）
    if cline -m claude-sonnet-4-5-20241022 -t 300 -y -p /tmp/temp_pine.pine "$cline_prompt" > /tmp/temp_python.py 2>&1; then
        # 转换成功
        python_code=$(cat /tmp/temp_python.py)

        # 检查 Python 代码是否有效
        if python3 -m py_compile /tmp/temp_python.py 2>/dev/null; then
            # 保存回测文件
            category_dir="backtests/${category}"
            mkdir -p "$category_dir"
            python_file="${category_dir}/${script_name}.py"
            echo "$python_code" > "$python_file"

            echo -e "    ${GREEN}✅ 转换成功${NC}"
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        else
            echo -e "    ${YELLOW}⚠️  Python 语法错误${NC}"
            FAILED_COUNT=$((FAILED_COUNT + 1))
        fi
    else
        echo -e "    ${YELLOW}⚠️  Cline 转换失败${NC}"
        FAILED_COUNT=$((FAILED_COUNT + 1))
    fi
    
    # 清理临时文件
    rm -f /tmp/temp_pine.pine /tmp/temp_python.py

    # 小延迟，避免速率限制
    if [ $((i % 5)) -eq 4 ]; then
        sleep 2
    fi
done

# 最终统计
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}转换完成${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}[最终统计]${NC}"
echo -e "  总尝试: ${#PENDING_SCRIPTS[@]}"
echo -e "  成功: ${SUCCESS_COUNT}"
echo -e "  失败: ${FAILED_COUNT}"
echo ""
echo -e "${GREEN}💰 成本: $0.00 (使用你的 Cline 账户)${NC}"
echo ""
