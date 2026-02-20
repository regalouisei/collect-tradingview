# OpenClaw TradingView 部署指南

## ✅ 已完成

1. ✅ 克隆仓库到 `/root/.openclaw/workspace/openclaw-tradingview`
2. ✅ 创建 Python 虚拟环境 (`venv/`)
3. ✅ 安装核心依赖:
   - anthropic (Claude API)
   - backtesting (回测引擎)
   - pandas, pandas-ta (数据分析)
   - yfinance (市场数据)
   - playwright (浏览器自动化)
   - fastapi, uvicorn (API 服务器)
4. ✅ 安装 Playwright Chromium 浏览器
5. ✅ 创建环境配置模板 (`.env`)

## 🔧 需要手动配置

### 1. Anthropic API Key

获取方式：
1. 访问 https://console.anthropic.com
2. 注册/登录
3. 创建 API Key
4. 编辑 `.env` 文件：
   ```bash
   ANTHROPIC_API_KEY=sk-ant-xxxxx
   ```

### 2. TradingView Cookies (必需)

**方法 A: 使用浏览器导出 (推荐)**

1. 在浏览器中登录 TradingView
2. 打开开发者工具 (F12)
3. 切换到 "Application" 标签
4. 左侧找到 "Cookies" → "https://www.tradingview.com"
5. 点击 "Export cookies" 或手动复制所有 cookie
6. 保存为 JSON 格式到 `results/.tv_cookies.json`

**Cookie JSON 格式示例：**
```json
[
  {"name": "sessionid", "value": "xxx", "domain": ".tradingview.com"},
  {"name": "sessionid_sign", "value": "yyy", "domain": ".tradingview.com"}
]
```

### 3. (可选) Supabase 配置

如果需要存储结果到数据库：
1. 访问 https://supabase.com 创建项目
2. 获取 URL 和 Key
3. 编辑 `.env`:
   ```bash
   SUPABASE_URL=https://xxx.supabase.co
   SUPABASE_KEY=eyJxxx
   ```

### 4. (可选) Telegram 通知

如果需要 Telegram 通知：
1. 创建 Telegram Bot (@BotFather)
2. 获取 Bot Token
3. 获取 Chat ID (@userinfobot)
4. 编辑 `.env`:
   ```bash
   TELEGRAM_BOT_TOKEN=12345:ABC-DEF
   TELEGRAM_CHAT_ID=-100123456789
   ```

## 🚀 快速开始

### 测试爬虫 (需要先配置 Cookies)

```bash
cd /root/.openclaw/workspace/openclaw-tradingview
./venv/bin/python scripts/batch_scraper.py --category editors_picks --limit 5
```

### 测试完整流程

```bash
# 1. 爬取脚本
./venv/bin/python scripts/batch_scraper.py --category popular --limit 10

# 2. 转换并回测
./venv/bin/python scripts/run_pipeline.py --limit 5
```

## 📅 定时任务 (自动运行)

### 方法 1: Cron (推荐)

```bash
# 编辑 crontab
crontab -e

# 添加以下内容 (每天凌晨 2 点运行)
0 2 * * * cd /root/.openclaw/workspace/openclaw-tradingview && ./venv/bin/python scripts/batch_scraper.py --all --incremental >> logs/cron.log 2>&1
0 4 * * * cd /root/.openclaw/workspace/openclaw-tradingview && ./venv/bin/python scripts/run_pipeline.py >> logs/cron.log 2>&1
```

### 方法 2: 使用 daily_run.sh

```bash
# 修改 daily_run.sh 中的路径
PROJ_DIR="/root/.openclaw/workspace/openclaw-tradingview"

# 设置执行权限
chmod +x scripts/daily_run.sh

# 添加到 crontab
0 2 * * * /root/.openclaw/workspace/openclaw-tradingview/scripts/daily_run.sh
```

## 📊 结果查看

### CSV 日志
```bash
cat results/pipeline_results.csv
```

### 回测代码
```bash
ls -lh backtests/
```

### Pine Script 源码
```bash
ls -lh pinescript/
```

## 🎯 主要功能

### 1. 爬取 TradingView 脚本

```bash
# 爬取所有分类
./venv/bin/python scripts/batch_scraper.py --all --incremental

# 爬取特定分类
./venv/bin/python scripts/batch_scraper.py --category editors_picks

# 使用自定义 URL 列表
./venv/bin/python scripts/batch_scraper.py --urls scripts/urls_custom.json
```

**支持的分类：**
- `editors_picks` - 编辑精选
- `popular` - 热门
- `top` - 顶级
- `trending` - 趋势
- `oscillators` - 震荡指标
- `trend_analysis` - 趋势分析
- `volume` - 成交量
- `moving_averages` - 移动平均
- `volatility` - 波动率
- `momentum` - 动量

### 2. 转换并回测

```bash
# 处理所有未处理的脚本
./venv/bin/python scripts/run_pipeline.py

# 处理特定分类
./venv/bin/python scripts/run_pipeline.py --category popular

# 限制数量
./venv/bin/python scripts/run_pipeline.py --limit 10

# 重新运行已处理的脚本
./venv/bin/python scripts/run_pipeline.py --rerun
```

### 3. 更新排名

```bash
./venv/bin/python scripts/update_rankings.py
```

## 🔍 故障排查

### 爬虫失败

**错误:** `No cookies file at results/.tv_cookies.json`

**解决:** 确保 `results/.tv_cookies.json` 存在且格式正确

**错误:** `Cannot find page element`

**解决:** TradingView 可能更新了页面结构，需要更新爬虫代码

### 转换失败

**错误:** `ANTHROPIC_API_KEY not set`

**解决:** 在 `.env` 中设置 `ANTHROPIC_API_KEY`

**错误:** `Conversion failed: no Strategy class found`

**解决:** Claude Haiku 没有正确生成代码，可能需要手动调整或重试

### 回测失败

**错误:** `Insufficient data`

**解决:** 检查数据获取是否成功，可能需要调整时间范围

**错误:** `ValueError: indicator calculation returned None`

**解决:** 某些指标在数据不足时会返回 None，需要添加保护代码

## 📈 性能优化

### 并行处理

修改 `run_pipeline.py` 中的循环，添加多线程处理：

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_single_pine, pines))
```

### 缓存数据

市场数据会自动缓存到 `results/` 目录

### 增量更新

使用 `--incremental` 标志跳过已处理的脚本

## 📝 项目结构

```
openclaw-tradingview/
├── api/              # FastAPI 接口
├── backtests/        # 生成的 Python 回测代码
├── framework/        # 核心框架
│   ├── backtest_engine.py    # 回测引擎
│   ├── pine_converter.py     # Pine → Python 转换
│   ├── data_fetcher.py      # 市场数据获取
│   └── ...
├── pinescript/       # 爬取的 Pine Script 源码
├── scripts/          # 主要脚本
│   ├── batch_scraper.py      # 批量爬虫
│   ├── run_pipeline.py       # 流水线
│   └── ...
├── results/          # 结果和状态文件
│   ├── .tv_cookies.json      # TradingView Cookies
│   ├── .scrape_state.json   # 爬虫状态
│   └── .pipeline_state.json  # 流水线状态
└── venv/             # Python 虚拟环境
```

## 🆘 支持

- GitHub: https://github.com/eddiebelaval/openclaw-tradingview
- Anthropic Docs: https://docs.anthropic.com
- Backtesting.py Docs: https://kernc.github.io/backtesting.py/

## 📄 许可证

MIT License
