"""
测试 Tushare Token 是否有效
"""
import os
import sys
import tushare as ts
from dotenv import load_dotenv
from pathlib import Path

# 加载项目根目录的 .env 文件
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(env_path)

# 从环境变量读取token
token = os.getenv("TUSHARE_TOKEN")
print(f"从 {env_path} 读取 Token: {token}")

try:
    # 初始化
    pro = ts.pro_api(token)
    print("✅ Token 初始化成功")

    # 测试1: 获取交易日历
    print("\n测试1: 获取交易日历...")
    df = pro.trade_cal(exchange='SSE', start_date='20251201', end_date='20251213')
    if df is not None and len(df) > 0:
        print(f"✅ 成功获取 {len(df)} 条交易日历数据")
        print(df.head())
    else:
        print("❌ 获取交易日历失败")

    # 测试2: 获取股票日线数据
    print("\n测试2: 获取股票日线数据...")
    df = pro.daily(ts_code='000001.SZ', start_date='20251201', end_date='20251213')
    if df is not None and len(df) > 0:
        print(f"✅ 成功获取 {len(df)} 条日线数据")
        print(df)
    else:
        print("❌ 获取日线数据失败")

    # 测试3: 获取指定股票连续2天的数据（模拟回测场景）
    print("\n测试3: 模拟回测场景 - 获取000001.SZ从12月9日开始的数据...")
    df = pro.daily(ts_code='000001.SZ', start_date='20251209', end_date='20251213')
    if df is not None and len(df) >= 2:
        print(f"✅ 成功获取 {len(df)} 条数据")
        df = df.sort_values('trade_date')
        print(df)
        print(f"\n第1天: {df.iloc[0]['trade_date']}, 涨跌幅: {df.iloc[0]['pct_chg']}%")
        print(f"第2天: {df.iloc[1]['trade_date']}, 涨跌幅: {df.iloc[1]['pct_chg']}%")
    else:
        print("❌ 数据不足")

    print("\n✅ Token 验证通过！")

except Exception as e:
    print(f"\n❌ Token 验证失败: {e}")
    import traceback
    traceback.print_exc()
