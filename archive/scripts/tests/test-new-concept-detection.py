#!/usr/bin/env python3
"""
测试新概念识别功能
验证系统能否正确识别和处理历史数据不足5天的新概念
"""
import sys, os
backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, backend_dir)

from dotenv import load_dotenv
load_dotenv()

from app.services.collectors.hot_concepts_collector import HotConceptsCollector
from loguru import logger

logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}")

print("="*70)
print("🔍 测试新概念识别功能")
print("="*70)
print()
print("测试目标：")
print("1. 验证系统能否处理历史数据不足5个交易日的概念")
print("2. 确认新概念会在日志中标记 🆕")
print("3. 检查新概念是否能正常参与排名")
print()
print("="*70)

collector = HotConceptsCollector()

# 只采集前10个，方便查看日志
print("\n开始采集热门概念（前10个）...\n")
hot_concepts = collector.collect_hot_concepts(top_n=10)

print("\n" + "="*70)
print(f"✅ 成功采集 {len(hot_concepts)} 个热门概念")
print("="*70)

# 显示详细信息
print("\n📊 热门概念详情：")
for idx, concept in enumerate(hot_concepts, 1):
    print(f"  {idx}. {concept['concept_name']}")
    print(f"     - 涨幅: {concept['change_pct']}%")
    print(f"     - 概念强度: {concept['concept_strength']}")
    print(f"     - 交易日期: {concept['trade_date']}")
    print()

print("="*70)
print("💡 提示：")
print("- 如果看到 🆕 标记，说明发现了新概念（历史数据不足5个交易日）")
print("- 新概念使用实际可用的交易日数据计算涨幅")
print("- 新概念仍会参与排名，不会被遗漏")
print("="*70)
