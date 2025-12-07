"""
数据采集定时任务调度器
使用 APScheduler 每日自动采集股票数据

运行方式:
python3 -m app.scheduler.data_scheduler
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from loguru import logger
import sys
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
logger.add(
    "logs/scheduler_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    level="DEBUG"
)

from app.services.collectors.market_index_collector import MarketIndexCollector
from app.services.collectors.limit_stocks_collector import LimitStocksCollector
from app.services.collectors.market_sentiment_collector import MarketSentimentCollector
from app.services.collectors.hot_concepts_collector import HotConceptsCollector


def collect_market_index():
    """采集大盘指数数据"""
    try:
        logger.info("=" * 60)
        logger.info("开始采集大盘指数数据...")

        collector = MarketIndexCollector()
        results = collector.collect_incremental()

        total = sum(results.values())
        logger.info(f"大盘指数采集完成: 共 {total} 条新数据")
        for symbol, count in results.items():
            logger.info(f"  {symbol}: {count} 条")

        return True
    except Exception as e:
        logger.error(f"大盘指数采集失败: {str(e)}")
        return False


def collect_limit_stocks():
    """采集涨跌停股池数据"""
    try:
        logger.info("=" * 60)
        logger.info("开始采集涨跌停股池数据...")

        collector = LimitStocksCollector()
        results = collector.collect_and_save()

        logger.info(f"涨跌停股池采集完成: 涨停{results['limit_up']}只, 跌停{results['limit_down']}只")

        return True
    except Exception as e:
        logger.error(f"涨跌停股池采集失败: {str(e)}")
        return False


def collect_market_sentiment():
    """采集市场情绪数据"""
    try:
        logger.info("=" * 60)
        logger.info("开始采集市场情绪数据...")

        collector = MarketSentimentCollector()
        success = collector.collect_and_save()

        if success:
            logger.info("市场情绪数据采集完成")
        else:
            logger.warning("市场情绪数据采集失败")

        return success
    except Exception as e:
        logger.error(f"市场情绪数据采集失败: {str(e)}")
        return False


def collect_hot_concepts():
    """采集热门概念板块数据"""
    try:
        logger.info("=" * 60)
        logger.info("开始采集热门概念板块数据...")

        collector = HotConceptsCollector()
        count = collector.collect_and_save(top_n=50)

        logger.info(f"热门概念板块采集完成: 共 {count} 个概念")

        return True
    except Exception as e:
        logger.error(f"热门概念板块采集失败: {str(e)}")
        return False


def run_daily_collection():
    """每日数据采集主任务"""
    logger.info("\n" + "=" * 80)
    logger.info(f"🚀 开始执行每日数据采集任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)

    results = {
        "market_index": False,
        "limit_stocks": False,
        "market_sentiment": False,
        "hot_concepts": False,
    }

    # 1. 采集大盘指数
    results["market_index"] = collect_market_index()

    # 2. 采集涨跌停股池
    results["limit_stocks"] = collect_limit_stocks()

    # 3. 采集市场情绪
    results["market_sentiment"] = collect_market_sentiment()

    # 4. 采集热门概念
    results["hot_concepts"] = collect_hot_concepts()

    # 汇总结果
    logger.info("\n" + "=" * 80)
    logger.info("📊 每日数据采集任务完成")
    logger.info("=" * 80)

    success_count = sum(results.values())
    total_count = len(results)

    logger.info(f"成功: {success_count}/{total_count}")
    for task, success in results.items():
        status = "✅" if success else "❌"
        logger.info(f"  {status} {task}")

    logger.info("=" * 80 + "\n")

    return success_count == total_count


def main():
    """主函数 - 启动定时任务调度器"""
    logger.info("=" * 80)
    logger.info("📅 数据采集定时任务调度器启动")
    logger.info("=" * 80)
    logger.info("调度规则:")
    logger.info("  - 每个交易日 16:00 执行数据采集")
    logger.info("  - 交易日: 周一至周五")
    logger.info("=" * 80)

    scheduler = BlockingScheduler()

    # 添加定时任务: 每个交易日16:00执行
    scheduler.add_job(
        run_daily_collection,
        trigger=CronTrigger(
            day_of_week='mon-fri',  # 周一到周五
            hour=16,                 # 16点
            minute=0                 # 0分
        ),
        id='daily_collection',
        name='每日数据采集',
        replace_existing=True
    )

    logger.info("✅ 定时任务已添加")
    logger.info("下次执行时间: " + str(scheduler.get_job('daily_collection').next_run_time))
    logger.info("\n⏰ 调度器正在运行中... (Ctrl+C 退出)\n")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("\n👋 调度器已停止")


if __name__ == "__main__":
    # 可以通过命令行参数立即运行一次
    if len(sys.argv) > 1 and sys.argv[1] == "--now":
        logger.info("立即执行一次数据采集...")
        run_daily_collection()
    else:
        main()
