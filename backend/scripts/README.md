# 数据采集脚本说明

## 📋 定时任务脚本

### daily_auto_collect.py - 每日自动数据采集

**功能特性：**
- ✅ 自动获取系统日期和星期，判断是否交易日
- ✅ 采集所有股票数据（大盘指数、涨停股池、市场情绪、热门概念）
- ✅ 数据完整性检查
- ✅ 失败自动重试（1小时后补全缺失数据）

**采集内容：**
1. **大盘指数** - 上证、深证、创业板（至少1条）
2. **涨停股池** - 涨停和跌停股票详细信息
3. **市场情绪** - 涨跌比、炸板率、连板分布等
4. **热门概念** - TOP50热门概念板块

**执行时间：**
- 每个交易日（周一至周五）16:00 自动执行
- 非交易日自动跳过

**执行流程：**
```
16:00 开始采集
  ↓
判断是否交易日
  ↓
采集所有数据（4个模块）
  ↓
检查数据完整性
  ↓
数据完整？
  ├─ 是 → 任务完成 ✅
  └─ 否 → 等待1小时
           ↓
       17:00 补全缺失数据
           ↓
       再次检查完整性
           ↓
       完成 ✅ / 部分失败 ⚠️
```

**日志文件：**
- 位置：`backend/logs/daily_collect_YYYYMMDD.log`
- 示例：`backend/logs/daily_collect_20251209.log`

## 🚀 手动执行

如果需要手动采集数据：

```bash
# 采集当日数据（自动判断交易日）
cd "/Users/win/Documents/ai 编程/cc/短线复盘/backend"
./venv/bin/python3 scripts/daily_auto_collect.py

# 采集指定日期数据
./venv/bin/python3 collect_date.py 2025-12-09
```

## ⏰ Crontab配置

当前定时任务：

```cron
# 短线复盘项目 - 每日数据采集（周一到周五 16:00）
0 16 * * 1-5 cd "/Users/win/Documents/ai 编程/cc/短线复盘/backend" && ./venv/bin/python3 scripts/daily_auto_collect.py >> "logs/daily_collect_$(date +\%Y\%m\%d).log" 2>&1
```

**查看定时任务：**
```bash
crontab -l
```

**编辑定时任务：**
```bash
crontab -e
```

## 📊 数据完整性标准

脚本会检查以下数据是否完整：

| 模块 | 完整性标准 | 说明 |
|------|-----------|------|
| 大盘指数 | ≥ 1 条 | 至少要有上证指数 |
| 涨停股池 | > 0 条 | 至少有涨停或跌停数据 |
| 市场情绪 | = 1 条 | 每日唯一记录 |
| 热门概念 | ≥ 10 条 | 至少10个热门概念 |

## 🔧 故障排查

### 1. 定时任务未执行

检查crontab是否正确配置：
```bash
crontab -l
```

检查日志文件：
```bash
ls -lh backend/logs/
tail -f backend/logs/daily_collect_*.log
```

### 2. 数据采集失败

**可能原因：**
- API限流（频繁调用导致）
- 网络问题
- 数据源暂时不可用

**解决方案：**
1. 等待1小时后自动重试（脚本内置）
2. 手动重新采集：
```bash
./venv/bin/python3 collect_date.py 2025-12-09
```

### 3. 深证和创业板指数缺失

**原因：** AKShare数据源更新延迟

**解决方案：**
- 代码已更新为使用东方财富接口 (`stock_zh_index_daily_em`)
- 如遇限流，等待1小时自动重试

## 📝 日志说明

**日志级别：**
- ✅ INFO - 正常信息
- ⚠️ WARNING - 警告（数据不完整）
- ❌ ERROR - 错误（采集失败）

**日志示例：**
```
2025-12-09 16:00:00 | INFO | 🎯 每日自动数据采集任务启动
2025-12-09 16:00:00 | INFO | 📅 当前日期: 2025-12-09 (周一)
2025-12-09 16:00:00 | INFO | 📊 是否交易日: 是
2025-12-09 16:00:05 | INFO | ✅ 大盘指数采集成功: 共 3 条
2025-12-09 16:00:10 | INFO | ✅ 涨跌停股池采集成功: 涨停53只, 跌停7只
2025-12-09 16:00:15 | INFO | ✅ 市场情绪采集成功
2025-12-09 16:00:20 | INFO | ✅ 热门概念采集成功: 50 个
2025-12-09 16:00:25 | INFO | ✅ 所有数据采集完整，任务完成！
```

## 🔄 API接口说明

脚本调用的采集器：

1. **MarketIndexCollector** - 大盘指数
   - API: `ak.stock_zh_index_daily_em()`
   - 包含重试机制（最多3次，指数退避）

2. **LimitStocksCollector** - 涨停股池
   - API: `ak.stock_zt_pool_em()` / `ak.stock_zt_pool_dtgc_em()`

3. **MarketSentimentCollector** - 市场情绪
   - API: 多个AKShare接口组合

4. **HotConceptsCollector** - 热门概念
   - API: `ak.stock_board_concept_name_ths()` + 个股数据

## 🔌 扩展新的数据采集模块

**重要：** `daily_auto_collect.py` 是总调度器，所有新增的数据采集API都应该纳入此脚本。

### 添加新模块的步骤：

#### 1. 创建采集器类

在 `backend/app/services/collectors/` 下创建新的采集器：

```python
# 例如：dragon_tiger_collector.py（龙虎榜采集器）
class DragonTigerCollector:
    def collect_and_save(self, trade_date: str = None):
        """采集并保存龙虎榜数据"""
        # 实现采集逻辑
        pass
```

#### 2. 在总调度脚本中导入

编辑 `scripts/daily_auto_collect.py`，添加导入：

```python
from app.services.collectors.dragon_tiger_collector import DragonTigerCollector
```

#### 3. 添加到采集函数

在 `collect_all_data()` 函数中添加新模块：

```python
def collect_all_data(trade_date: str):
    results = {
        "market_index": False,
        "limit_stocks": False,
        "market_sentiment": False,
        "hot_concepts": False,
        "dragon_tiger": False,  # 新增模块
    }

    # ... 现有采集代码 ...

    # 5. 采集龙虎榜（新增）
    try:
        logger.info("\n🐉 [5/5] 采集龙虎榜...")
        collector = DragonTigerCollector()
        count = collector.collect_and_save(trade_date=trade_date)

        if count > 0:
            logger.info(f"✅ 龙虎榜采集成功: {count} 条")
            results["dragon_tiger"] = True
        else:
            logger.warning("⚠️ 龙虎榜采集失败: 无数据")
    except Exception as e:
        logger.error(f"❌ 龙虎榜采集失败: {str(e)}")

    return results
```

#### 4. 添加完整性检查

在 `check_data_completeness()` 函数中添加检查：

```python
def check_data_completeness(trade_date: str):
    # ... 现有检查代码 ...

    # 5. 检查龙虎榜（新增）
    response = supabase.table("dragon_tiger").select("*", count="exact").eq("trade_date", trade_date).execute()
    count = response.count if response.count else 0
    results["dragon_tiger"] = (count > 0, count)
    logger.info(f"  龙虎榜: {count} 条 {'✅' if count > 0 else '❌ 缺失'}")

    return results
```

#### 5. 添加补全逻辑

在 `collect_missing_data()` 函数中添加补全：

```python
def collect_missing_data(trade_date: str, completeness_check: dict):
    # ... 现有补全代码 ...

    elif module == "dragon_tiger":
        collector = DragonTigerCollector()
        count = collector.collect_and_save(trade_date=trade_date)
        results[module] = count > 0
        logger.info(f"  {'✅ 补全成功' if results[module] else '❌ 补全失败'}: {count} 条")

    return results
```

### 示例：完整的新模块添加

假设要添加"个股异动"采集模块：

```python
# 1. 创建采集器
# backend/app/services/collectors/stock_change_collector.py
class StockChangeCollector:
    def collect_and_save(self, trade_date: str = None):
        """采集个股异动数据"""
        # 采集逻辑...
        return count

# 2. 在总调度中注册（只需在3个函数中添加）
# scripts/daily_auto_collect.py

# ① collect_all_data() - 添加采集逻辑
results["stock_change"] = False  # 初始化
# ... 采集代码 ...

# ② check_data_completeness() - 添加检查逻辑
results["stock_change"] = (count > 0, count)

# ③ collect_missing_data() - 添加补全逻辑
elif module == "stock_change":
    # ... 补全代码 ...
```

### 自动化测试新模块

添加新模块后，手动测试：

```bash
# 测试采集
cd "/Users/win/Documents/ai 编程/cc/短线复盘/backend"
./venv/bin/python3 scripts/daily_auto_collect.py

# 或者只测试新模块
./venv/bin/python3 -c "
from app.services.collectors.dragon_tiger_collector import DragonTigerCollector
collector = DragonTigerCollector()
result = collector.collect_and_save('2025-12-09')
print(f'采集结果: {result}')
"
```

---

## 💡 最佳实践

1. **定期检查日志**
   ```bash
   # 查看最新日志
   tail -n 100 backend/logs/daily_collect_$(date +%Y%m%d).log
   ```

2. **数据验证**
   - 登录前端查看数据
   - 或通过API验证：`http://localhost:8000/api/concepts/hot`

3. **备份数据**
   - Supabase自动备份
   - 建议定期导出重要数据

4. **模块化原则**
   - 每个采集器独立成类
   - 统一通过总调度管理
   - 新增模块遵循同样的模式

## 📞 问题反馈

如遇问题，请检查：
1. 日志文件内容
2. Crontab配置是否正确
3. 虚拟环境是否激活
4. 数据库连接是否正常

---

**更新日期：** 2025-12-09
**版本：** v1.0
**维护者：** 短线复盘项目
