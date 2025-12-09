#!/usr/bin/env python3
"""
每日自动数据采集脚本 - 短线复盘项目
- 从系统获取当日日期和星期
- 采集当日所有股票数据（大盘指数、涨停股池、市场情绪、热门概念）
- 数据完整性检查
- 失败后1小时重试补全

定时任务配置：
0 16 * * 1-5 cd "/Users/win/Documents/ai 编程/cc/短线复盘/backend" && ./venv/bin/python3 scripts/daily_auto_collect.py >> "logs/daily_collect_$(date +\%Y\%m\%d).log" 2>&1
"""

import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from loguru import logger
from app.utils.supabase_client import get_supabase
from app.services.collectors.market_index_collector import MarketIndexCollector
from app.services.collectors.limit_stocks_collector import LimitStocksCollector
from app.services.collectors.market_sentiment_collector import MarketSentimentCollector
from app.services.collectors.hot_concepts_collector import HotConceptsCollector

# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:8}</level> | <level>{message}</level>",
    level="INFO"
)


def get_trading_date():
    """
    获取当前交易日期

    Returns:
        tuple: (日期字符串 YYYY-MM-DD, 星期几 0-6, 是否交易日)
    """
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    weekday = now.weekday()  # 0=周一, 6=周日

    # 周一到周五是交易日
    is_trading_day = weekday < 5

    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

    logger.info(f"📅 当前日期: {date_str} ({weekday_names[weekday]})")
    logger.info(f"📊 是否交易日: {'是' if is_trading_day else '否'}")

    return date_str, weekday, is_trading_day


def check_data_completeness(trade_date: str):
    """
    检查指定日期的数据完整性

    Args:
        trade_date: 交易日期 YYYY-MM-DD

    Returns:
        dict: 各模块数据状态 {module_name: (exists, count)}
    """
    logger.info("=" * 80)
    logger.info("🔍 检查数据完整性...")
    logger.info("=" * 80)

    supabase = get_supabase()
    results = {}

    try:
        # 1. 检查大盘指数（应该有3条：上证、深证、创业板）
        response = supabase.table("market_index").select("*", count="exact").eq("trade_date", trade_date).execute()
        count = response.count if response.count else 0
        results["market_index"] = (count >= 1, count)  # 至少要有1条（上证）
        logger.info(f"  大盘指数: {count} 条 {'✅' if count >= 1 else '❌ 不完整'}")

        # 2. 检查涨停股池
        response = supabase.table("limit_stocks_detail").select("*", count="exact").eq("trade_date", trade_date).execute()
        count = response.count if response.count else 0
        results["limit_stocks"] = (count > 0, count)
        logger.info(f"  涨停股池: {count} 条 {'✅' if count > 0 else '❌ 缺失'}")

        # 3. 检查市场情绪（应该只有1条）
        response = supabase.table("market_sentiment").select("*", count="exact").eq("trade_date", trade_date).execute()
        count = response.count if response.count else 0
        results["market_sentiment"] = (count == 1, count)
        logger.info(f"  市场情绪: {count} 条 {'✅' if count == 1 else '❌ 缺失'}")

        # 4. 检查热门概念（应该有50条）
        response = supabase.table("hot_concepts").select("*", count="exact").eq("trade_date", trade_date).execute()
        count = response.count if response.count else 0
        results["hot_concepts"] = (count >= 10, count)  # 至少10个概念
        logger.info(f"  热门概念: {count} 条 {'✅' if count >= 10 else '❌ 不完整'}")

    except Exception as e:
        logger.error(f"检查数据完整性失败: {str(e)}")
        return None

    # 统计
    complete_count = sum(1 for exists, _ in results.values() if exists)
    total_count = len(results)

    logger.info(f"\n完整性: {complete_count}/{total_count} 个模块")

    return results


def collect_all_data(trade_date: str):
    """
    采集所有数据

    Args:
        trade_date: 交易日期 YYYY-MM-DD

    Returns:
        dict: 采集结果 {module_name: success}
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
        logger.info("\n📈 [1/4] 采集大盘指数...")
        collector = MarketIndexCollector()
        index_results = collector.collect_all_indexes(start_date=trade_date, end_date=trade_date)
        total = sum(index_results.values())

        if total > 0:
            logger.info(f"✅ 大盘指数采集成功: 共 {total} 条")
            for symbol, count in index_results.items():
                logger.info(f"  {symbol}: {count} 条")
            results["market_index"] = True
        else:
            logger.warning("⚠️ 大盘指数采集失败: 无数据")
    except Exception as e:
        logger.error(f"❌ 大盘指数采集失败: {str(e)}")

    # 2. 采集涨跌停股池
    try:
        logger.info("\n📊 [2/4] 采集涨跌停股池...")
        collector = LimitStocksCollector()
        limit_results = collector.collect_and_save(trade_date=trade_date)

        if limit_results['limit_up'] > 0 or limit_results['limit_down'] > 0:
            logger.info(f"✅ 涨跌停股池采集成功: 涨停{limit_results['limit_up']}只, 跌停{limit_results['limit_down']}只")
            results["limit_stocks"] = True
        else:
            logger.warning("⚠️ 涨跌停股池采集失败: 无数据")
    except Exception as e:
        logger.error(f"❌ 涨跌停股池采集失败: {str(e)}")

    # 3. 采集市场情绪
    try:
        logger.info("\n😊 [3/4] 采集市场情绪...")
        collector = MarketSentimentCollector()
        success = collector.collect_and_save(trade_date=trade_date)

        if success:
            logger.info("✅ 市场情绪采集成功")
            results["market_sentiment"] = True
        else:
            logger.warning("⚠️ 市场情绪采集失败")
    except Exception as e:
        logger.error(f"❌ 市场情绪采集失败: {str(e)}")

    # 4. 采集热门概念
    try:
        logger.info("\n🔥 [4/4] 采集热门概念...")
        collector = HotConceptsCollector()
        count = collector.collect_and_save(trade_date=trade_date, top_n=50)

        if count > 0:
            logger.info(f"✅ 热门概念采集成功: {count} 个")
            results["hot_concepts"] = True
        else:
            logger.warning("⚠️ 热门概念采集失败: 无数据")
    except Exception as e:
        logger.error(f"❌ 热门概念采集失败: {str(e)}")

    # 统计
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    logger.info("\n" + "=" * 80)
    logger.info(f"📋 采集完成: {success_count}/{total_count} 个模块成功")
    logger.info("=" * 80)

    for module, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        logger.info(f"  {module}: {status}")

    return results


def collect_missing_data(trade_date: str, completeness_check: dict):
    """
    补全缺失的数据

    Args:
        trade_date: 交易日期 YYYY-MM-DD
        completeness_check: 数据完整性检查结果

    Returns:
        dict: 补全结果
    """
    logger.info("=" * 80)
    logger.info(f"🔧 补全 {trade_date} 缺失的数据")
    logger.info("=" * 80)

    results = {}

    # 只采集缺失的数据
    for module, (is_complete, count) in completeness_check.items():
        if is_complete:
            logger.info(f"  {module}: 已完整，跳过")
            results[module] = True
            continue

        logger.info(f"\n补全 {module}...")

        try:
            if module == "market_index":
                collector = MarketIndexCollector()
                index_results = collector.collect_all_indexes(start_date=trade_date, end_date=trade_date)
                total = sum(index_results.values())
                results[module] = total > 0
                logger.info(f"  {'✅ 补全成功' if results[module] else '❌ 补全失败'}: {total} 条")

            elif module == "limit_stocks":
                collector = LimitStocksCollector()
                limit_results = collector.collect_and_save(trade_date=trade_date)
                results[module] = limit_results['limit_up'] > 0 or limit_results['limit_down'] > 0
                logger.info(f"  {'✅ 补全成功' if results[module] else '❌ 补全失败'}: 涨停{limit_results['limit_up']}只, 跌停{limit_results['limit_down']}只")

            elif module == "market_sentiment":
                collector = MarketSentimentCollector()
                success = collector.collect_and_save(trade_date=trade_date)
                results[module] = success
                logger.info(f"  {'✅ 补全成功' if results[module] else '❌ 补全失败'}")

            elif module == "hot_concepts":
                collector = HotConceptsCollector()
                count = collector.collect_and_save(trade_date=trade_date, top_n=50)
                results[module] = count > 0
                logger.info(f"  {'✅ 补全成功' if results[module] else '❌ 补全失败'}: {count} 个")

        except Exception as e:
            logger.error(f"  ❌ 补全失败: {str(e)}")
            results[module] = False

    return results


def main():
    """主函数"""
    logger.info("\n" + "=" * 80)
    logger.info("🎯 每日自动数据采集任务启动")
    logger.info("=" * 80)
    logger.info(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)

    # 1. 获取当前日期
    trade_date, weekday, is_trading_day = get_trading_date()

    # 2. 判断是否交易日
    if not is_trading_day:
        logger.info("\n⏭️  今日非交易日，跳过采集")
        logger.info("=" * 80)
        return 0

    # 3. 首次采集
    logger.info("\n" + "=" * 80)
    logger.info("🔄 第1次采集")
    logger.info("=" * 80)

    collect_results = collect_all_data(trade_date)

    # 4. 检查数据完整性
    time.sleep(5)  # 等待数据库写入
    completeness = check_data_completeness(trade_date)

    if completeness is None:
        logger.error("\n❌ 数据完整性检查失败")
        return 1

    # 5. 判断是否所有数据都完整
    all_complete = all(is_complete for is_complete, _ in completeness.values())

    if all_complete:
        logger.info("\n" + "=" * 80)
        logger.info("✅ 所有数据采集完整，任务完成！")
        logger.info("=" * 80)
        return 0

    # 6. 数据不完整，1小时后重试
    logger.info("\n" + "=" * 80)
    logger.warning("⚠️  数据不完整，1小时后重试补全...")
    logger.info("=" * 80)

    retry_time = datetime.now() + timedelta(hours=1)
    logger.info(f"⏰ 重试时间: {retry_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 等待1小时
    logger.info("⏳ 等待中...")
    time.sleep(3600)  # 3600秒 = 1小时

    # 7. 重试补全
    logger.info("\n" + "=" * 80)
    logger.info("🔄 第2次采集（补全缺失数据）")
    logger.info("=" * 80)

    retry_results = collect_missing_data(trade_date, completeness)

    # 8. 再次检查完整性
    time.sleep(5)
    final_completeness = check_data_completeness(trade_date)

    if final_completeness is None:
        logger.error("\n❌ 最终数据完整性检查失败")
        return 1

    # 9. 最终结果
    all_complete_final = all(is_complete for is_complete, _ in final_completeness.values())

    logger.info("\n" + "=" * 80)
    if all_complete_final:
        logger.info("✅ 数据补全成功，所有数据已完整！")
    else:
        logger.warning("⚠️  部分数据仍然缺失，请检查日志")
        logger.info("\n缺失的模块:")
        for module, (is_complete, count) in final_completeness.items():
            if not is_complete:
                logger.warning(f"  - {module}: {count} 条")

    logger.info("=" * 80)
    logger.info(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)

    return 0 if all_complete_final else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
