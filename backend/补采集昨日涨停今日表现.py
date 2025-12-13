"""
手动补采集2025-12-11涨停股票在12月12日的表现
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from loguru import logger
from app.services.collectors.limit_stocks_collector import LimitStocksCollector
from app.utils.supabase_client import get_supabase

def main():
    collector = LimitStocksCollector()
    supabase = get_supabase()

    trade_date = "2025-12-12"
    previous_date = "2025-12-11"

    logger.info(f"开始补采集 {previous_date} 涨停股票在 {trade_date} 的表现...")

    # 1. 查询前一交易日涨停的股票
    yesterday_stocks = collector._get_previous_day_limit_up_stocks(previous_date)
    logger.info(f"✅ {previous_date} 涨停股票: {len(yesterday_stocks)} 只")

    # 2. 查询今日已有数据的股票
    response_today = supabase.table("limit_stocks_detail")\
        .select("stock_code")\
        .eq("trade_date", trade_date)\
        .execute()

    existing_codes = set([r["stock_code"] for r in response_today.data])
    logger.info(f"✅ {trade_date} 已有数据: {len(existing_codes)} 只")

    # 3. 找出缺失的股票
    all_codes = set([s["stock_code"] for s in yesterday_stocks])
    missing_codes = all_codes - existing_codes

    logger.info(f"⚠️  缺失数据: {len(missing_codes)} 只")
    logger.info(f"   缺失股票: {list(missing_codes)}")

    if not missing_codes:
        logger.info("✅ 所有股票数据已完整，无需补采集")
        return

    # 4. 补采集缺失的股票
    missing_stocks = [s for s in yesterday_stocks if s["stock_code"] in missing_codes]
    stock_codes = [s["stock_code"] for s in missing_stocks]
    stock_name_map = {s["stock_code"]: s["stock_name"] for s in missing_stocks}

    logger.info(f"\n开始采集这 {len(stock_codes)} 只股票的日线数据...")
    daily_df = collector._collect_stocks_daily_data(stock_codes, trade_date)

    if daily_df.empty:
        logger.error("❌ 未获取到日线数据")
        return

    logger.info(f"✅ 成功获取 {len(daily_df)} 只股票的日线数据")

    # 5. 处理并保存数据
    performance_records = collector._process_daily_data(daily_df, trade_date, stock_name_map)

    if performance_records:
        saved_count = collector.save_to_database(performance_records)
        logger.info(f"\n🎉 成功保存 {saved_count} 条记录")

        # 显示部分结果
        logger.info("\n采集结果示例:")
        for r in performance_records[:10]:
            logger.info(
                f"  {r['stock_code']} {r['stock_name']}: "
                f"{r['change_pct']:.2f}% (limit_type={r['limit_type']})"
            )
    else:
        logger.warning("⚠️  没有有效记录")

if __name__ == "__main__":
    main()
