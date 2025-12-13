#!/usr/bin/env python3
"""
创建回测表的脚本
"""
from pathlib import Path
from dotenv import load_dotenv
from app.utils.supabase_client import get_supabase

# 加载环境变量
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

def create_backtest_table():
    """执行SQL创建回测表"""

    # 读取SQL文件
    sql_file = Path(__file__).parent.parent / "database" / "create-backtest-table.sql"

    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    print("=" * 60)
    print("准备创建回测表...")
    print("=" * 60)

    try:
        supabase = get_supabase()

        # 执行SQL（Supabase Python客户端需要通过RPC或者直接使用PostgreSQL连接）
        # 这里我们使用postgrest_query

        # 由于Supabase Python客户端不支持直接执行DDL，我们需要检查表是否存在
        # 如果不存在，需要手动在Supabase Dashboard中执行SQL

        # 先尝试查询表
        try:
            response = supabase.table("premium_score_backtest").select("count", count="exact").limit(0).execute()
            print("✅ 表 premium_score_backtest 已存在")
            print(f"   当前记录数: {response.count if hasattr(response, 'count') else '未知'}")
            return True
        except Exception as e:
            print(f"⚠️  表不存在或查询失败: {e}")
            print("\n" + "=" * 60)
            print("请在 Supabase Dashboard 中执行以下SQL:")
            print("=" * 60)
            print(sql_content)
            print("=" * 60)
            return False

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    create_backtest_table()
