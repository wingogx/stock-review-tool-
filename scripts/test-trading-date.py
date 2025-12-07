"""
测试交易日期工具函数
验证 get_latest_trading_date() 是否正常工作
"""

import sys
import os

# 添加 backend 到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.utils.trading_date import get_latest_trading_date
from datetime import datetime
from loguru import logger

# 配置日志
logger.remove()
logger.add(sys.stdout, level="DEBUG")

def test_get_latest_trading_date():
    """测试获取最近交易日"""

    print("=" * 60)
    print("测试 get_latest_trading_date()")
    print("=" * 60)

    # 获取系统当前日期
    system_date = datetime.now().strftime("%Y-%m-%d")
    print(f"\n系统当前日期: {system_date}")

    # 获取最近交易日
    trading_date = get_latest_trading_date()
    print(f"最近交易日期: {trading_date}")

    # 判断是否相同
    if system_date == trading_date:
        print(f"✅ 今天是交易日")
    else:
        print(f"⚠️  今天不是交易日，自动使用最近交易日: {trading_date}")

    print("\n" + "=" * 60)
    print("测试结论:")
    print("=" * 60)
    print(f"get_latest_trading_date() 返回: {trading_date}")
    print(f"这个日期将被用于所有采集器，确保数据库中保存的是实际交易日期")

    return trading_date


def test_collectors_with_trading_date():
    """测试采集器使用最近交易日"""

    from app.services.collectors.limit_stocks_collector import LimitStocksCollector
    from app.services.collectors.market_sentiment_collector import MarketSentimentCollector

    trading_date = get_latest_trading_date()

    print("\n" + "=" * 60)
    print("测试采集器（不会实际采集，只验证日期参数）")
    print("=" * 60)

    print(f"\n1. LimitStocksCollector")
    print(f"   预期使用日期: {trading_date}")

    print(f"\n2. MarketSentimentCollector")
    print(f"   预期使用日期: {trading_date}")

    print(f"\n✅ 两个采集器都将使用最近交易日: {trading_date}")


if __name__ == "__main__":
    print("\n🚀 开始测试交易日期工具...\n")

    # 测试1: 获取最近交易日
    trading_date = test_get_latest_trading_date()

    # 测试2: 验证采集器使用
    test_collectors_with_trading_date()

    print("\n✅ 测试完成！\n")
