"""
测试涨停股采集器 - Tushare优先版本
"""
from dotenv import load_dotenv
load_dotenv()

from loguru import logger
import sys

logger.remove()
logger.add(sys.stdout, level="INFO")

from app.services.collectors.limit_stocks_collector import LimitStocksCollector

print("=" * 80)
print("测试涨停股采集器（Tushare优先，带concepts字段）")
print("=" * 80)
print()

# 创建采集器实例
collector = LimitStocksCollector()

# 测试采集2025-12-10的数据
trade_date = "2025-12-10"
print(f"开始采集 {trade_date} 的涨跌停数据...")
print()

results = collector.collect_and_save(trade_date=trade_date)

print()
print("=" * 80)
print(f"✅ 采集完成:")
print(f"   涨停股: {results['limit_up']} 只")
print(f"   跌停股: {results['limit_down']} 只")
print("=" * 80)

# 查询数据库验证concepts字段
print()
print("验证数据库中的concepts字段...")
from app.utils.supabase_client import get_supabase
supabase = get_supabase()

result = supabase.table('limit_stocks_detail')\
    .select('stock_code, stock_name, concepts')\
    .eq('trade_date', trade_date)\
    .eq('limit_type', 'limit_up')\
    .limit(5)\
    .execute()

if result.data:
    print(f"\n前5只涨停股的concepts字段示例:")
    for stock in result.data:
        concepts = stock.get('concepts', [])
        print(f"  {stock['stock_code']} {stock['stock_name']}: {concepts}")
else:
    print("⚠️ 未查询到涨停股数据")
