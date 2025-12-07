#!/usr/bin/env python3
"""
测试 Supabase 数据库连接
验证配置是否正确，表是否创建成功
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# 加载环境变量
load_dotenv()

def test_connection():
    """测试 Supabase 连接"""

    print("=" * 60)
    print("🔍 Supabase 连接测试")
    print("=" * 60)
    print()

    # 1. 检查环境变量
    print("📋 Step 1: 检查环境变量配置")
    print("-" * 60)

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    anon_key = os.getenv("SUPABASE_ANON_KEY")

    if not url or url == "your_supabase_url":
        print("❌ SUPABASE_URL 未配置")
        return False
    print(f"✅ SUPABASE_URL: {url}")

    if not key or key == "your_service_role_key":
        print("❌ SUPABASE_KEY 未配置")
        return False
    print(f"✅ SUPABASE_KEY: {key[:20]}...")

    if not anon_key or anon_key == "your_anon_public_key":
        print("❌ SUPABASE_ANON_KEY 未配置")
        return False
    print(f"✅ SUPABASE_ANON_KEY: {anon_key[:20]}...")
    print()

    # 2. 测试连接
    print("📋 Step 2: 测试数据库连接")
    print("-" * 60)

    try:
        # 使用 service_role key 创建客户端（有完整权限）
        supabase: Client = create_client(url, key)
        print("✅ Supabase 客户端创建成功")
    except Exception as e:
        print(f"❌ Supabase 客户端创建失败: {e}")
        return False
    print()

    # 3. 验证表是否存在
    print("📋 Step 3: 验证数据库表")
    print("-" * 60)

    # MVP 版本 - 仅保留核心表
    expected_tables = [
        "market_index",              # 1. 大盘指数表
        "market_sentiment",          # 2. 市场情绪分析表
        "limit_stocks_detail",       # 3. 涨跌停个股详细表
        "hot_concepts",              # 4. 热门概念表
        "user_watchlist"             # 5. 用户自选股配置表（预留）
    ]

    # 注意: concept_stocks 表是可选的，如果存在也算正常

    try:
        # 使用简单的方法：尝试查询每张表
        found_tables = []
        missing_tables = []

        for table in expected_tables:
            try:
                # 尝试查询表（限制 1 条记录）
                result = supabase.table(table).select("*").limit(1).execute()
                found_tables.append(table)
                print(f"  ✅ {table}")
            except Exception as e:
                missing_tables.append(table)
                error_msg = str(e)
                if "does not exist" in error_msg or "relation" in error_msg:
                    print(f"  ❌ {table} - 表不存在")
                else:
                    print(f"  ⚠️  {table} - {error_msg[:50]}")

        print()
        print(f"📊 统计: 发现 {len(found_tables)}/{len(expected_tables)} 张表")

        # 检查是否还有 concept_stocks 表（可选表）
        try:
            result = supabase.table("concept_stocks").select("*").limit(1).execute()
            print(f"  ℹ️  concept_stocks (可选表) - 已存在")
        except:
            pass

        if len(found_tables) == len(expected_tables):
            print("✅ 所有 MVP 核心表都已创建！")
            print()
            return True
        elif len(found_tables) > 0:
            print(f"⚠️  部分表已创建，缺少 {len(missing_tables)} 张表:")
            for table in missing_tables:
                print(f"   - {table}")
            print()
            print("💡 请在 Supabase SQL Editor 中执行完整的 database/schema.sql")
            return False
        else:
            print("❌ 未找到任何表")
            print()
            print("💡 下一步操作:")
            print("   1. 打开 Supabase 项目: https://xzuxntimaushuughrclw.supabase.co")
            print("   2. 点击左侧菜单 'SQL Editor'")
            print("   3. 点击 'New query'")
            print("   4. 复制 database/schema.sql 的完整内容")
            print("   5. 粘贴到编辑器并点击 'Run'")
            return False

    except Exception as e:
        print(f"❌ 验证过程出错: {e}")
        print()
        print("💡 请检查:")
        print("   1. 网络连接是否正常")
        print("   2. Supabase 项目是否正常运行")
        print("   3. Service Role Key 是否正确")
        return False

def main():
    """主函数"""
    success = test_connection()

    print()
    print("=" * 60)
    if success:
        print("🎉 测试通过！Supabase 配置正确，表已创建成功！")
        print()
        print("⏭️  下一步: Task 1.2 - 后端项目初始化")
    else:
        print("❌ 测试失败，请检查上述问题")
        print()
        print("📖 参考文档:")
        print("   - docs/开发指南/Supabase数据库搭建指南.md")
        print("   - Task-1.1-检查清单.md")
    print("=" * 60)

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
