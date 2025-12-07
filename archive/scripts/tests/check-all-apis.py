#!/usr/bin/env python3
"""
检查所有数据采集API的状态和数据格式
"""
import sys, os
backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, backend_dir)

from dotenv import load_dotenv
load_dotenv()

from loguru import logger
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}")

print("=" * 80)
print("🔍 检查所有数据采集API的状态")
print("=" * 80)

# 1. 大盘指数采集器
print("\n📊 1. 大盘指数采集器 (MarketIndexCollector)")
print("-" * 80)
try:
    from app.services.collectors.market_index_collector import MarketIndexCollector
    collector = MarketIndexCollector()

    print("✅ 采集器初始化成功")
    print(f"   支持的指数: {list(collector.index_mapping.keys())}")

    # 测试采集
    df = collector.collect_index_daily("sh000001", "2025-12-05", "2025-12-05")
    if not df.empty:
        print(f"✅ 数据采集成功: {len(df)} 条记录")
        print(f"   数据字段: {df.columns.tolist()}")
        print(f"   示例数据: 上证指数 收盘={df.iloc[0]['close_price']:.2f}, 涨跌幅={df.iloc[0]['change_pct']:.2f}%")
    else:
        print("⚠️  数据为空")
except Exception as e:
    print(f"❌ 失败: {e}")

# 2. 涨跌停股池采集器
print("\n📊 2. 涨跌停股池采集器 (LimitStocksCollector)")
print("-" * 80)
try:
    from app.services.collectors.limit_stocks_collector import LimitStocksCollector
    collector = LimitStocksCollector()

    print("✅ 采集器初始化成功")

    # 测试采集涨停池
    df = collector.collect_limit_up_stocks("20251205")
    if not df.empty:
        print(f"✅ 涨停池数据采集成功: {len(df)} 只股票")
        print(f"   数据字段: {df.columns.tolist()}")
    else:
        print("⚠️  涨停池数据为空")

    # 测试采集跌停池
    df = collector.collect_limit_down_stocks("20251205")
    if not df.empty:
        print(f"✅ 跌停池数据采集成功: {len(df)} 只股票")
    else:
        print("⚠️  跌停池数据为空")

except Exception as e:
    print(f"❌ 失败: {e}")

# 3. 市场情绪采集器
print("\n📊 3. 市场情绪采集器 (MarketSentimentCollector)")
print("-" * 80)
try:
    from app.services.collectors.market_sentiment_collector import MarketSentimentCollector
    collector = MarketSentimentCollector()

    print("✅ 采集器初始化成功")

    # 测试市场异动数据
    market_activity = collector.collect_market_activity_data()
    if market_activity:
        print(f"✅ 市场异动数据采集成功")
        print(f"   上涨: {market_activity.get('上涨', 0)}, 下跌: {market_activity.get('下跌', 0)}, 平盘: {market_activity.get('平盘', 0)}")
    else:
        print("⚠️  市场异动数据为空")

    # 测试两市总成交额
    total_amount = collector.collect_total_amount("20251205")
    if total_amount > 0:
        print(f"✅ 两市总成交额采集成功: {total_amount/1e8:.2f} 亿元")
    else:
        print("⚠️  总成交额为0")

except Exception as e:
    print(f"❌ 失败: {e}")

# 4. 热门概念采集器
print("\n📊 4. 热门概念采集器 (HotConceptsCollector)")
print("-" * 80)
try:
    from app.services.collectors.hot_concepts_collector import HotConceptsCollector
    collector = HotConceptsCollector()

    print("✅ 采集器初始化成功")

    # 测试获取概念列表
    df = collector.get_all_concepts()
    if not df.empty:
        print(f"✅ 概念列表采集成功: {len(df)} 个概念")
    else:
        print("⚠️  概念列表为空")

    # 测试涨停池数据
    df = collector.get_limit_up_stocks("20251205")
    if not df.empty:
        print(f"✅ 涨停股池数据采集成功: {len(df)} 只股票")

        # 测试龙头股提取
        leading = collector.extract_leading_stocks_from_limit_up("人工智能", df, limit=3)
        if leading:
            print(f"✅ 龙头股提取功能正常: 示例概念'人工智能'提取到 {len(leading)} 只龙头股")
        else:
            print("⚠️  未找到该概念的龙头股（可能该概念当天无涨停股）")
    else:
        print("⚠️  涨停股池为空")

except Exception as e:
    print(f"❌ 失败: {e}")

print("\n" + "=" * 80)
print("✅ API状态检查完成")
print("=" * 80)
