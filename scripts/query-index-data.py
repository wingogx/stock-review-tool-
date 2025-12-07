#!/usr/bin/env python3
"""
查询数据库中的指数数据
"""
import sys, os
backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, backend_dir)

from dotenv import load_dotenv
load_dotenv()

from app.utils.supabase_client import get_supabase

supabase = get_supabase()

print("=" * 60)
print("📊 查询数据库中的指数数据")
print("=" * 60)

# 查询所有指数的最新数据
response = supabase.table("market_index").select("*").order("trade_date", desc=True).limit(10).execute()

if response.data:
    print(f"\n✅ 找到 {len(response.data)} 条最新指数数据:\n")

    # 按指数分组显示
    from collections import defaultdict
    by_index = defaultdict(list)
    for record in response.data:
        by_index[record['index_name']].append(record)

    for index_name, records in by_index.items():
        latest = records[0]
        print(f"【{index_name}】")
        print(f"  代码: {latest['index_code']}")
        print(f"  最新日期: {latest['trade_date']}")
        print(f"  收盘价: {latest['close_price']:.2f}")
        print(f"  涨跌幅: {latest['change_pct']:.2f}%")
        print(f"  成交量: {latest['volume']}")
        print(f"  成交额: {latest['amount']:.2e} 元 ({latest['amount']/1e8:.2f} 亿元)")
        print()
else:
    print("\n❌ 没有找到指数数据")

print("=" * 60)
