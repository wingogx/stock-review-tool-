"""
测试涨跌停股池API数据结构
检查返回数据中是否包含日期字段
"""

import akshare as ak
import sys
import os

# 添加 backend 到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from datetime import datetime, timedelta

def test_limit_stocks_api():
    """测试涨跌停股池API返回的数据结构"""

    # 使用最近的交易日（尝试今天和昨天）
    today = datetime.now()
    dates_to_try = [
        today.strftime("%Y%m%d"),
        (today - timedelta(days=1)).strftime("%Y%m%d"),
        (today - timedelta(days=2)).strftime("%Y%m%d"),
        (today - timedelta(days=3)).strftime("%Y%m%d"),
    ]

    print("=" * 60)
    print("测试涨停股池 API (stock_zt_pool_em)")
    print("=" * 60)

    limit_up_df = None
    for date_str in dates_to_try:
        try:
            print(f"\n尝试日期: {date_str}")
            df = ak.stock_zt_pool_em(date=date_str)

            if df is not None and not df.empty:
                print(f"✅ 成功获取数据，共 {len(df)} 条记录")
                print(f"\n列名列表:")
                print(df.columns.tolist())

                print(f"\n前3行数据:")
                print(df.head(3).to_string())

                print(f"\n数据类型:")
                print(df.dtypes)

                # 检查是否有日期相关字段
                date_columns = [col for col in df.columns if any(word in col for word in ['日期', '时间', 'date', 'time', 'Date', 'Time'])]
                if date_columns:
                    print(f"\n⚠️  发现日期相关字段: {date_columns}")
                    for col in date_columns:
                        print(f"   {col}: {df[col].iloc[0]}")
                else:
                    print("\n❌ 未发现日期相关字段")

                limit_up_df = df
                break
            else:
                print(f"   该日期无数据")
        except Exception as e:
            print(f"   采集失败: {str(e)}")

    print("\n" + "=" * 60)
    print("测试跌停股池 API (stock_zt_pool_dtgc_em)")
    print("=" * 60)

    limit_down_df = None
    for date_str in dates_to_try:
        try:
            print(f"\n尝试日期: {date_str}")
            df = ak.stock_zt_pool_dtgc_em(date=date_str)

            if df is not None and not df.empty:
                print(f"✅ 成功获取数据，共 {len(df)} 条记录")
                print(f"\n列名列表:")
                print(df.columns.tolist())

                print(f"\n前3行数据:")
                print(df.head(3).to_string())

                print(f"\n数据类型:")
                print(df.dtypes)

                # 检查是否有日期相关字段
                date_columns = [col for col in df.columns if any(word in col for word in ['日期', '时间', 'date', 'time', 'Date', 'Time'])]
                if date_columns:
                    print(f"\n⚠️  发现日期相关字段: {date_columns}")
                    for col in date_columns:
                        print(f"   {col}: {df[col].iloc[0]}")
                else:
                    print("\n❌ 未发现日期相关字段")

                limit_down_df = df
                break
            else:
                print(f"   该日期无数据")
        except Exception as e:
            print(f"   采集失败: {str(e)}")

    print("\n" + "=" * 60)
    print("结论")
    print("=" * 60)

    if limit_up_df is not None:
        date_cols = [col for col in limit_up_df.columns if any(word in col for word in ['日期', '时间', 'date', 'time', 'Date', 'Time'])]
        if date_cols:
            print(f"✅ 涨停股池API包含日期字段: {date_cols}")
            print(f"   建议使用这些字段作为实际交易日期")
        else:
            print("❌ 涨停股池API不包含日期字段")
            print("   只能使用传入的参数日期")

    if limit_down_df is not None:
        date_cols = [col for col in limit_down_df.columns if any(word in col for word in ['日期', '时间', 'date', 'time', 'Date', 'Time'])]
        if date_cols:
            print(f"✅ 跌停股池API包含日期字段: {date_cols}")
            print(f"   建议使用这些字段作为实际交易日期")
        else:
            print("❌ 跌停股池API不包含日期字段")
            print("   只能使用传入的参数日期")

if __name__ == "__main__":
    test_limit_stocks_api()
