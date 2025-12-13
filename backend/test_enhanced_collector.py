"""
测试增强后的涨停采集器
验证是否能正确采集前一交易日涨停股票的今日表现
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()  # 加载环境变量

from loguru import logger
from app.services.collectors.limit_stocks_collector import LimitStocksCollector

def test_enhanced_collector():
    """测试增强后的采集器"""
    logger.info("=" * 80)
    logger.info("测试增强后的涨停采集器")
    logger.info("=" * 80)

    collector = LimitStocksCollector()

    # 采集12月12日的数据（包括12月11日涨停股票的今日表现）
    test_date = "2024-12-12"
    logger.info(f"\n开始采集 {test_date} 的数据...")

    results = collector.collect_and_save(test_date)

    logger.info("\n" + "=" * 80)
    logger.info("采集结果:")
    logger.info(f"  ✅ 当日涨停: {results['limit_up']} 只")
    logger.info(f"  ✅ 当日跌停: {results['limit_down']} 只")
    logger.info(f"  ✅ 昨日涨停今日表现: {results['yesterday_limit_performance']} 只")
    logger.info("=" * 80)

    # 验证数据
    from app.utils.supabase_client import get_supabase
    supabase = get_supabase()

    # 查询12月12日所有数据
    response = supabase.table("limit_stocks_detail")\
        .select("stock_code, stock_name, limit_type, change_pct")\
        .eq("trade_date", test_date)\
        .execute()

    all_records = response.data
    logger.info(f"\n数据库中 {test_date} 总记录数: {len(all_records)}")

    # 统计各类型记录
    limit_up_count = sum(1 for r in all_records if r['limit_type'] == 'limit_up')
    limit_down_count = sum(1 for r in all_records if r['limit_type'] == 'limit_down')
    normal_count = sum(1 for r in all_records if r['limit_type'] == 'normal')

    logger.info(f"  - 涨停: {limit_up_count} 只")
    logger.info(f"  - 跌停: {limit_down_count} 只")
    logger.info(f"  - 正常涨跌: {normal_count} 只 ⭐ (昨日涨停今日未涨停/跌停)")

    # 显示部分正常涨跌的股票（这些是昨日涨停今日没涨停的）
    normal_records = [r for r in all_records if r['limit_type'] == 'normal']
    if normal_records:
        logger.info(f"\n昨日涨停今日表现示例（前5只）:")
        for r in normal_records[:5]:
            logger.info(f"  {r['stock_code']} {r['stock_name']}: {r['change_pct']:.2f}%")

if __name__ == "__main__":
    test_enhanced_collector()
