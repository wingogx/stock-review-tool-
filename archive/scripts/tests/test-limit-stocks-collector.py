#!/usr/bin/env python3
import sys, os
backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, backend_dir)

from dotenv import load_dotenv
load_dotenv()

from app.services.collectors.limit_stocks_collector import LimitStocksCollector
from loguru import logger

logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}")

print("="*60)
print("🧪 涨停池/跌停池数据采集测试")
print("="*60)

collector = LimitStocksCollector()
results = collector.collect_and_save()

print(f'\n✅ 涨停股: {results["limit_up"]} 只')
print(f'✅ 跌停股: {results["limit_down"]} 只')
print("="*60)
