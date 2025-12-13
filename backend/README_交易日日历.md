# 2025年A股交易日日历使用说明

## 概述

`trading_calendar_2025.py` 提供了2025年完整的A股交易日日历,包含所有法定节假日和周末休市安排。使用此日历可以避免在采集历史数据时错误地包含非交易日。

## 功能特性

### 1. 完整的节假日数据
- ✅ 元旦: 2025-01-01
- ✅ 春节: 2025-01-28 ~ 2025-02-04 (8天)
- ✅ 清明节: 2025-04-04 ~ 2025-04-06 (3天)
- ✅ 劳动节: 2025-05-01 ~ 2025-05-05 (5天)
- ✅ 端午节: 2025-05-31 ~ 2025-06-02 (3天)
- ✅ 国庆节、中秋节: 2025-10-01 ~ 2025-10-08 (8天)

### 2. 自动周末识别
自动排除所有周六、周日,无需手动判断

### 3. 全年统计
- 总交易日: **243天**
- 首个交易日: 2025-01-02
- 最后交易日: 2025-12-31

## 使用方法

### 基础用法

```python
from backend.trading_calendar_2025 import get_calendar

# 获取日历实例(单例模式)
calendar = get_calendar()

# 判断某天是否为交易日
is_trading = calendar.is_trading_day("2025-10-01")  # False (国庆节)
is_trading = calendar.is_trading_day("2025-10-09")  # True

# 获取某个日期范围内的所有交易日
trading_days = calendar.get_trading_days(
    start_date="2025-09-01",
    end_date="2025-09-30"
)
print(f"9月份交易日: {len(trading_days)}天")

# 获取最近的交易日(今天或之前最近的交易日)
latest = calendar.get_latest_trading_day()
print(f"最近交易日: {latest}")

# 获取指定日期的前后交易日
prev_day = calendar.get_previous_trading_day("2025-10-09")  # 2025-09-30
next_day = calendar.get_next_trading_day("2025-09-30")      # 2025-10-09

# 获取日期详细信息
info = calendar.get_day_info("2025-10-01")
print(info)
# {
#   'date': '2025-10-01',
#   'weekday': '周三',
#   'is_weekend': False,
#   'is_holiday': True,
#   'holiday_name': '国庆节',
#   'is_trading_day': False
# }
```

### 在数据采集中使用

#### 采集最近60个交易日数据

```python
from backend.trading_calendar_2025 import get_calendar

calendar = get_calendar()

# 获取最近60个交易日
latest = calendar.get_latest_trading_day()
all_days = sorted(calendar.get_trading_days())
latest_idx = all_days.index(latest)

# 往前数60天(包含当天)
start_idx = max(0, latest_idx - 59)
target_days = all_days[start_idx:latest_idx + 1]

print(f"采集日期: {target_days[0]} ~ {target_days[-1]}")
print(f"共 {len(target_days)} 个交易日")

# 遍历采集
for date in target_days:
    # 采集数据...
    pass
```

#### 避免采集国庆等长假期数据

```python
# ❌ 错误做法: 简单地跳过周末
current_date = start_date
while current_date <= end_date:
    if current_date.weekday() >= 5:  # 只跳过周末
        current_date += timedelta(days=1)
        continue
    # 这样会错误地采集国庆节(10-01~10-08)数据
    collect_data(current_date)
    current_date += timedelta(days=1)

# ✅ 正确做法: 使用交易日日历
trading_days = calendar.get_trading_days(start_date, end_date)
for date in trading_days:
    # 自动排除周末和节假日
    collect_data(date)
```

## 已更新的文件

以下文件已集成交易日日历:

1. **采集脚本**
   - `collect_sentiment_history.py` - 市场情绪历史数据采集
   - `collect_index_history.py` - 大盘指数历史数据采集

2. **工具模块**
   - `app/utils/trading_date.py` - 交易日期工具
     - `get_latest_trading_date()` 函数优先使用日历

## 测试

运行测试脚本验证功能:

```bash
cd backend
python3 trading_calendar_2025.py
```

输出示例:
```
=== 2025年A股交易日日历 ===

1. 全年交易日统计:
   总交易日: 243天
   首个交易日: 2025-01-02
   最后交易日: 2025-12-31

2. 节假日休市安排:
   元旦: 2025-01-01 ~ 2025-01-01 (1天)
   劳动节: 2025-05-01 ~ 2025-05-05 (5天)
   ...

✅ 测试完成!
```

## 注意事项

1. **单例模式**: 使用 `get_calendar()` 获取全局单例,避免重复创建对象
2. **日期格式**: 所有日期使用标准格式 `YYYY-MM-DD`
3. **年度更新**: 此日历仅适用于2025年,2026年需要创建新的日历文件
4. **数据源**: 基于中国证监会发布的2025年休市安排

## 常见问题

### Q: 为什么10月份只有17个交易日?
A: 国庆节和中秋节连休8天(10-01 ~ 10-08),扣除这8天和4个周末,10月份实际交易日为17天。

### Q: 如何处理历史数据中的无效日期?
A: 使用交易日日历可以避免采集无效日期,如果已经采集了错误数据,可以通过查询清理:

```python
from supabase import create_client
from backend.trading_calendar_2025 import get_calendar

calendar = get_calendar()
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 查询所有数据
result = supabase.table("market_sentiment").select("trade_date").execute()

# 找出非交易日的数据
invalid_dates = [
    item['trade_date']
    for item in result.data
    if not calendar.is_trading_day(item['trade_date'])
]

# 删除无效数据
for date in invalid_dates:
    supabase.table("market_sentiment").delete().eq("trade_date", date).execute()
```

### Q: 为什么不直接用Tushare的交易日历接口?
A:
1. Tushare交易日历需要消耗积分
2. 离线日历不依赖网络请求,速度更快
3. 便于测试和验证逻辑
4. 可以提前知道全年的交易日安排

## 更新记录

- 2025-12-12: 首次创建,包含2025年完整休市安排
