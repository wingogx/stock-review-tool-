"""
手动指定日期采集数据的脚本
用法: python3 collect_date.py 2025-12-09
"""

import sys
from datetime import datetime
from loguru import logger
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)

from app.services.collectors.market_index_collector import MarketIndexCollector
from app.services.collectors.limit_stocks_collector import LimitStocksCollector
from app.services.collectors.market_sentiment_collector import MarketSentimentCollector
from app.services.collectors.hot_concepts_collector import HotConceptsCollector


def collect_all_data(trade_date: str):
    """
    采集指定日期的所有数据

    Args:
        trade_date: 交易日期 YYYY-MM-DD
    """
    logger.info("=" * 80)
    logger.info(f"🚀 开始采集 {trade_date} 的所有数据")
    logger.info("=" * 80)

    results = {
        "market_index": False,
        "limit_stocks": False,
        "market_sentiment": False,
        "hot_concepts": False,
    }

    # 1. 采集大盘指数
    try:
        logger.info("\n" + "=" * 60)
        logger.info("📈 采集大盘指数数据...")
        collector = MarketIndexCollector()

        # 采集所有指数（使用正确的方法）
        index_results = collector.collect_all_indexes(start_date=trade_date, end_date=trade_date)

        # 显示结果
        for symbol, count in index_results.items():
            logger.info(f"  {symbol}: {count} 条")

        total = sum(index_results.values())
        logger.info(f"✅ 大盘指数采集完成: 共 {total} 条")
        results["market_index"] = True
    except Exception as e:
        logger.error(f"❌ 大盘指数采集失败: {str(e)}")

    # 2. 采集涨跌停股池
    try:
        logger.info("\n" + "=" * 60)
        logger.info("📊 采集涨跌停股池数据...")
        collector = LimitStocksCollector()
        limit_results = collector.collect_and_save(trade_date=trade_date)
        logger.info(f"✅ 涨跌停股池采集完成: 涨停{limit_results['limit_up']}只, 跌停{limit_results['limit_down']}只")
        results["limit_stocks"] = True
    except Exception as e:
        logger.error(f"❌ 涨跌停股池采集失败: {str(e)}")

    # 3. 采集市场情绪
    try:
        logger.info("\n" + "=" * 60)
        logger.info("😊 采集市场情绪数据...")
        collector = MarketSentimentCollector()
        success = collector.collect_and_save(trade_date=trade_date)
        if success:
            logger.info("✅ 市场情绪数据采集完成")
            results["market_sentiment"] = True
        else:
            logger.warning("⚠️ 市场情绪数据采集失败")
    except Exception as e:
        logger.error(f"❌ 市场情绪数据采集失败: {str(e)}")

    # 4. 采集热门概念
    try:
        logger.info("\n" + "=" * 60)
        logger.info("🔥 采集热门概念板块数据...")
        collector = HotConceptsCollector()
        count = collector.collect_and_save(trade_date=trade_date, top_n=10)  # Top 10，按5日涨幅排序
        logger.info(f"✅ 热门概念采集完成: 保存了 {count} 个概念")
        results["hot_concepts"] = True
    except Exception as e:
        logger.error(f"❌ 热门概念采集失败: {str(e)}")

    # 总结
    logger.info("\n" + "=" * 80)
    logger.info("📋 数据采集总结")
    logger.info("=" * 80)
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    for module, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        logger.info(f"  {module}: {status}")

    logger.info(f"\n总计: {success_count}/{total_count} 个模块采集成功")
    logger.info("=" * 80)

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 collect_date.py YYYY-MM-DD")
        print("示例: python3 collect_date.py 2025-12-09")
        sys.exit(1)

    trade_date = sys.argv[1]

    # 验证日期格式
    try:
        datetime.strptime(trade_date, "%Y-%m-%d")
    except ValueError:
        print(f"错误: 日期格式不正确，应为 YYYY-MM-DD")
        sys.exit(1)

    collect_all_data(trade_date)
