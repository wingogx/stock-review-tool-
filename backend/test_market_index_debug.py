#!/usr/bin/env python3
"""
大盘指数API详细调试脚本
测试不同的API接口和参数，找出问题原因
"""

import akshare as ak
import pandas as pd
from datetime import datetime
import time

def test_api(api_name, api_func, symbol, **kwargs):
    """测试单个API"""
    print(f"\n{'='*80}")
    print(f"测试 API: {api_name}")
    print(f"参数: symbol={symbol}, {kwargs}")
    print(f"{'='*80}")

    try:
        start_time = time.time()
        df = api_func(symbol=symbol, **kwargs)
        elapsed = time.time() - start_time

        if df is None or df.empty:
            print(f"❌ 返回数据为空")
            return None

        print(f"✅ 成功！耗时: {elapsed:.2f}秒")
        print(f"返回记录数: {len(df)}")
        print(f"\n列名: {list(df.columns)}")
        print(f"\n最新5条数据:")
        print(df.tail())

        return df

    except Exception as e:
        print(f"❌ 失败: {type(e).__name__}")
        print(f"错误详情: {str(e)}")
        import traceback
        print(f"\n完整错误堆栈:")
        traceback.print_exc()
        return None


def main():
    print("\n" + "="*80)
    print("大盘指数API详细调试")
    print("="*80)
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试日期: 2025-12-09")

    # 测试1: 东方财富接口 - 上证指数 (当前使用的)
    print("\n\n【测试1】东方财富接口 - 上证指数")
    print("这是当前代码使用的接口")
    test_api(
        "stock_zh_index_daily_em",
        ak.stock_zh_index_daily_em,
        "sh000001",
        start_date="20251209",
        end_date="20251209"
    )

    time.sleep(3)  # 避免太频繁

    # 测试2: 东方财富接口 - 获取更长时间范围
    print("\n\n【测试2】东方财富接口 - 获取最近3天数据")
    print("测试是否是日期参数的问题")
    test_api(
        "stock_zh_index_daily_em",
        ak.stock_zh_index_daily_em,
        "sh000001",
        start_date="20251207",
        end_date="20251209"
    )

    time.sleep(3)

    # 测试3: 新浪接口 (旧接口)
    print("\n\n【测试3】新浪接口 (旧接口)")
    print("测试旧接口是否还能用")
    test_api(
        "stock_zh_index_daily",
        ak.stock_zh_index_daily,
        "sh000001"
    )

    time.sleep(3)

    # 测试4: 测试其他指数代码
    print("\n\n【测试4】东方财富接口 - 测试深证成指")
    test_api(
        "stock_zh_index_daily_em",
        ak.stock_zh_index_daily_em,
        "sz399001",
        start_date="20251209",
        end_date="20251209"
    )

    time.sleep(3)

    # 测试5: 不指定日期参数，获取默认数据
    print("\n\n【测试5】东方财富接口 - 不指定日期（默认全部数据）")
    print("测试是否是日期参数导致的问题")
    try:
        print("调用 ak.stock_zh_index_daily_em(symbol='sh000001') ...")
        df = ak.stock_zh_index_daily_em(symbol="sh000001")
        print(f"✅ 成功！返回 {len(df)} 条记录")
        print(f"最新日期: {df['date'].max()}")
        print(f"\n最新5条数据:")
        print(df.tail())
    except Exception as e:
        print(f"❌ 失败: {str(e)}")
        import traceback
        traceback.print_exc()

    # 测试6: 检查AKShare版本
    print("\n\n【测试6】检查环境信息")
    print(f"AKShare 版本: {ak.__version__}")
    print(f"Pandas 版本: {pd.__version__}")

    # 测试7: 测试网络连接
    print("\n\n【测试7】测试网络连接")
    try:
        import requests
        response = requests.get("https://quote.eastmoney.com", timeout=10)
        print(f"✅ 东方财富网站可访问 (状态码: {response.status_code})")
    except Exception as e:
        print(f"❌ 无法访问东方财富: {str(e)}")

    print("\n" + "="*80)
    print("测试完成")
    print("="*80)


if __name__ == "__main__":
    main()
