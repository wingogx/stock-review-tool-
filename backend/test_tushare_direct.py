"""
直接测试 Tushare Token（不使用自定义URL）
"""
import tushare as ts

# 直接使用token，不设置环境变量
token = "4937369187852746524"
print(f"测试 Token: {token}")

try:
    # 初始化（不设置自定义URL）
    pro = ts.pro_api(token)
    print("✅ Token 初始化成功")

    # 测试：获取股票日线数据
    print("\n测试: 获取000001.SZ日线数据...")
    df = pro.daily(ts_code='000001.SZ', start_date='20251201', end_date='20251213')
    if df is not None and len(df) > 0:
        print(f"✅ 成功获取 {len(df)} 条数据")
        print(df)
    else:
        print("❌ 获取数据失败")

    print("\n✅ Token 验证通过！")

except Exception as e:
    print(f"\n❌ Token 验证失败: {e}")
    import traceback
    traceback.print_exc()
