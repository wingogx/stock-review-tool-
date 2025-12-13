"""
清理并重新采集大盘指数数据
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

from backend.app.utils.supabase_client import get_supabase
from backend.app.services.collectors.market_index_collector import MarketIndexCollector
from backend.trading_calendar_2025 import get_calendar

def clear_market_index_data():
    """清理 market_index 表中的所有数据"""
    print("🗑️  正在清理 market_index 表数据...")

    supabase = get_supabase()

    # 删除所有数据
    response = supabase.table("market_index").delete().neq("id", 0).execute()

    print(f"✅ 已清理 market_index 表数据")
    return True

def collect_index_data():
    """重新采集大盘指数数据"""
    collector = MarketIndexCollector()
    calendar = get_calendar()

    # 使用交易日日历获取最近80个交易日(确保60天都有完整MA20数据)
    latest_trading_day = calendar.get_latest_trading_day("2025-12-11")
    all_trading_days = sorted(calendar.get_trading_days())
    latest_idx = all_trading_days.index(latest_trading_day)

    # 往前数80个交易日(确保最近60天都有完整的MA20数据)
    start_idx = max(0, latest_idx - 79)  # 包含当天共80天
    start_date = all_trading_days[start_idx]
    end_date = latest_trading_day

    print(f"\n📊 开始采集大盘指数历史数据（含均线）...")
    print(f"   日期范围: {start_date} ~ {end_date}")
    print(f"   交易日数: {latest_idx - start_idx + 1}天\n")

    results = collector.collect_all_indexes(start_date=start_date, end_date=end_date)

    print(f"\n✅ 采集完成！")
    for symbol, count in results.items():
        index_name = collector.index_mapping[symbol]["name"]
        print(f"   {index_name}: {count} 条记录")

    return results

if __name__ == "__main__":
    print("=" * 50)
    print("大盘指数数据重新初始化")
    print("=" * 50)

    # Step 1: 清理数据
    clear_market_index_data()

    # Step 2: 重新采集
    collect_index_data()

    print("\n" + "=" * 50)
    print("✅ 重新初始化完成！")
    print("=" * 50)
