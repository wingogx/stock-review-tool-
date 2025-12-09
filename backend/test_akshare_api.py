"""
测试不同的AKShare接口，找到正确获取深证和创业板指数的方法
"""
import akshare as ak
import pandas as pd

print("=" * 80)
print("测试 AKShare 指数接口")
print("=" * 80)

# 测试1: stock_zh_index_daily (当前使用的接口)
print("\n【方法1】stock_zh_index_daily")
print("-" * 80)
for symbol in ["sh000001", "sz399001", "sz399006"]:
    try:
        df = ak.stock_zh_index_daily(symbol=symbol)
        if df is not None and not df.empty:
            latest = df.tail(1)
            print(f"✅ {symbol}: {len(df)} 条记录, 最新日期: {latest['date'].values[0]}")
        else:
            print(f"❌ {symbol}: 无数据")
    except Exception as e:
        print(f"❌ {symbol}: 错误 - {str(e)}")

# 测试2: index_zh_a_hist (指数历史数据)
print("\n【方法2】index_zh_a_hist")
print("-" * 80)
for symbol, name in [("000001", "上证指数"), ("399001", "深证成指"), ("399006", "创业板指")]:
    try:
        df = ak.index_zh_a_hist(symbol=symbol, period="daily", start_date="20251209", end_date="20251209")
        if df is not None and not df.empty:
            print(f"✅ {name}({symbol}): {len(df)} 条记录")
            print(f"   列名: {list(df.columns)}")
            print(f"   数据: {df.to_dict('records')[0] if len(df) > 0 else 'N/A'}")
        else:
            print(f"❌ {name}({symbol}): 无数据")
    except Exception as e:
        print(f"❌ {name}({symbol}): 错误 - {str(e)}")

# 测试3: stock_zh_index_spot_em (指数实时行情)
print("\n【方法3】stock_zh_index_spot_em (实时行情)")
print("-" * 80)
try:
    df = ak.stock_zh_index_spot_em()
    if df is not None and not df.empty:
        # 查找三大指数
        for code, name in [("000001", "上证指数"), ("399001", "深证成指"), ("399006", "创业板指")]:
            index_data = df[df['代码'] == code]
            if not index_data.empty:
                print(f"✅ {name}({code}): 找到实时数据")
                print(f"   最新价: {index_data['最新价'].values[0]}")
                print(f"   涨跌幅: {index_data['涨跌幅'].values[0]}%")
            else:
                print(f"❌ {name}({code}): 未找到")
    else:
        print("❌ 无法获取实时行情数据")
except Exception as e:
    print(f"❌ 错误 - {str(e)}")

# 测试4: stock_zh_index_daily_em (东方财富指数日线)
print("\n【方法4】stock_zh_index_daily_em")
print("-" * 80)
for code, name in [("sh000001", "上证指数"), ("sz399001", "深证成指"), ("sz399006", "创业板指")]:
    try:
        df = ak.stock_zh_index_daily_em(symbol=code, start_date="20251209", end_date="20251209")
        if df is not None and not df.empty:
            print(f"✅ {name}({code}): {len(df)} 条记录")
            print(f"   列名: {list(df.columns)}")
            if len(df) > 0:
                print(f"   数据: {df.tail(1).to_dict('records')[0]}")
        else:
            print(f"❌ {name}({code}): 无数据")
    except Exception as e:
        print(f"❌ {name}({code}): 错误 - {str(e)}")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
