#!/usr/bin/env python3
"""
测试大盘指数数据采集功能
"""

import sys
import os
from datetime import datetime, timedelta

# 添加后端目录到 Python 路径
backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, backend_dir)

from dotenv import load_dotenv
from loguru import logger

# 加载环境变量
load_dotenv()

# 配置日志
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")


def test_collector():
    """测试采集器"""
    from app.services.collectors.market_index_collector import MarketIndexCollector

    print("=" * 60)
    print("🧪 大盘指数数据采集测试")
    print("=" * 60)
    print()

    collector = MarketIndexCollector()

    # 测试 1: 采集单个指数最近 5 天数据
    print("📋 Test 1: 采集上证指数最近 5 天数据")
    print("-" * 60)

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")

    df = collector.collect_index_daily("sh000001", start_date, end_date)

    if not df.empty:
        print(f"✅ 成功采集 {len(df)} 条数据")
        print("\n数据预览:")
        print(df.head())
        print()

        # 保存到数据库
        print("💾 保存到数据库...")
        count = collector.save_to_database("sh000001", df)
        print(f"✅ 成功保存 {count} 条数据")
    else:
        print("❌ 采集失败，没有数据")

    print()

    # 测试 2: 增量采集所有指数
    print("📋 Test 2: 增量采集所有指数")
    print("-" * 60)

    results = collector.collect_incremental()

    print("\n增量采集结果:")
    for symbol, count in results.items():
        index_name = collector.index_mapping[symbol]["name"]
        print(f"  {index_name} ({symbol}): {count} 条新数据")

    print()

    # 测试 3: 查询数据库中的最新数据
    print("📋 Test 3: 查询数据库最新数据")
    print("-" * 60)

    for symbol, info in collector.index_mapping.items():
        latest_date = collector.get_latest_trade_date(info["code"])
        print(f"  {info['name']}: {latest_date or '暂无数据'}")

    print()
    print("=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_collector()
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
