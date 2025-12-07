"""
清理并重新采集涨跌停股票数据
"""

import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加 backend 到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.utils.supabase_client import get_supabase
from app.services.collectors.limit_stocks_collector import LimitStocksCollector
from loguru import logger

# 配置日志
logger.remove()
logger.add(sys.stdout, level="INFO")

def clean_limit_stocks_table():
    """清理涨跌停股票表"""

    supabase = get_supabase()

    print("=" * 60)
    print("清理 limit_stocks_detail 表")
    print("=" * 60)

    try:
        # 查询当前记录数
        response = supabase.table("limit_stocks_detail")\
            .select("*", count="exact")\
            .execute()

        count = response.count if hasattr(response, 'count') else len(response.data)
        print(f"\n当前表中有 {count} 条记录")

        if count > 0:
            print(f"正在删除所有记录...")

            # 删除所有记录
            delete_response = supabase.table("limit_stocks_detail")\
                .delete()\
                .neq("id", 0)\
                .execute()  # 删除所有 id != 0 的记录(即所有记录)

            print(f"✅ 成功清理 limit_stocks_detail 表")
        else:
            print(f"✅ 表已经是空的,无需清理")

    except Exception as e:
        print(f"❌ 清理失败: {str(e)}")
        return False

    return True


def recollect_limit_stocks():
    """重新采集涨跌停股票数据"""

    print("\n" + "=" * 60)
    print("重新采集涨跌停股票数据")
    print("=" * 60)

    try:
        collector = LimitStocksCollector()

        # 不传入日期参数,让它自动使用最近交易日
        results = collector.collect_and_save()

        print("\n" + "=" * 60)
        print("采集结果")
        print("=" * 60)
        print(f"✅ 涨停股票: {results['limit_up']} 只")
        print(f"✅ 跌停股票: {results['limit_down']} 只")
        print(f"✅ 总计: {results['limit_up'] + results['limit_down']} 只")

        return True

    except Exception as e:
        print(f"❌ 采集失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def verify_data():
    """验证数据"""

    supabase = get_supabase()

    print("\n" + "=" * 60)
    print("验证采集结果")
    print("=" * 60)

    try:
        # 查询所有记录
        response = supabase.table("limit_stocks_detail")\
            .select("*")\
            .execute()

        if not response.data:
            print("❌ 表为空,采集可能失败")
            return False

        # 统计各个字段
        data = response.data
        total = len(data)

        # 统计日期分布
        dates = [row['trade_date'] for row in data]
        date_counts = {}
        for date in dates:
            date_counts[date] = date_counts.get(date, 0) + 1

        # 统计涨停/跌停分布
        limit_types = [row['limit_type'] for row in data]
        limit_up_count = limit_types.count('limit_up')
        limit_down_count = limit_types.count('limit_down')

        print(f"\n总记录数: {total}")
        print(f"\n日期分布:")
        for date, count in sorted(date_counts.items()):
            print(f"  {date}: {count} 条记录")

        print(f"\n涨跌停分布:")
        print(f"  涨停 (limit_up): {limit_up_count} 只")
        print(f"  跌停 (limit_down): {limit_down_count} 只")

        # 显示前5条记录
        print(f"\n前5条记录样例:")
        for i, row in enumerate(data[:5], 1):
            print(f"\n  [{i}] {row['stock_name']} ({row['stock_code']})")
            print(f"      日期: {row['trade_date']}")
            print(f"      类型: {row['limit_type']}")
            print(f"      涨跌幅: {row.get('change_pct', 'N/A')}%")
            print(f"      收盘价: {row.get('close_price', 'N/A')}")
            if row['limit_type'] == 'limit_up':
                print(f"      封板时间: {row.get('first_limit_time', 'N/A')}")
                print(f"      连板数: {row.get('continuous_days', 'N/A')}")

        print("\n" + "=" * 60)
        print("✅ 数据验证完成")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"❌ 验证失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🔧 开始清理并重新采集涨跌停股票数据...\n")

    # 步骤1: 清理表
    if not clean_limit_stocks_table():
        print("\n❌ 清理失败,终止操作")
        sys.exit(1)

    # 步骤2: 重新采集
    if not recollect_limit_stocks():
        print("\n❌ 采集失败,终止操作")
        sys.exit(1)

    # 步骤3: 验证数据
    if not verify_data():
        print("\n❌ 验证失败")
        sys.exit(1)

    print("\n✅ 所有操作完成！\n")
