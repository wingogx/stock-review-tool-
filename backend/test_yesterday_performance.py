"""
简单测试：只测试采集前一交易日涨停股票的今日表现
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from loguru import logger
from app.services.collectors.limit_stocks_collector import LimitStocksCollector
from app.utils.trading_date import get_previous_trading_date

def test_yesterday_performance():
    """测试采集前一交易日涨停股票今日表现"""

    collector = LimitStocksCollector()

    # 测试日期
    trade_date = "2025-12-12"

    # 1. 获取前一交易日
    logger.info(f"获取 {trade_date} 的前一交易日...")
    previous_date = get_previous_trading_date(trade_date)

    if not previous_date:
        logger.error("❌ 无法获取前一交易日")
        return

    logger.info(f"✅ 前一交易日: {previous_date}")

    # 2. 查询前一交易日涨停的股票
    logger.info(f"\n查询 {previous_date} 涨停股票...")
    yesterday_stocks = collector._get_previous_day_limit_up_stocks(previous_date)

    if not yesterday_stocks:
        logger.error(f"❌ {previous_date} 无涨停数据")
        return

    logger.info(f"✅ 找到 {len(yesterday_stocks)} 只涨停股票")
    logger.info(f"   示例: {yesterday_stocks[:3]}")

    # 3. 只测试前5只股票（避免太慢）
    test_stocks = yesterday_stocks[:5]
    stock_codes = [s["stock_code"] for s in test_stocks]
    stock_name_map = {s["stock_code"]: s["stock_name"] for s in test_stocks}

    logger.info(f"\n开始获取这5只股票在 {trade_date} 的日线数据...")
    logger.info(f"   股票列表: {stock_codes}")

    # 4. 获取日线数据
    daily_df = collector._collect_stocks_daily_data(stock_codes, trade_date)

    if daily_df.empty:
        logger.error("❌ 未获取到日线数据")
        return

    logger.info(f"✅ 成功获取 {len(daily_df)} 只股票的日线数据")
    logger.info(f"   数据列: {daily_df.columns.tolist()}")

    # 5. 处理数据
    logger.info(f"\n开始处理数据...")
    performance_records = collector._process_daily_data(daily_df, trade_date, stock_name_map)

    logger.info(f"✅ 处理完成，共 {len(performance_records)} 条记录")

    # 6. 显示结果
    logger.info(f"\n采集结果示例:")
    for record in performance_records:
        logger.info(
            f"  {record['stock_code']} {record['stock_name']}: "
            f"{record['change_pct']:.2f}% (limit_type={record['limit_type']})"
        )

    logger.info("\n✅ 测试完成！新功能正常工作。")

if __name__ == "__main__":
    test_yesterday_performance()
