#!/usr/bin/env python3
"""
检查龙头股数据
"""
import sys, os
backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, backend_dir)

from dotenv import load_dotenv
load_dotenv()

from app.utils.supabase_client import get_supabase
import json

supabase = get_supabase()

print("=" * 60)
print("📊 检查龙头股数据")
print("=" * 60)

response = supabase.table("hot_concepts").select("*").order("change_pct", desc=True).limit(3).execute()

for record in response.data:
    print(f"\n【{record['concept_name']}】")
    print(f"  涨跌幅: {record['change_pct']}%")
    print(f"  涨停数: {record['limit_up_count']}")
    print(f"  股票数: {record['stock_count']}")

    leading_stocks = record.get('leading_stocks', [])
    print(f"  龙头股数组: {type(leading_stocks)} - {len(leading_stocks) if leading_stocks else 0} 个")

    if leading_stocks and len(leading_stocks) > 0:
        print(f"  龙头股内容:")
        for i, stock_json in enumerate(leading_stocks, 1):
            try:
                stock = json.loads(stock_json) if isinstance(stock_json, str) else stock_json
                print(f"    {i}. {stock.get('name', '未知')} ({stock.get('code', '')})")
                print(f"       涨跌幅: {stock.get('change_pct', 0)}%")
                print(f"       连板数: {stock.get('continuous_days', 0)}")
                print(f"       封板时间: {stock.get('first_limit_time', '')}")
            except Exception as e:
                print(f"    {i}. 解析失败: {e}")
                print(f"       原始数据: {stock_json}")
    else:
        print(f"  ⚠️ 没有龙头股数据")

print("\n" + "=" * 60)
