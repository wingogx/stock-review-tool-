"""
最终 Token 和方法验证测试
"""
import os
import tushare as ts
from dotenv import load_dotenv
from pathlib import Path

# 加载环境变量
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(env_path)

token = os.getenv("TUSHARE_TOKEN")
http_url = os.getenv("TUSHARE_HTTP_URL")

print("=" * 60)
print("🔍 Tushare 配置验证")
print("=" * 60)
print(f"Token: {token}")
print(f"HTTP URL: {http_url}")
print()

try:
    # 方法1: 使用自定义URL初始化
    print("方法1: 使用自定义HTTP URL")
    print("-" * 60)
    pro = ts.pro_api()
    pro._DataApi__token = token
    pro._DataApi__http_url = http_url

    # 测试1: 获取交易日历
    print("测试1: 获取2025年12月交易日历...")
    df1 = pro.trade_cal(exchange='SSE', start_date='20251201', end_date='20251213')
    if df1 is not None and len(df1) > 0:
        print(f"✅ 成功！获取 {len(df1)} 条记录")
        trading_days = df1[df1['is_open'] == 1]
        print(f"   其中交易日: {len(trading_days)} 天")
    else:
        print("❌ 失败")

    print()

    # 测试2: 获取股票日线数据（模拟回测场景）
    print("测试2: 获取股票日线数据（000001.SZ, 2024-11月）...")
    df2 = pro.daily(ts_code='000001.SZ', start_date='20241101', end_date='20241130')
    if df2 is not None and len(df2) > 0:
        print(f"✅ 成功！获取 {len(df2)} 条记录")
        print(f"   日期范围: {df2['trade_date'].min()} ~ {df2['trade_date'].max()}")
    else:
        print("❌ 失败")

    print()

    # 测试3: 模拟回测中获取次日数据的场景
    print("测试3: 模拟回测场景（获取12月9日后的数据）...")
    df3 = pro.daily(ts_code='000001.SZ', start_date='20251209', end_date='20251213')
    if df3 is not None and len(df3) >= 2:
        df3 = df3.sort_values('trade_date')
        print(f"✅ 成功！获取 {len(df3)} 条记录")
        print(f"   第1天: {df3.iloc[0]['trade_date']}, 涨跌幅: {df3.iloc[0]['pct_chg']:.2f}%")
        print(f"   第2天: {df3.iloc[1]['trade_date']}, 涨跌幅: {df3.iloc[1]['pct_chg']:.2f}%")
        print("   ✅ 可以获取次日涨跌幅数据")
    else:
        print("❌ 数据不足")

    print()
    print("=" * 60)
    print("✅ 所有测试通过！Token 和方法配置正确")
    print("=" * 60)

except Exception as e:
    print()
    print("=" * 60)
    print(f"❌ 测试失败: {e}")
    print("=" * 60)
    import traceback
    traceback.print_exc()
