"""
采集昨日涨停股今日表现数据

用法：
    python collect_yesterday_limit.py              # 采集最新交易日
    python collect_yesterday_limit.py 2025-12-11  # 采集指定日期
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from app.services.collectors.yesterday_limit_collector import collect_yesterday_limit_performance


def main():
    # 获取命令行参数
    trade_date = sys.argv[1] if len(sys.argv) > 1 else None

    print("=" * 60)
    print("📊 昨日涨停股今日表现采集")
    print("=" * 60)

    if trade_date:
        print(f"📅 指定日期: {trade_date}")
    else:
        print("📅 使用最新交易日")

    print()

    # 执行采集
    result = collect_yesterday_limit_performance(trade_date)

    print()
    print("=" * 60)

    if result.get("success"):
        print("✅ 采集成功!")
        print(f"   今日日期: {result.get('trade_date')}")
        print(f"   昨日日期: {result.get('yesterday')}")
        print(f"   总记录数: {result.get('total_count')}")
        print()

        stats = result.get("stats", {})
        if stats:
            print("📈 统计数据:")
            print(f"   昨日涨停数: {stats.get('total', 0)}")
            print(f"   获取行情数: {stats.get('with_quote', 0)}")
            print(f"   平均涨跌幅: {stats.get('avg_change_pct', 0)}%")
            print(f"   晋级数(今日涨停): {stats.get('promotion_count', 0)} ({stats.get('promotion_rate', 0)}%)")
            print(f"   大面数(跌>5%): {stats.get('big_loss_count', 0)} ({stats.get('big_loss_rate', 0)}%)")
            print(f"   高位(3板+)数: {stats.get('high_board_count', 0)}")
            print(f"   高位大面数: {stats.get('high_board_big_loss', 0)} ({stats.get('high_board_big_loss_rate', 0)}%)")
    else:
        print(f"❌ 采集失败: {result.get('error')}")

    print("=" * 60)


if __name__ == "__main__":
    main()
