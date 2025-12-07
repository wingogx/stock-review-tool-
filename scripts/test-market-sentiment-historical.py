#!/usr/bin/env python3
"""
测试修复后的市场情绪采集器 - 使用历史日期
"""
import sys, os
backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, backend_dir)

from dotenv import load_dotenv
load_dotenv()

from app.services.collectors.market_sentiment_collector import MarketSentimentCollector
from loguru import logger

logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}")

print("=" * 60)
print("🧪 测试市场情绪采集器（历史日期 2025-12-05）")
print("=" * 60)

collector = MarketSentimentCollector()
sentiment_data = collector.collect_market_sentiment(trade_date="2025-12-05")

print("\n" + "=" * 60)
print("📊 采集到的数据:")
print("=" * 60)
print(f"  交易日期: {sentiment_data['trade_date']}")
print(f"  总成交额: {sentiment_data['total_amount'] / 1e8:.2f} 亿元")
print(f"  上涨家数: {sentiment_data['up_count']}")
print(f"  下跌家数: {sentiment_data['down_count']}")
print(f"  平盘家数: {sentiment_data['flat_count']}")
print(f"  涨跌比: {sentiment_data['up_down_ratio']:.4f}")
print(f"  涨停数: {sentiment_data['limit_up_count']}")
print(f"  跌停数: {sentiment_data['limit_down_count']}")
print(f"  连板分布: {sentiment_data['continuous_limit_distribution']}")
print(f"  炸板数: {sentiment_data['exploded_count']}")
print(f"  炸板率: {sentiment_data['explosion_rate']:.2f}%")

print("\n" + "=" * 60)
print("💾 保存到数据库...")
success = collector.save_to_database(sentiment_data)
if success:
    print("✅ 成功保存市场情绪数据！")
else:
    print("❌ 保存失败！")

print("=" * 60)
