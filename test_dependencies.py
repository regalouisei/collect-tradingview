#!/usr/bin/env python3
"""
简单测试脚本 - 避免输出重定向问题
"""
import sys
import os
from datetime import datetime

def write_to_file(message: str):
    """写入到 /tmp 文件，避免输出重定向问题"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"

    try:
        with open("/tmp/scraper_test.log", "a", encoding='utf-8') as f:
            f.write(log_line + "\n")
    except Exception as e:
        print(f"无法写入日志文件: {e}", file=sys.stderr)

# 1. Python 版本检查
write_to_file("=" * 60)
write_to_file("1. Python 环境检查")
write_to_file("=" * 60)
write_to_file(f"Python 版本: {sys.version}")
write_to_file(f"执行路径: {sys.executable}")
write_to_file(f"脚本文件: {__file__}")
write_to_file(f"当前目录: {os.getcwd()}")
write_to_file("")

# 2. 检查 playwright
write_to_file("=" * 60)
write_to_file("2. Playwright 检查")
write_to_file("=" * 60)
try:
    import playwright
    write_to_file(f"Playwright 版本: {playwright.__version__}")
    write_to_file(f"Playwright 安装路径: {playwright.__path__}")
    write_to_file(f"Chromium 可用: {playwright.chromium.is_available()}")
    write_to_file("✅ Playwright 安装正常")
except ImportError as e:
    write_to_file(f"❌ Playwright 导入失败: {e}")
    write_to_file("需要安装: pip install playwright")
except Exception as e:
    write_to_file(f"❌ Playwright 检查失败: {e}")

# 3. 检查 pandas
write_to_file("")
write_to_file("=" * 60)
write_to_file("3. Pandas 检查")
write_to_file("=" * 60)
try:
    import pandas
    write_to_file(f"Pandas 版本: {pandas.__version__}")
    write_to_file("✅ Pandas 安装正常")
except ImportError as e:
    write_to_file(f"❌ Pandas 导入失败: {e}")
    write_to_file("需要安装: pip install pandas")
except Exception as e:
    write_to_file(f"❌ Pandas 检查失败: {e}")

# 4. 检查 yfinance
write_to_file("")
write_to_file("=" * 60)
write_to_file("4. Yfinance 检查")
write_to_file("=" * 60)
try:
    import yfinance
    write_to_file(f"Yfinance 版本: {yfinance.__version__}")
    write_to_file("✅ Yfinance 安装正常")
except ImportError as e:
    write_to_file(f"❌ Yfinance 导入失败: {e}")
    write_to_file("需要安装: pip install yfinance")
except Exception as e:
    write_to_file(f"❌ Yfinance 检查失败: {e}")

# 5. 检查 backtesting
write_to_file("")
write_to_file("=" * 60)
write_to_file("5. Backtesting 检查")
write_to_file("=" * 60)
try:
    import backtesting
    write_to_file(f"Backtesting 版本: {backtesting.__version__}")
    write_to_file("✅ Backtesting 安装正常")
except ImportError as e:
    write_to_file(f"❌ Backtesting 导入失败: {e}")
    write_to_file("需要安装: pip install backtesting")
except Exception as e:
    write_to_file(f"❌ Backtesting 检查失败: {e}")

# 6. 总结
write_to_file("")
write_to_file("=" * 60)
write_to_file("总结")
write_to_file("=" * 60)
write_to_file("所有依赖检查完成")
write_to_file("日志文件: /tmp/scraper_test.log")
write_to_file("")
write_to_file("可以查看日志: cat /tmp/scraper_test.log")
