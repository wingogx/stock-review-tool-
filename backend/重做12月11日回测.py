"""
清理并重新做12月11日的涨停股票评分回测
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

import asyncio
from loguru import logger
from app.services.backtest_service import BacktestService
from app.utils.supabase_client import get_supabase

async def main():
    """清理并重新做回测"""

    service = BacktestService()
    supabase = get_supabase()

    test_date = "2025-12-11"
    next_date = "2025-12-12"

    # 1. 查询现有回测数据
    logger.info(f"查询 {test_date} 现有回测数据...")
    response = supabase.table("premium_score_backtest")\
        .select("id, stock_code, stock_name, total_score")\
        .eq("trade_date", test_date)\
        .execute()

    existing_records = response.data
    logger.info(f"找到 {len(existing_records)} 条现有回测记录")

    if existing_records:
        logger.info("示例记录:")
        for r in existing_records[:5]:
            logger.info(f"  ID:{r['id']} {r['stock_code']} {r['stock_name']} 评分:{r['total_score']}")

    # 2. 删除现有回测数据
    if existing_records:
        logger.info(f"\n开始删除 {len(existing_records)} 条回测记录...")
        record_ids = [r["id"] for r in existing_records]

        deleted_count = service.delete_backtest_records(record_ids)
        logger.info(f"✅ 成功删除 {deleted_count} 条记录")
    else:
        logger.info("没有需要删除的记录")

    # 3. 验证数据库中12月12日的数据完整性
    logger.info(f"\n验证 {next_date} 数据完整性...")

    # 查询12月11日涨停股票
    response_1211 = supabase.table("limit_stocks_detail")\
        .select("stock_code")\
        .eq("trade_date", test_date)\
        .eq("limit_type", "limit_up")\
        .execute()

    codes_1211 = set([r["stock_code"] for r in response_1211.data])
    logger.info(f"  {test_date} 涨停股票: {len(codes_1211)} 只")

    # 查询12月12日所有数据
    response_1212 = supabase.table("limit_stocks_detail")\
        .select("stock_code")\
        .eq("trade_date", next_date)\
        .execute()

    codes_1212 = set([r["stock_code"] for r in response_1212.data])
    logger.info(f"  {next_date} 所有数据: {len(codes_1212)} 只")

    # 检查缺失数据
    missing = codes_1211 - codes_1212
    if missing:
        logger.warning(f"  ⚠️  缺失 {len(missing)} 只股票数据: {list(missing)[:5]}")
    else:
        logger.info(f"  ✅ 数据完整，无缺失")

    # 4. 重新做回测
    logger.info(f"\n{'='*80}")
    logger.info(f"开始重新做 {test_date} 回测...")
    logger.info(f"{'='*80}\n")

    result = await service.batch_save_backtest(
        trade_date=test_date,
        next_trade_date=next_date,
        limit=50  # 限制50只股票，避免太慢
    )

    logger.info(f"\n{'='*80}")
    logger.info("回测完成!")
    logger.info(f"  总数: {result['total']}")
    logger.info(f"  成功: {result['success']}")
    logger.info(f"  失败: {result['fail']}")
    logger.info(f"{'='*80}")

    # 5. 查看回测统计
    logger.info(f"\n获取回测统计数据...")
    stats = service.get_backtest_statistics(test_date)

    if stats.get("total", 0) > 0:
        logger.info(f"\n回测统计:")
        logger.info(f"  总记录数: {stats['total']}")

        overall = stats.get("overall", {})
        logger.info(f"\n整体表现:")
        logger.info(f"  平均次日涨跌幅: {overall.get('avg_next_day_pct', 0):.2f}%")
        logger.info(f"  次日涨停数: {overall.get('limit_up_count', 0)}")
        logger.info(f"  次日涨停率: {overall.get('limit_up_rate', 0):.2f}%")
        logger.info(f"  盈利数: {overall.get('profitable_count', 0)}")
        logger.info(f"  盈利率: {overall.get('profitable_rate', 0):.2f}%")
        logger.info(f"  预测准确率: {overall.get('prediction_accuracy', 0):.2f}%")

        by_level = stats.get("by_level", {})
        if by_level:
            logger.info(f"\n按溢价等级统计:")
            for level in ["极高溢价", "高溢价", "中等溢价", "低溢价", "极低溢价"]:
                if level in by_level:
                    level_stats = by_level[level]
                    logger.info(f"\n  {level} ({level_stats['count']}只):")
                    logger.info(f"    平均次日涨跌: {level_stats['avg_next_day_pct']:.2f}%")
                    logger.info(f"    次日涨停率: {level_stats['limit_up_rate']:.2f}%")
                    logger.info(f"    盈利率: {level_stats['profitable_rate']:.2f}%")
                    logger.info(f"    预测准确率: {level_stats['prediction_accuracy']:.2f}%")

if __name__ == "__main__":
    asyncio.run(main())
