# 数据采集器日期字段使用分析

## 用户问题

> 我发现有一些表中的时间不是交易时间，是你的采集时间，例如limit_stocks_detail表中的第一个列，你检查下，避免错误，你是否都改成交易时间，而不是采集时间。

## 问题分析

### 1. 采集器对比

| 采集器 | API是否返回日期 | 日期字段来源 | 是否有问题 |
|--------|----------------|--------------|------------|
| hot_concepts_collector | ✅ 是（返回"日期"字段） | 从API数据提取 `actual_trade_date` | ✅ 正确 |
| market_index_collector | ✅ 是（返回"trade_date"字段） | 从API数据提取 | ✅ 正确 |
| market_sentiment_collector | ❌ 否 | 使用参数/系统时间 | ⚠️ 潜在问题 |
| limit_stocks_collector | ❌ 否 | 使用参数/系统时间 | ⚠️ 潜在问题 |

### 2. API数据结构分析

#### hot_concepts_collector (正确示例)

**API**: `ak.stock_board_concept_index_ths()`

**返回字段**: 包含 `日期` 字段
```python
# 第190行：从API数据中提取实际交易日期
actual_trade_date = pd.to_datetime(latest_data['日期']).strftime("%Y-%m-%d")
```

**结果**: 即使在周末运行，也会保存最后一个交易日的日期（如周五）✅

---

#### limit_stocks_collector (有问题)

**API**:
- `ak.stock_zt_pool_em()` - 涨停股池
- `ak.stock_zt_pool_dtgc_em()` - 跌停股池

**返回字段**:
```python
['序号', '代码', '名称', '涨跌幅', '最新价', '成交额', '流通市值', '总市值',
 '换手率', '封板资金', '首次封板时间', '最后封板时间', '炸板次数', '涨停统计',
 '连板数', '所属行业']
```

**问题**:
- ❌ 不包含"日期"字段
- ❌ 只有 `首次封板时间`、`最后封板时间` 字段（仅时间点，如 `092500` = 09:25:00）
- ❌ 无法从API数据中提取实际交易日期

**当前代码**（第305行）:
```python
if not trade_date:
    trade_date = datetime.now().strftime("%Y-%m-%d")  # ❌ 使用系统当前时间
```

**问题场景**:
- 在周日运行采集 → `trade_date = "2025-12-08"` （周日）
- 但 API 没有周日的数据 → 采集失败或数据为空
- 如果强制保存 → 数据库中的 `trade_date` 字段是错误的（周日而不是周五）

---

#### market_sentiment_collector (有问题)

**API**:
- `ak.stock_market_activity_legu()` - 市场异动（不含日期）
- `ak.stock_sse_deal_daily()` - 上交所（需要传入日期参数）
- `ak.stock_szse_summary()` - 深交所（需要传入日期参数）

**当前代码**（第270行）:
```python
if not trade_date:
    trade_date = datetime.now().strftime("%Y-%m-%d")  # ❌ 使用系统当前时间
```

**问题**: 和 `limit_stocks_collector` 相同

---

### 3. 调度器分析

**文件**: `app/scheduler/data_scheduler.py`

**调度时间**: 每个交易日 16:00 执行

**调用方式**:
```python
# 第66行 - 涨跌停采集
collector = LimitStocksCollector()
results = collector.collect_and_save()  # ❌ 未传入 trade_date 参数

# 第83行 - 市场情绪采集
collector = MarketSentimentCollector()
success = collector.collect_and_save()  # ❌ 未传入 trade_date 参数
```

**分析**:
- ✅ 在交易日16:00运行时：`datetime.now()` = 当天日期 = 交易日期 → **没问题**
- ❌ 在非交易日手动运行时：`datetime.now()` = 非交易日日期 → **有问题**
- ❌ 在非交易时间手动运行时：可能获取不到当天数据（因为市场还未收盘）

---

## 解决方案

### 方案A: 使用"最近交易日"逻辑（推荐）

为所有采集器添加"获取最近交易日"的工具函数，而不是直接使用 `datetime.now()`。

#### 实现示例:

```python
# app/utils/trading_date.py

import akshare as ak
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger


def get_latest_trading_date() -> str:
    """
    获取最近的交易日期（从同花顺API）

    逻辑:
    1. 使用 stock_zh_a_hist 获取任意一只股票的历史数据
    2. 取最后一条记录的日期作为最近交易日
    3. 如果失败，回退到系统当前日期

    Returns:
        最近交易日期 YYYY-MM-DD
    """
    try:
        # 使用上证指数获取最近交易日
        df = ak.stock_zh_index_daily(symbol="sh000001")

        if df is not None and not df.empty:
            latest_date = pd.to_datetime(df['date'].iloc[-1]).strftime("%Y-%m-%d")
            logger.debug(f"获取最近交易日: {latest_date}")
            return latest_date
    except Exception as e:
        logger.warning(f"获取最近交易日失败: {e}")

    # 回退方案：使用系统当前日期
    return datetime.now().strftime("%Y-%m-%d")
```

#### 修改采集器:

```python
# limit_stocks_collector.py (第305行)
from app.utils.trading_date import get_latest_trading_date

def collect_and_save(self, trade_date: Optional[str] = None) -> Dict[str, int]:
    if not trade_date:
        trade_date = get_latest_trading_date()  # ✅ 使用最近交易日
    # ...
```

```python
# market_sentiment_collector.py (第270行)
from app.utils.trading_date import get_latest_trading_date

def collect_market_sentiment(self, trade_date: Optional[str] = None) -> Dict:
    if not trade_date:
        trade_date = get_latest_trading_date()  # ✅ 使用最近交易日
    # ...
```

**优点**:
- ✅ 自动获取最近交易日，即使在周末运行也能获取周五的日期
- ✅ 与 `hot_concepts_collector` 的逻辑一致
- ✅ 避免错误的日期进入数据库

**缺点**:
- 需要额外的API调用（但可以缓存）

---

### 方案B: 在调度器中传入日期（简单但不灵活）

修改 `data_scheduler.py`，显式传入交易日期:

```python
def run_daily_collection():
    # 获取当天日期
    trade_date = datetime.now().strftime("%Y-%m-%d")

    # 传入日期参数
    results["limit_stocks"] = collect_limit_stocks(trade_date)
    results["market_sentiment"] = collect_market_sentiment(trade_date)
```

**优点**:
- 简单直接

**缺点**:
- ❌ 在非交易日运行仍然会有问题
- ❌ 需要同时修改调度器和采集器

---

## 推荐方案

**采用方案A: 使用"最近交易日"逻辑**

### 实施步骤:

1. ✅ 创建 `app/utils/trading_date.py` 工具模块
2. ✅ 实现 `get_latest_trading_date()` 函数
3. ✅ 修改 `limit_stocks_collector.py`
4. ✅ 修改 `market_sentiment_collector.py`
5. ✅ 测试采集器在非交易日的行为
6. ✅ 验证数据库中的 `trade_date` 字段正确性

---

## 测试验证

### 测试场景:

1. **交易日16:00执行** → 应该采集当天数据
2. **周六/周日执行** → 应该采集上周五的数据
3. **交易日早上执行** → 应该采集上一个交易日的数据（因为当天市场还未收盘）

### 验证命令:

```bash
# 测试涨跌停采集
python3 scripts/test-limit-stocks-collector.py

# 查询数据库验证日期
# SELECT DISTINCT trade_date FROM limit_stocks_detail ORDER BY trade_date DESC LIMIT 10;
```

---

## 总结

| 采集器 | 当前状态 | 修复方案 |
|--------|---------|---------|
| hot_concepts_collector | ✅ 正确（从API提取日期） | 无需修改 |
| market_index_collector | ✅ 正确（从API提取日期） | 无需修改 |
| limit_stocks_collector | ❌ 使用系统时间 | 改用 `get_latest_trading_date()` |
| market_sentiment_collector | ❌ 使用系统时间 | 改用 `get_latest_trading_date()` |

**核心问题**: 部分API不返回日期字段，导致只能依赖参数传入的日期，而默认使用 `datetime.now()` 在非交易日会出错。

**解决方案**: 实现 `get_latest_trading_date()` 工具函数，通过查询任意股票/指数的最新数据来获取最近交易日。
