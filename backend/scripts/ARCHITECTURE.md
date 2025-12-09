# 数据采集架构设计

## 🏗️ 总调度器架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Crontab 定时任务                         │
│                  周一至周五 16:00 触发                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│            daily_auto_collect.py (总调度器)                  │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  1. 获取系统日期 & 判断交易日                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  2. 采集所有模块数据                                 │   │
│  │     ├─ market_index     (大盘指数)                  │   │
│  │     ├─ limit_stocks     (涨停股池)                  │   │
│  │     ├─ market_sentiment (市场情绪)                  │   │
│  │     ├─ hot_concepts     (热门概念)                  │   │
│  │     └─ [future_module]  (未来扩展)                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  3. 检查数据完整性                                   │   │
│  │     ├─ 验证各模块数据量                             │   │
│  │     └─ 生成完整性报告                               │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                   │
│                ┌─────────┴─────────┐                        │
│                ▼                   ▼                        │
│  ┌──────────────────┐   ┌──────────────────┐              │
│  │  数据完整 ✅      │   │  数据不完整 ⚠️    │              │
│  │  任务完成         │   │  等待1小时        │              │
│  └──────────────────┘   └─────┬────────────┘              │
│                                 │                            │
│                                 ▼                            │
│                    ┌──────────────────────┐                │
│                    │  4. 补全缺失数据      │                │
│                    │     只采集缺失模块    │                │
│                    └──────────┬───────────┘                │
│                               │                              │
│                               ▼                              │
│                    ┌──────────────────────┐                │
│                    │  5. 最终验证          │                │
│                    │     完成/部分失败     │                │
│                    └──────────────────────┘                │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌──────────────────────┐
              │   日志文件输出        │
              │   logs/daily_collect_ │
              │   YYYYMMDD.log        │
              └──────────────────────┘
```

---

## 📦 模块化设计

### 当前采集模块（4个）

```
backend/app/services/collectors/
├── market_index_collector.py      # 大盘指数
├── limit_stocks_collector.py      # 涨停股池
├── market_sentiment_collector.py  # 市场情绪
└── hot_concepts_collector.py      # 热门概念
```

### 未来扩展模块（示例）

```
backend/app/services/collectors/
├── dragon_tiger_collector.py      # 龙虎榜
├── stock_change_collector.py      # 个股异动
├── block_trade_collector.py       # 大宗交易
└── [your_module]_collector.py     # 您的新模块
```

---

## 🔄 数据流向

```
AKShare API
    │
    ▼
采集器 Collectors
(market_index, limit_stocks, etc.)
    │
    ▼
数据处理 & 清洗
    │
    ▼
Supabase 数据库
(market_index, limit_stocks_detail, etc.)
    │
    ▼
FastAPI 后端
(/api/market/index, /api/limit/stocks, etc.)
    │
    ▼
Next.js 前端
(数据展示 & 可视化)
```

---

## 🧩 添加新模块的核心接口

每个采集器必须实现：

```python
class YourCollector:
    def __init__(self):
        """初始化，连接数据库等"""
        pass

    def collect_and_save(self, trade_date: str = None) -> int:
        """
        采集并保存数据

        Args:
            trade_date: 交易日期 YYYY-MM-DD

        Returns:
            int: 成功保存的记录数

        必须实现此方法！
        """
        pass
```

总调度器调用流程：

```python
# 1. 导入
from app.services.collectors.your_collector import YourCollector

# 2. 实例化
collector = YourCollector()

# 3. 调用
count = collector.collect_and_save(trade_date="2025-12-09")

# 4. 验证
success = count > 0
```

---

## 📊 数据完整性标准

每个模块必须定义完整性标准：

| 模块 | 表名 | 完整性条件 | 示例 |
|------|------|-----------|------|
| market_index | market_index | count >= 1 | 至少1条（上证） |
| limit_stocks | limit_stocks_detail | count > 0 | 至少有涨停或跌停数据 |
| market_sentiment | market_sentiment | count == 1 | 每日唯一记录 |
| hot_concepts | hot_concepts | count >= 10 | 至少10个概念 |
| **[新模块]** | **[表名]** | **[条件]** | **[说明]** |

添加新模块时，在 `check_data_completeness()` 函数中定义检查逻辑。

---

## ⚙️ 重试机制

```
16:00 首次采集
    │
    ▼
┌─────────┐
│ 采集失败 │ ──┐
└─────────┘   │
              │ 等待1小时
              │
17:00 重试    │
    ▲         │
    └─────────┘
    │
    ▼
┌─────────┐
│ 仍失败？ │ ──> 记录日志，人工介入
└─────────┘
```

**重试策略：**
- ✅ 只重试缺失的模块
- ✅ 不重复采集已完整的数据
- ✅ 每个模块独立重试（互不影响）
- ✅ 最多重试1次（避免无限循环）

---

## 🔐 错误处理

### 采集器级别

```python
try:
    # 采集数据
    data = fetch_from_api()
except ConnectionError:
    # 网络错误 - 可重试
    logger.error("网络连接失败")
except ValueError:
    # 数据格式错误 - 不可重试
    logger.error("数据格式异常")
except Exception as e:
    # 未知错误
    logger.error(f"未知错误: {str(e)}")
```

### 总调度级别

```python
# 单个模块失败不影响其他模块
for module in modules:
    try:
        collect_module(module)
    except Exception:
        # 记录失败，继续执行其他模块
        logger.error(f"模块 {module} 失败")
        continue
```

---

## 📈 性能优化

### API调用优化

```python
# ✅ 好的做法
time.sleep(2)  # 每个请求间隔2秒
retry_with_backoff(max_retries=3)  # 指数退避

# ❌ 避免
while True:  # 无限重试
    api_call()  # 无延迟
```

### 并发控制

```python
# 当前：顺序执行（安全）
for module in modules:
    collect(module)

# 未来：可考虑并发（需测试API限制）
with ThreadPoolExecutor(max_workers=2) as executor:
    executor.map(collect, modules)
```

---

## 🎯 设计原则

1. **模块化** - 每个采集器独立，职责单一
2. **可扩展** - 新增模块只需3步（创建、注册、测试）
3. **容错性** - 单个模块失败不影响整体
4. **幂等性** - 重复执行不会产生重复数据
5. **可观测** - 详细日志，便于排查问题
6. **自动化** - 无需人工干预，自动重试补全

---

## 🚀 未来规划

### Phase 1（当前）
- ✅ 大盘指数
- ✅ 涨停股池
- ✅ 市场情绪
- ✅ 热门概念

### Phase 2（计划中）
- 🔲 龙虎榜数据
- 🔲 个股异动
- 🔲 大宗交易
- 🔲 资金流向

### Phase 3（可选）
- 🔲 新闻舆情
- 🔲 财报数据
- 🔲 研报推荐
- 🔲 AI预测模型

---

## 📝 维护清单

定期检查：

- [ ] 日志文件大小（定期清理）
- [ ] API调用成功率
- [ ] 数据完整性趋势
- [ ] 磁盘空间使用
- [ ] Supabase配额

每月审查：

- [ ] 采集器性能
- [ ] 新增数据需求
- [ ] API接口变更
- [ ] 优化机会

---

**版本：** v1.0
**更新日期：** 2025-12-09
**设计者：** 短线复盘项目团队
