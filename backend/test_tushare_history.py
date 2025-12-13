"""
测试历史数据（2024年11月）
"""
import tushare as ts

token = "4937369187852746524"
print(f"测试 Token: {token}\n")

try:
    pro = ts.pro_api(token)

    # 测试1: 2024年11月数据
    print("测试1: 获取2024-11月数据...")
    df = pro.daily(ts_code='000001.SZ', start_date='20241101', end_date='20241130')
    if df is not None and len(df) > 0:
        print(f"✅ 成功！获取 {len(df)} 条数据\n")
        print(df.head())
    else:
        print("❌ 失败\n")

except Exception as e:
    print(f"❌ 失败: {e}\n")
