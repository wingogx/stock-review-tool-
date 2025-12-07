#!/usr/bin/env python3
"""
查询数据库中的热门概念数据
"""
import sys, os
backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, backend_dir)

from dotenv import load_dotenv
load_dotenv()

from app.utils.supabase_client import get_supabase

supabase = get_supabase()

print("=" * 60)
print("📊 查询数据库中的热门概念数据")
print("=" * 60)

# 查询所有热门概念的最新数据
response = supabase.table("hot_concepts").select("*").order("trade_date", desc=True).limit(20).execute()

if response.data:
    print(f"\n✅ 找到 {len(response.data)} 条最新热门概念数据:\n")

    for record in response.data:
        print(f"【{record['concept_name']}】")
        print(f"  日期: {record['trade_date']}")
        print(f"  涨跌幅: {record['change_pct']}%")
        print(f"  排名: {record['rank']}")
        print(f"  股票数: {record.get('stock_count', 0)}")
        print(f"  涨停数: {record.get('limit_up_count', 0)}")
        print(f"  概念强度: {record.get('concept_strength', 0)}")
        print()
else:
    print("\n❌ 表为空，没有找到热门概念数据")

print("=" * 60)
