"""
修复数据库中的交易日期 (改进版)
先删除错误日期的记录,避免唯一约束冲突
"""

import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加 backend 到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.utils.supabase_client import get_supabase
from datetime import datetime
from loguru import logger

# 配置日志
logger.remove()
logger.add(sys.stdout, level="INFO")

def fix_dates_by_deletion():
    """通过删除错误日期记录的方式修复"""

    supabase = get_supabase()

    # 正确的交易日期
    correct_date = "2025-12-05"

    # 可能的错误日期 (周五之后的日期)
    wrong_dates = ["2025-12-06", "2025-12-07", "2025-12-08"]

    tables = [
        "limit_stocks_detail",
        "market_sentiment"
    ]

    print("=" * 60)
    print("修复数据库中的交易日期（通过删除错误记录）")
    print("=" * 60)
    print(f"正确的交易日期: {correct_date}")
    print(f"需要删除的错误日期: {', '.join(wrong_dates)}")
    print("=" * 60)

    for table in tables:
        print(f"\n处理表: {table}")

        try:
            # 查询该表中的所有不同日期
            response = supabase.table(table)\
                .select("trade_date")\
                .execute()

            if not response.data:
                print(f"  ✅ {table} - 表为空，无需修复")
                continue

            # 统计各个日期的记录数
            dates = [row['trade_date'] for row in response.data]
            date_counts = {}
            for date in dates:
                date_counts[date] = date_counts.get(date, 0) + 1

            print(f"  当前日期分布:")
            for date, count in sorted(date_counts.items()):
                marker = " ❌ 将被删除" if date in wrong_dates else " ✅ 保留"
                print(f"    {date}: {count} 条记录{marker}")

            # 删除错误日期的记录
            deleted_count = 0
            for wrong_date in wrong_dates:
                if wrong_date in date_counts:
                    print(f"\n  删除 {wrong_date} 的记录...")

                    try:
                        delete_response = supabase.table(table)\
                            .delete()\
                            .eq("trade_date", wrong_date)\
                            .execute()

                        count = date_counts[wrong_date]
                        deleted_count += count
                        print(f"    ✅ 成功删除 {count} 条记录")

                    except Exception as e:
                        print(f"    ❌ 删除失败: {str(e)}")

            if deleted_count > 0:
                print(f"  ✅ {table} - 共删除 {deleted_count} 条错误记录")
            else:
                print(f"  ✅ {table} - 无需删除")

        except Exception as e:
            print(f"  ❌ 处理 {table} 失败: {str(e)}")

    print("\n" + "=" * 60)
    print("修复完成！")
    print("=" * 60)


def verify_final_state():
    """验证最终状态"""

    supabase = get_supabase()
    correct_date = "2025-12-05"
    wrong_dates = ["2025-12-06", "2025-12-07", "2025-12-08"]

    tables = [
        "hot_concepts",
        "limit_stocks_detail",
        "market_sentiment",
        "market_index"
    ]

    print("\n" + "=" * 60)
    print("验证最终状态")
    print("=" * 60)

    for table in tables:
        try:
            # 查询所有不同日期
            response = supabase.table(table)\
                .select("trade_date")\
                .execute()

            if not response.data:
                print(f"✅ {table}: 表为空")
                continue

            # 统计日期分布
            dates = [row['trade_date'] for row in response.data]
            date_counts = {}
            for date in dates:
                date_counts[date] = date_counts.get(date, 0) + 1

            # 检查是否还有错误日期
            has_wrong_dates = any(date in wrong_dates for date in date_counts.keys())

            if has_wrong_dates:
                print(f"❌ {table}: 仍存在错误日期")
                for date, count in sorted(date_counts.items()):
                    if date in wrong_dates:
                        print(f"   ❌ {date}: {count} 条记录")
            else:
                # 显示正确日期的记录数
                correct_count = date_counts.get(correct_date, 0)
                total = len(response.data)
                print(f"✅ {table}: 共 {total} 条记录, {correct_date} 有 {correct_count} 条")

        except Exception as e:
            print(f"❌ {table}: 验证失败 - {str(e)}")

    print("=" * 60)


if __name__ == "__main__":
    print("\n🔧 开始修复交易日期...\n")

    # 删除错误日期的记录
    fix_dates_by_deletion()

    # 验证最终状态
    verify_final_state()

    print("\n✅ 所有操作完成！")
    print("\n说明: 错误日期的记录已被删除。")
    print("如需重新采集这些日期的数据,请使用正确的日期参数运行采集器。\n")
