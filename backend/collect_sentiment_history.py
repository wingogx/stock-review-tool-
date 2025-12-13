"""
采集市场情绪历史数据
使用2025年交易日日历,避免采集节假日数据
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

from backend.app.services.collectors.market_sentiment_collector import MarketSentimentCollector
from backend.trading_calendar_2025 import get_calendar

if __name__ == "__main__":
    collector = MarketSentimentCollector()
    calendar = get_calendar()

    # 使用交易日日历获取最近60个交易日
    latest_trading_day = calendar.get_latest_trading_day("2025-12-11")
    all_trading_days = sorted(calendar.get_trading_days())
    latest_idx = all_trading_days.index(latest_trading_day)

    # 往前数60个交易日
    start_idx = max(0, latest_idx - 59)  # 包含当天共60天
    target_days = all_trading_days[start_idx:latest_idx + 1]

    print(f"开始采集市场情绪历史数据...")
    print(f"日期范围: {target_days[0]} ~ {target_days[-1]}")
    print(f"交易日数: {len(target_days)}天\n")

    success_count = 0
    skip_count = 0

    for date_str in target_days:
        try:
            print(f"采集 {date_str}...", end=" ")
            result = collector.collect_and_save(date_str)
            if result:
                print("✅")
                success_count += 1
            else:
                print("⚠️ 无数据")
                skip_count += 1
        except Exception as e:
            print(f"❌ 错误: {e}")
            skip_count += 1

    print(f"\n✅ 采集完成！")
    print(f"   成功: {success_count} 天")
    print(f"   跳过: {skip_count} 天")
