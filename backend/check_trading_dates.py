"""
检查数据库中的交易日期数据
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from app.utils.supabase_client import get_supabase

supabase = get_supabase()

# 查询数据库中最近的交易日期
response = supabase.table('limit_stocks_detail')\
    .select('trade_date')\
    .order('trade_date', desc=True)\
    .limit(10)\
    .execute()

print("数据库中最近10个交易日:")
dates = sorted(set([r['trade_date'] for r in response.data]), reverse=True)
for date in dates:
    print(f"  - {date}")

# 检查12月11日是否有数据
response_1211 = supabase.table('limit_stocks_detail')\
    .select('stock_code, stock_name, limit_type')\
    .eq('trade_date', '2024-12-11')\
    .eq('limit_type', 'limit_up')\
    .limit(5)\
    .execute()

print(f"\n2024-12-11 涨停股票数: {len(response_1211.data)}")
if response_1211.data:
    print("示例:")
    for r in response_1211.data[:5]:
        print(f"  {r['stock_code']} {r['stock_name']}")
