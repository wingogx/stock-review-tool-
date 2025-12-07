"""
定时任务调度器
每个交易日下午 16:00 自动采集当日数据
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
from datetime import datetime
import sys
import os

# 添加data_collector模块路径
sys.path.append(os.path.dirname(__file__))

# 导入数据采集器
try:
    from data_collector import StockDataCollector
except ImportError:
    print("错误: 无法导入 data_collector 模块")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class StockDataScheduler:
    """股票数据采集调度器"""

    def __init__(self):
        self.scheduler = BlockingScheduler()
        self.collector = StockDataCollector()

    def daily_collection_job(self):
        """每日数据采集任务"""
        try:
            logger.info(f"{'='*60}")
            logger.info(f"开始执行每日数据采集任务")
            logger.info(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"{'='*60}")

            # 执行数据采集
            self.collector.collect_all_data()

            logger.info(f"{'='*60}")
            logger.info(f"每日数据采集任务执行完成")
            logger.info(f"{'='*60}\n")

        except Exception as e:
            logger.error(f"数据采集任务执行失败: {str(e)}", exc_info=True)

    def manual_collection(self):
        """手动执行采集（用于测试）"""
        logger.info("手动触发数据采集...")
        self.daily_collection_job()

    def start(self):
        """启动调度器"""
        # 添加定时任务：周一到周五下午16:00执行
        self.scheduler.add_job(
            self.daily_collection_job,
            trigger=CronTrigger(
                day_of_week='mon-fri',  # 周一到周五
                hour=16,                 # 16点
                minute=0,                # 0分
                timezone='Asia/Shanghai' # 使用上海时区
            ),
            id='daily_stock_collection',
            name='每日股票数据采集',
            replace_existing=True
        )

        logger.info("="*60)
        logger.info("📅 股票数据采集调度器已启动")
        logger.info("⏰ 执行时间: 每个交易日 16:00 (周一至周五)")
        logger.info("📊 采集内容:")
        logger.info("   - 大盘指数数据")
        logger.info("   - 涨跌停统计")
        logger.info("   - 龙虎榜数据")
        logger.info("   - 热门概念板块")
        logger.info("="*60)

        # 打印所有已注册的任务
        jobs = self.scheduler.get_jobs()
        logger.info(f"\n已注册的定时任务:")
        for job in jobs:
            logger.info(f"  - {job.name} (ID: {job.id})")
            logger.info(f"    下次执行: {job.next_run_time}")

        logger.info(f"\n等待定时任务触发...")
        logger.info(f"按 Ctrl+C 停止调度器\n")

        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("\n调度器已停止")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='股票数据采集调度器')
    parser.add_argument(
        '--manual',
        action='store_true',
        help='手动执行一次数据采集（不启动定时任务）'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='测试模式：每分钟执行一次（用于调试）'
    )

    args = parser.parse_args()

    scheduler_instance = StockDataScheduler()

    if args.manual:
        # 手动执行模式
        logger.info("="*60)
        logger.info("手动执行模式")
        logger.info("="*60)
        scheduler_instance.manual_collection()

    elif args.test:
        # 测试模式：每分钟执行一次
        logger.info("="*60)
        logger.info("⚠️  测试模式：每分钟执行一次")
        logger.info("="*60)

        scheduler_instance.scheduler.add_job(
            scheduler_instance.daily_collection_job,
            trigger=CronTrigger(
                minute='*',  # 每分钟
                timezone='Asia/Shanghai'
            ),
            id='test_collection',
            name='测试数据采集',
            replace_existing=True
        )

        try:
            scheduler_instance.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("\n测试模式已停止")

    else:
        # 正常调度模式
        scheduler_instance.start()


if __name__ == "__main__":
    main()
