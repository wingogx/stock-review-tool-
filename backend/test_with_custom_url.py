"""
使用自定义HTTP URL测试
"""
import tushare as ts

token = "4937369187852746524"
http_url = "http://7d01.xiximiao.com/dataapi"

print(f"Token: {token}")
print(f"HTTP URL: {http_url}\n")

try:
    # 使用自定义URL初始化
    pro = ts.pro_api()
    pro._DataApi__token = token
    pro._DataApi__http_url = http_url

    print("测试: 获取2024-11月数据...")
    df = pro.daily(ts_code='000001.SZ', start_date='20241101', end_date='20241130')

    if df is not None and len(df) > 0:
        print(f"✅ 成功！获取 {len(df)} 条数据")
        print(df.head())
    else:
        print("❌ 无数据")

except Exception as e:
    print(f"❌ 失败: {e}")
