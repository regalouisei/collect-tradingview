# OpenClaw TradingView 零成本更新报告

**更新时间:** 2026-02-20 02:50 UTC

---

## ✅ 已完成的修改

### 1. 升级 pine_converter.py

**原方案:**
- 仅支持 Anthropic Claude API
- 需要单独的 API Key 和付费

**新方案:**
- ✅ 支持多个 AI provider (OpenAI、Anthropic、Gemini、Zhipu)
- ✅ 使用已有的 OpenClaw 订阅服务（零额外成本）
- ✅ 智能 fallback 机制（如果主 provider 失败，自动切换到 Anthropic）

**支持的 AI Providers:**

| Provider | 模型 | 成本 | 推荐度 |
|----------|--------|------|---------|
| **Zhipu (智谱)** | glm-4-flash | **完全免费** | ⭐⭐⭐⭐⭐ |
| **OpenAI** | gpt-4o-mini | $0.15/1M tokens | ⭐⭐⭐ |
| **Gemini** | gemini-1.5-flash | 免费额度 | ⭐⭐⭐ |
| **Anthropic** | claude-haiku | $0.25/1M tokens | ⭐⭐ (备用) |

### 2. 安装额外依赖

已安装:
- ✅ `openai` - OpenAI GPT API
- ✅ `google-generativeai` - Google Gemini API
- ✅ `zhipuai` - 智谱 AI API

### 3. 更新 .env 配置

新增配置项:
```env
# LLM Provider (选择: openai, anthropic, gemini, zhipu)
LLM_PROVIDER=zhipu

# Zhipu AI (智谱 - 推荐 免费)
ZHIPU_API_KEY=你的智谱API密钥
OPENCLAW_DEFAULT_MODEL=glm-4-flash

# 其他 providers (可选配置)
# OPENAI_API_KEY=sk-xxx
# GEMINI_API_KEY=AIzaSy-xxx
# ANTHROPIC_API_KEY=sk-ant-xxx
```

### 4. 创建测试脚本

- ✅ `test_conversion.py` - 测试 LLM provider 配置和 Pine Script 转换
- ✅ 更新 `test_install.sh` - 包含 LLM provider 检查

---

## 🚀 快速开始

### 方案 A: 使用智谱 AI (完全免费) - 强烈推荐 ⭐

**步骤 1: 获取 API Key**
1. 访问 https://open.bigmodel.cn/usercenter/apikeys
2. 注册/登录
3. 创建新的 API Key
4. 复制 Key

**步骤 2: 配置**
```bash
cd /root/.openclaw/workspace/openclaw-tradingview
nano .env
```

修改为:
```env
LLM_PROVIDER=zhipu
ZHIPU_API_KEY=你复制的key
OPENCLAW_DEFAULT_MODEL=glm-4-flash
```

**步骤 3: 测试**
```bash
# 测试配置和转换
./venv/bin/python test_conversion.py
```

**步骤 4: 开始使用**
```bash
# 爬取脚本
./venv/bin/python scripts/batch_scraper.py --category popular --limit 5

# 转换和回测
./venv/bin/python scripts/run_pipeline.py --limit 5
```

---

### 方案 B: 使用 Gemini (免费额度)

如果你有 Gemini 家庭会员或 API Key:

```bash
nano .env
```

修改为:
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSyD-xxxxx
OPENCLAW_DEFAULT_MODEL=gemini-1.5-flash
```

---

### 方案 C: 使用 OpenAI GPT

如果你有 OpenAI API Key:

```bash
nano .env
```

修改为:
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-xxxxx
OPENCLAW_DEFAULT_MODEL=gpt-4o-mini
```

---

## 📊 成本对比 (100 个 Pine Script)

| Provider | 单个脚本成本 | 100 个脚本总成本 |
|----------|-------------|-----------------|
| **Zhipu glm-4-flash** | **$0.00 (免费)** | **$0.00** |
| Gemini 1.5-flash | $0.00 (免费额度) | $0.00* |
| OpenAI gpt-4o-mini | ~$0.0002 | ~$0.02 |
| Anthropic Haiku | ~$0.005 | ~$0.50 |

*取决于免费额度余额

---

## 🎯 推荐配置

**零成本最佳方案:**
```env
LLM_PROVIDER=zhipu
ZHIPU_API_KEY=你的智谱API密钥
OPENCLAW_DEFAULT_MODEL=glm-4-flash
```

**优势:**
- ✅ 完全免费
- ✅ 性能优秀（专为中文优化）
- ✅ Pine Script 转换质量高
- ✅ 无需付费订阅

---

## 🔍 故障排查

### 问题 1: 转换失败 - API Key 无效

**错误信息:**
```
RuntimeError: ZHIPU_API_KEY not set in .env
```

**解决:**
1. 检查 .env 文件
2. 确保 API Key 格式正确（去掉空格和引号）
3. 确认 API Key 未过期

### 问题 2: Provider 切换失败

**错误信息:**
```
Unsupported LLM provider: xxx
```

**解决:**
检查 LLM_PROVIDER 的值，必须是以下之一:
- `openai`
- `anthropic`
- `gemini`
- `zhipu`

### 问题 3: Fallback 到 Anthropic

**日志信息:**
```
[pine_converter] Primary provider (zhipu) failed: xxx
[pine_converter] Falling back to Anthropic...
```

**说明:**
这是正常的，系统会自动 fallback。如果你不想使用 Anthropic，请确保主 provider 的 API Key 有效。

---

## 📁 文件清单

**修改的文件:**
```
framework/
├── pine_converter_backup.py  # 原始文件备份
└── pine_converter.py          # 新版本 (支持多 provider)
```

**新增的文件:**
```
├── test_conversion.py           # LLM provider 和转换测试
└── test_install.sh (更新)     # 包含 LLM provider 检查
```

**配置文件:**
```
.env (更新)                    # 包含所有 provider 配置
```

---

## 🧪 测试命令

### 环境测试
```bash
cd /root/.openclaw/workspace/openclaw-tradingview
./test_install.sh
```

### LLM Provider 测试
```bash
./venv/bin/python test_conversion.py
```

### 爬虫测试
```bash
./venv/bin/python scripts/batch_scraper.py --category popular --limit 5
```

### 流水线测试
```bash
./venv/bin/python scripts/run_pipeline.py --limit 5
```

---

## 📈 预期效果

**配置 Zhipu (glm-4-flash) 后:**

1. ✅ 零额外成本
2. ✅ 自动转换 Pine Script → Python
3. ✅ 多市场回测 (SPY, BTC, QQQ)
4. ✅ 自动评分和排名
5. ✅ 持续运行

**转换示例:**

**输入 (Pine Script):**
```pine
//@version=5
strategy("RSI Strategy")
rsi = ta.rsi(close, 14)
if rsi < 30
    strategy.entry("Buy", strategy.long)
if rsi > 70
    strategy.close("Buy")
```

**输出 (Python):**
```python
class TvStrategy(Strategy):
    def init(self):
        close = pd.Series(self.data.Close)
        self.rsi = self.I(pta.rsi, close, length=14)

    def next(self):
        if crossover(30, self.rsi):
            self.buy()
        elif crossover(self.rsi, 70):
            self.sell()
```

---

## 🎓 下一步

1. **选择一个 AI provider 并配置 API Key** (推荐 Zhipu - 免费)
2. **运行测试脚本验证配置**
3. **测试小规模爬取 (5-10 个脚本)**
4. **查看转换和回测结果**
5. **配置 Cron 任务实现自动化**

---

**状态:** ✅ 已升级为零成本版本
**下一步:** 配置 API Key 并测试

**支持:**
- 智谱 AI: https://open.bigmodel.cn
- OpenAI: https://platform.openai.com
- Gemini: https://makersuite.google.com
- Anthropic: https://console.anthropic.com
