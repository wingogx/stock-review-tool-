"""
手动采集大盘指数数据
"""
import os
os.chdir('/Users/win/Documents/ai 编程/cc/短线复盘/backend')

from dotenv import load_dotenv
load_dotenv()

from app.services.collectors.market_index_collector import MarketIndexCollector
from loguru import logger
import sys

logger.remove()
logger.add(sys.stdout, level="INFO")

collector = MarketIndexCollector()
result = collector.collect_all_indexes(start_date="2025-12-09", end_date="2025-12-09")

print(f"\n📊 采集结果:")
for symbol, count in result.items():
    print(f"  {symbol}: {count} 条")
print(f"✅ 总计: {sum(result.values())} 条")
