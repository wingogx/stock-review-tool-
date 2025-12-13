#!/usr/bin/env python3
"""
使用psycopg2直接连接Supabase执行SQL
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

def execute_sql():
    """执行SQL创建表"""
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 未安装，正在安装...")
        os.system("pip3 install psycopg2-binary")
        import psycopg2

    # Supabase PostgreSQL连接信息
    # 格式：postgresql://postgres:[password]@[host]:5432/postgres
    supabase_url = os.getenv("SUPABASE_URL")

    # 从URL中提取项目ID
    # https://yowpwgpuznrqsyeukgbf.supabase.co -> yowpwgpuznrqsyeukgbf
    project_id = supabase_url.replace("https://", "").replace(".supabase.co", "")

    # 构建PostgreSQL连接字符串
    # Supabase的数据库连接需要使用项目密码
    # 通常在 Project Settings > Database > Connection string 中获取
    # 格式：postgresql://postgres.yowpwgpuznrqsyeukgbf:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres

    print("=" * 60)
    print("⚠️  直接数据库连接需要数据库密码")
    print("=" * 60)
    print("请在 Supabase Dashboard 中:")
    print("1. 打开 Project Settings > Database")
    print("2. 找到 Connection string")
    print("3. 复制 Connection Pooler (port 6543) 的连接字符串")
    print("4. 手动执行 database/create-backtest-table.sql 中的SQL")
    print("=" * 60)
    print("\n或者使用 Supabase SQL Editor:")
    print("1. 打开 Supabase Dashboard > SQL Editor")
    print("2. 新建查询")
    print("3. 粘贴 database/create-backtest-table.sql 的内容")
    print("4. 点击 Run 执行")
    print("=" * 60)

    # 读取并显示SQL
    sql_file = Path(__file__).parent.parent / "database" / "create-backtest-table.sql"
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    print("\n要执行的SQL:")
    print("=" * 60)
    print(sql_content)
    print("=" * 60)

if __name__ == "__main__":
    execute_sql()
