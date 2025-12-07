#!/usr/bin/env python3
"""
检查概念名称匹配情况
"""
import sys, os
backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, backend_dir)

from dotenv import load_dotenv
load_dotenv()

import akshare as ak
from datetime import datetime

print("=" * 80)
print("🔍 检查概念名称匹配情况")
print("=" * 80)

# 1. 获取今天的涨停股池
date_str = datetime.now().strftime("%Y%m%d")
print(f"\n1️⃣ 获取涨停股池 ({date_str})...")

try:
    limit_up_df = ak.stock_zt_pool_em(date=date_str)
    print(f"   共 {len(limit_up_df)} 只涨停股")

    # 查看字段
    print(f"\n   字段: {limit_up_df.columns.tolist()}")

    # 检查是否有概念字段
    if '所属概念' in limit_up_df.columns:
        concept_col = '所属概念'
    elif '所属行业' in limit_up_df.columns:
        concept_col = '所属行业'
    else:
        print("   ⚠️ 没有找到概念相关字段")
        concept_col = None

    if concept_col:
        # 提取所有概念
        all_concepts = set()
        for concepts_str in limit_up_df[concept_col].fillna(''):
            if concepts_str:
                # 概念通常用分号或逗号分隔
                for c in concepts_str.replace('；', ';').replace('，', ',').split(';'):
                    for cc in c.split(','):
                        if cc.strip():
                            all_concepts.add(cc.strip())

        print(f"\n   涨停股所属概念 (共 {len(all_concepts)} 个):")
        sorted_concepts = sorted(list(all_concepts))
        for i, c in enumerate(sorted_concepts[:30], 1):  # 只显示前30个
            print(f"      {i}. {c}")
        if len(all_concepts) > 30:
            print(f"      ... 还有 {len(all_concepts) - 30} 个")

        # 2. 测试匹配
        print(f"\n2️⃣ 测试热门概念匹配:")
        hot_concepts = ["超导概念", "光纤概念", "福建自贸区", "可控核聚变", "商业航天"]

        for concept in hot_concepts:
            matched = limit_up_df[
                limit_up_df[concept_col].fillna('').str.contains(concept, na=False, regex=False)
            ]
            print(f"\n   【{concept}】")
            print(f"      精确匹配: {len(matched)} 只股票")

            if len(matched) == 0:
                # 尝试部分匹配
                partial_name = concept.replace("概念", "").replace("板块", "")
                matched_partial = limit_up_df[
                    limit_up_df[concept_col].fillna('').str.contains(partial_name, na=False, regex=False)
                ]
                print(f"      部分匹配 ('{partial_name}'): {len(matched_partial)} 只股票")

                if len(matched_partial) > 0:
                    print(f"      示例股票: {matched_partial.iloc[0]['名称']} - {matched_partial.iloc[0][concept_col]}")
            else:
                print(f"      示例股票: {matched.iloc[0]['名称']} - {matched.iloc[0][concept_col]}")

except Exception as e:
    print(f"   ❌ 失败: {e}")

print("\n" + "=" * 80)
