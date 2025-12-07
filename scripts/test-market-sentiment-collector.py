#!/usr/bin/env python3
"""
测试市场情绪数据采集功能
"""

import sys
import os
from datetime import datetime

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
    """测试市场情绪采集器"""
    from app.services.collectors.market_sentiment_collector import MarketSentimentCollector

    print("=" * 60)
    print("🧪 市场情绪数据采集测试")
    print("=" * 60)
    print()

    collector = MarketSentimentCollector()

    # 测试: 采集今日市场情绪数据
    print("📋 采集今日市场情绪数据")
    print("-" * 60)

    trade_date = datetime.now().strftime("%Y-%m-%d")

    sentiment_data = collector.collect_market_sentiment(trade_date)

    print("\n市场情绪数据:")
    print(f"  交易日期: {sentiment_data['trade_date']}")
    print(f"  总成交额: {sentiment_data['total_amount']:,.0f} 元")
    print(f"  上涨家数: {sentiment_data['up_count']}")
    print(f"  下跌家数: {sentiment_data['down_count']}")
    print(f"  平盘家数: {sentiment_data['flat_count']}")
    print(f"  涨跌比: {sentiment_data['up_down_ratio']:.4f}")
    print(f"  涨停数: {sentiment_data['limit_up_count']}")
    print(f"  跌停数: {sentiment_data['limit_down_count']}")
    print(f"  连板分布: {sentiment_data['continuous_limit_distribution']}")
    print(f"  炸板数: {sentiment_data.get('exploded_count', 0)}")
    print(f"  炸板率: {sentiment_data['explosion_rate']:.2f}%")

    print()

    # 保存到数据库
    print("💾 保存到数据库...")
    success = collector.save_to_database(sentiment_data)

    if success:
        print("✅ 成功保存市场情绪数据")
    else:
        print("❌ 保存失败")

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
