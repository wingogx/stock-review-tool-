#!/usr/bin/env python3
import sys, os
backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, backend_dir)

from dotenv import load_dotenv
load_dotenv()

from app.services.collectors.hot_concepts_collector import HotConceptsCollector
from loguru import logger

logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}")

print("="*60)
print("🧪 热门概念板块数据采集测试")
print("="*60)

collector = HotConceptsCollector()
count = collector.collect_and_save(top_n=10)  # 只采集前10个

print(f'\n✅ 成功采集并保存 {count} 个热门概念')
print("="*60)
