"""
清理并重新采集指定日期的数据
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from loguru import logger
from app.utils.supabase_client import get_supabase

# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)


def clean_data_for_date(trade_date: str):
    """
    清理指定日期的所有数据

    Args:
        trade_date: 日期 YYYY-MM-DD
    """
    supabase = get_supabase()

    tables = [
        "market_index",
        "market_sentiment",
        "limit_stocks_detail",
        "hot_concepts",
        "yesterday_limit_performance",
    ]

    logger.info(f"=" * 60)
    logger.info(f"开始清理 {trade_date} 的数据...")
    logger.info(f"=" * 60)

    for table in tables:
        try:
            # 先查询数据量
            count_result = supabase.table(table).select("id", count="exact").eq("trade_date", trade_date).execute()
            count = count_result.count if hasattr(count_result, 'count') else len(count_result.data)

            if count > 0:
                # 删除数据
                supabase.table(table).delete().eq("trade_date", trade_date).execute()
                logger.info(f"✅ {table}: 删除 {count} 条记录")
            else:
                logger.info(f"⏭️  {table}: 无数据需要清理")

        except Exception as e:
            logger.warning(f"❌ {table}: 清理失败 - {str(e)}")

    logger.info(f"数据清理完成！")
    logger.info(f"=" * 60)


def collect_data_for_date(trade_date: str):
    """
    采集指定日期的所有数据

    Args:
        trade_date: 日期 YYYY-MM-DD
    """
    from app.services.collectors.market_index_collector import MarketIndexCollector
    from app.services.collectors.limit_stocks_collector import LimitStocksCollector
    from app.services.collectors.market_sentiment_collector import MarketSentimentCollector
    from app.services.collectors.hot_concepts_collector import HotConceptsCollector
    from app.services.collectors.yesterday_limit_collector import YesterdayLimitCollector

    logger.info(f"\n" + "=" * 60)
    logger.info(f"开始采集 {trade_date} 的数据...")
    logger.info(f"=" * 60)

    results = {}

    # 1. 采集大盘指数（需要更多历史数据来计算走势分析）
    try:
        logger.info(f"\n📊 [1/5] 采集大盘指数数据...")
        collector = MarketIndexCollector()

        # 为了正确计算MA均线和5日涨幅，需要获取更多历史数据
        # 往前推30天以确保有足够数据计算MA20和change_5d
        from datetime import datetime, timedelta
        date_obj = datetime.strptime(trade_date, "%Y-%m-%d")
        start_date_for_fetch = (date_obj - timedelta(days=30)).strftime("%Y-%m-%d")

        logger.info(f"   获取 {start_date_for_fetch} 至 {trade_date} 的数据用于计算走势分析...")
        result = collector.collect_all_indexes(start_date=start_date_for_fetch, end_date=trade_date)
        total = sum(result.values())
        results["market_index"] = total
        logger.info(f"✅ 大盘指数: 共 {total} 条记录（含历史数据用于走势计算）")
    except Exception as e:
        logger.error(f"❌ 大盘指数采集失败: {str(e)}")
        results["market_index"] = 0

    # 2. 采集涨跌停股池
    try:
        logger.info(f"\n📊 [2/5] 采集涨跌停股池数据...")
        collector = LimitStocksCollector()
        result = collector.collect_and_save(trade_date)
        results["limit_stocks"] = result["limit_up"] + result["limit_down"]
        logger.info(f"✅ 涨跌停股池: 涨停{result['limit_up']}只, 跌停{result['limit_down']}只")
    except Exception as e:
        logger.error(f"❌ 涨跌停股池采集失败: {str(e)}")
        results["limit_stocks"] = 0

    # 3. 采集市场情绪
    try:
        logger.info(f"\n📊 [3/5] 采集市场情绪数据...")
        collector = MarketSentimentCollector()
        success = collector.collect_and_save(trade_date)
        results["market_sentiment"] = 1 if success else 0
        logger.info(f"✅ 市场情绪: {'成功' if success else '失败'}")
    except Exception as e:
        logger.error(f"❌ 市场情绪采集失败: {str(e)}")
        results["market_sentiment"] = 0

    # 4. 采集热门概念
    try:
        logger.info(f"\n📊 [4/5] 采集热门概念板块数据...")
        collector = HotConceptsCollector()
        count = collector.collect_and_save(trade_date, top_n=10)
        results["hot_concepts"] = count
        logger.info(f"✅ 热门概念: 共 {count} 个概念")
    except Exception as e:
        logger.error(f"❌ 热门概念采集失败: {str(e)}")
        results["hot_concepts"] = 0

    # 5. 采集昨日涨停表现
    try:
        logger.info(f"\n📊 [5/5] 采集昨日涨停表现数据...")
        collector = YesterdayLimitCollector()
        result = collector.collect(trade_date)
        results["yesterday_limit"] = result.get("total_count", 0) if result.get("success") else 0
        logger.info(f"✅ 昨日涨停表现: 共 {results['yesterday_limit']} 条记录")
    except Exception as e:
        logger.error(f"❌ 昨日涨停表现采集失败: {str(e)}")
        results["yesterday_limit"] = 0

    # 汇总
    logger.info(f"\n" + "=" * 60)
    logger.info(f"📊 数据采集完成 - {trade_date}")
    logger.info(f"=" * 60)
    for task, count in results.items():
        status = "✅" if count > 0 else "❌"
        logger.info(f"  {status} {task}: {count}")
    logger.info(f"=" * 60)

    return results


def main():
    """主函数"""
    # 指定要清理和重采集的日期
    trade_date = "2025-12-12"

    logger.info(f"\n{'#' * 60}")
    logger.info(f"# 清理并重新采集 {trade_date} 的数据")
    logger.info(f"{'#' * 60}\n")

    # 步骤1: 清理数据
    clean_data_for_date(trade_date)

    # 步骤2: 重新采集数据
    collect_data_for_date(trade_date)

    logger.info(f"\n🎉 全部操作完成！")


if __name__ == "__main__":
    main()
