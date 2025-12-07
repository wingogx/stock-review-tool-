"""
修复数据库中的交易日期
将错误的日期(如12月6日、12月7日、12月8日)更正为实际的交易日期(12月5日)
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

def check_and_fix_dates():
    """检查并修复所有表中的日期"""

    supabase = get_supabase()

    # 正确的交易日期
    correct_date = "2025-12-05"

    # 可能的错误日期 (周五之后的日期)
    wrong_dates = ["2025-12-06", "2025-12-07", "2025-12-08"]

    tables = [
        "hot_concepts",
        "limit_stocks_detail",
        "market_sentiment",
        "market_index"
    ]

    print("=" * 60)
    print("检查并修复数据库中的交易日期")
    print("=" * 60)
    print(f"正确的交易日期: {correct_date}")
    print(f"需要修正的日期: {', '.join(wrong_dates)}")
    print("=" * 60)

    for table in tables:
        print(f"\n检查表: {table}")

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
                marker = " ❌ 需要修复" if date in wrong_dates else " ✅"
                print(f"    {date}: {count} 条记录{marker}")

            # 修复错误日期
            fixed_count = 0
            for wrong_date in wrong_dates:
                if wrong_date in date_counts:
                    print(f"\n  修复 {wrong_date} -> {correct_date}...")

                    # 更新日期
                    try:
                        update_response = supabase.table(table)\
                            .update({"trade_date": correct_date})\
                            .eq("trade_date", wrong_date)\
                            .execute()

                        count = date_counts[wrong_date]
                        fixed_count += count
                        print(f"    ✅ 成功修复 {count} 条记录")

                    except Exception as e:
                        print(f"    ❌ 修复失败: {str(e)}")

            if fixed_count > 0:
                print(f"  ✅ {table} - 共修复 {fixed_count} 条记录")
            else:
                print(f"  ✅ {table} - 无需修复")

        except Exception as e:
            print(f"  ❌ 检查 {table} 失败: {str(e)}")

    print("\n" + "=" * 60)
    print("修复完成！")
    print("=" * 60)


def verify_dates():
    """验证修复后的日期"""

    supabase = get_supabase()
    correct_date = "2025-12-05"

    tables = [
        "hot_concepts",
        "limit_stocks_detail",
        "market_sentiment",
        "market_index"
    ]

    print("\n" + "=" * 60)
    print("验证修复结果")
    print("=" * 60)

    for table in tables:
        try:
            # 查询最新日期的记录数
            response = supabase.table(table)\
                .select("trade_date", count="exact")\
                .eq("trade_date", correct_date)\
                .execute()

            count = response.count if hasattr(response, 'count') else len(response.data)
            print(f"✅ {table}: {count} 条记录的日期为 {correct_date}")

        except Exception as e:
            print(f"❌ {table}: 验证失败 - {str(e)}")

    print("=" * 60)


if __name__ == "__main__":
    print("\n🔧 开始修复交易日期...\n")

    # 检查并修复
    check_and_fix_dates()

    # 验证结果
    verify_dates()

    print("\n✅ 所有操作完成！\n")
