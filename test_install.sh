#!/bin/bash
# 快速测试脚本

echo "=========================================="
echo "OpenClaw TradingView - 环境检查"
echo "=========================================="

# 检查 Python 虚拟环境
if [ -f "./venv/bin/python" ]; then
    echo "✅ Python 虚拟环境已创建"
    ./venv/bin/python --version
else
    echo "❌ Python 虚拟环境不存在"
    exit 1
fi

# 检查依赖
echo ""
echo "检查核心依赖..."

./venv/bin/pip list | grep -q "anthropic" && echo "✅ anthropic" || echo "❌ anthropic"
./venv/bin/pip list | grep -q "backtesting" && echo "✅ backtesting" || echo "❌ backtesting"
./venv/bin/pip list | grep -q "playwright" && echo "✅ playwright" || echo "❌ playwright"
./venv/bin/pip list | grep -q "pandas" && echo "✅ pandas" || echo "❌ pandas"
./venv/bin/pip list | grep -q "pandas-ta" && echo "✅ pandas-ta" || echo "❌ pandas-ta"
./venv/bin/pip list | grep -q "yfinance" && echo "✅ yfinance" || echo "❌ yfinance"

# 检查 LLM provider 依赖
echo ""
echo "检查 LLM provider 依赖..."

./venv/bin/pip list | grep -q "openai" && echo "✅ openai (GPT)" || echo "⚠️  openai (GPT) 未安装"
./venv/bin/pip list | grep -q "google-generativeai" && echo "✅ google-generativeai (Gemini)" || echo "⚠️  google-generativeai (Gemini) 未安装"
./venv/bin/pip list | grep -q "zhipuai" && echo "✅ zhipuai (智谱 AI)" || echo "⚠️  zhipuai (智谱 AI) 未安装"

# 检查 Playwright 浏览器
echo ""
echo "检查 Playwright 浏览器..."
if ./venv/bin/python -c "from playwright.sync_api import sync_playwright" 2>/dev/null; then
    echo "✅ Playwright Python 库已安装"
else
    echo "❌ Playwright Python 库未安装"
fi

# 检查环境变量
echo ""
echo "检查环境配置..."
if [ -f "./.env" ]; then
    echo "✅ .env 文件存在"

    # 检查 LLM provider 配置
    if grep -q "LLM_PROVIDER=" .env; then
        PROVIDER=$(grep "LLM_PROVIDER=" .env | cut -d'=' -f2)
        echo "✅ LLM_PROVIDER: ${PROVIDER}"
    else
        echo "⚠️  LLM_PROVIDER 未配置 (默认: anthropic)"
    fi
else
    echo "❌ .env 文件不存在"
fi

if [ -f "./results/.tv_cookies.json" ]; then
    echo "✅ TradingView Cookies 存在"
else
    echo "⚠️  TradingView Cookies 不存在 (运行爬虫需要)"
fi

# 检查 API Keys
echo ""
echo "检查 API Keys..."

if grep -q "ZHIPU_API_KEY=" .env 2>/dev/null && ! grep "ZHIPU_API_KEY=你的" .env 2>/dev/null; then
    echo "✅ ZHIPU_API_KEY 已配置 (推荐 免费)"
elif grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
    echo "✅ OPENAI_API_KEY 已配置"
elif grep -q "GEMINI_API_KEY=" .env 2>/dev/null && ! grep "GEMINI_API_KEY=AIza" .env 2>/dev/null; then
    echo "✅ GEMINI_API_KEY 已配置"
elif grep -q "ANTHROPIC_API_KEY=sk-ant-" .env 2>/dev/null; then
    echo "✅ ANTHROPIC_API_KEY 已配置"
else
    echo "⚠️  ⚠️  ⚠️  没有配置任何 API Key！"
    echo ""
    echo "请选择一个并配置:"
    echo "  1. Zhipu (智谱 AI) - 推荐 完全免费"
    echo "     获取: https://open.bigmodel.cn/usercenter/apikeys"
    echo "     配置: ZHIPU_API_KEY=你的密钥"
    echo ""
    echo "  2. OpenAI (GPT) - 需要 API Key"
    echo "     获取: https://platform.openai.com/api-keys"
    echo "     配置: OPENAI_API_KEY=sk-xxx"
    echo ""
    echo "  3. Gemini (Google) - 需要 API Key"
    echo "     获取: https://makersuite.google.com/app/apikey"
    echo "     配置: GEMINI_API_KEY=AIzaSy-xxx"
fi

# 创建必要目录
echo ""
echo "创建必要的目录..."
mkdir -p results logs
echo "✅ 目录已创建"

echo ""
echo "=========================================="
echo "环境检查完成"
echo "=========================================="
echo ""
echo "下一步:"
if [ -f "./results/.tv_cookies.json" ]; then
    echo "1. 配置一个 API Key (见上方 ⚠️  说明)"
    echo "2. 测试转换: ./venv/bin/python test_conversion.py"
    echo "3. 运行爬虫: ./venv/bin/python scripts/batch_scraper.py --category popular --limit 5"
else
    echo "1. 导出 TradingView Cookies 到 results/.tv_cookies.json"
    echo "2. 配置一个 API Key (见上方 ⚠️  说明)"
    echo "3. 测试转换: ./venv/bin/python test_conversion.py"
    echo "4. 运行爬虫: ./venv/bin/python scripts/batch_scraper.py --category popular --limit 5"
fi
echo ""
echo "详细文档: cat DEPLOY_GUIDE.md"
echo "配置指南: cat .env"
