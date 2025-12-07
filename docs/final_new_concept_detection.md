# 基于首次出现日期的新概念识别（最终方案）

## 核心改进

从"历史数据长度判断"升级到"首次出现日期判断"，确保不遗漏任何新概念。

## 最终判断逻辑

### 新概念的精准定义

**新概念** = 首次出现在同花顺API的日期距今 **≤ 7天** 的概念

### 判断流程

```python
1. 查询数据库：该概念是否存在 first_seen_date？

2. 如果不存在（first_seen_date = None）：
   → 这是全新概念！
   → 设置 first_seen_date = 今天
   → is_new_concept = True
   → 日志：🆕 发现全新概念

3. 如果存在：
   → 计算：天数 = 今天 - first_seen_date
   → 判断：天数 ≤ 7？
      ├─ 是 → is_new_concept = True
      │        日志：🆕 新概念 (出现第X天)
      └─ 否 → is_new_concept = False
               (成熟概念，不再显示为"新")
```

## 实例演示

### 场景：AI+机器人概念首次出现

**12月10日（周二）**
- 同花顺新增"AI+机器人"概念
- 系统采集时查询数据库：`first_seen_date = None`
- 判断：全新概念 ✅
- 保存：`first_seen_date = 2025-12-10`, `is_new_concept = true`
- 日志：`🆕 发现全新概念: AI+机器人 (2个交易日数据，涨幅: 28.50%)`

**12月11日（周三）**
- 系统再次采集"AI+机器人"
- 查询数据库：`first_seen_date = 2025-12-10`
- 计算天数：12月11日 - 12月10日 = 1天
- 判断：1天 ≤ 7天 → 仍是新概念 ✅
- 保存：`is_new_concept = true` (first_seen_date不变)
- 日志：`🆕 新概念: AI+机器人 (出现第2天，涨幅: 35.20%)`

**12月17日（周二，第8天）**
- 计算天数：12月17日 - 12月10日 = 7天
- 判断：7天 ≤ 7天 → 仍是新概念 ✅
- 日志：`🆕 新概念: AI+机器人 (出现第8天，涨幅: 42.10%)`

**12月18日（周三，第9天）**
- 计算天数：12月18日 - 12月10日 = 8天
- 判断：8天 > 7天 → 不再是新概念 ❌
- 保存：`is_new_concept = false`
- 不再显示 🆕 标记

## 数据库表结构（最终版）

```sql
CREATE TABLE hot_concepts (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    concept_name TEXT NOT NULL,
    change_pct NUMERIC(10, 2) NOT NULL,
    concept_strength NUMERIC(10, 4) NOT NULL,
    rank INTEGER NOT NULL,
    is_new_concept BOOLEAN NOT NULL DEFAULT false,  -- 是否为新概念（≤7天）
    first_seen_date DATE,                           -- 🆕 首次出现日期
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (trade_date, concept_name)
);
```

## 代码实现

### 关键方法：get_first_seen_date()

```python
def get_first_seen_date(self, concept_name: str) -> Optional[str]:
    """查询概念的首次出现日期"""
    try:
        response = self.supabase.table("hot_concepts")\
            .select("first_seen_date")\
            .eq("concept_name", concept_name)\
            .not_.is_("first_seen_date", "null")\
            .order("first_seen_date")\
            .limit(1)\
            .execute()

        if response.data and len(response.data) > 0:
            return response.data[0]['first_seen_date']

        return None
    except Exception as e:
        logger.debug(f"查询首次出现日期失败: {concept_name}, {str(e)}")
        return None
```

### 核心判断逻辑

```python
# 判断是否为新概念（基于首次出现日期）
first_seen = self.get_first_seen_date(concept_name)

if first_seen is None:
    # 数据库中不存在 → 真正的新概念
    is_new_concept = True
    first_seen_date = actual_trade_date  # 今天是首次出现
    logger.info(f"🆕 发现全新概念: {concept_name}")
else:
    # 已存在，判断首次出现距今天数
    first_seen_date = first_seen
    days_since_first_seen = (今天 - first_seen日期).days

    # 如果首次出现距今 ≤ 7天，仍然是新概念
    is_new_concept = days_since_first_seen <= 7

    if is_new_concept:
        logger.info(f"🆕 新概念: {concept_name} (出现第{days_since_first_seen + 1}天)")
```

## 优势对比

### 旧逻辑（历史数据长度）

```python
is_new_concept = len(last_5_days) < 5
```

**问题：**
- ❌ 12月10日：AI+机器人（2天数据）→ 新概念 ✅
- ❌ 12月13日：AI+机器人（5天数据）→ **不再是新概念**  ← 错误！
- ❌ 无法识别"真正首次出现"vs"数据缺失"

### 新逻辑（首次出现日期）

```python
is_new_concept = (今天 - first_seen_date).days <= 7
```

**优势：**
- ✅ 12月10日：AI+机器人（首次出现）→ 新概念 ✅
- ✅ 12月13日：AI+机器人（第4天）→ **仍是新概念** ✅
- ✅ 12月17日：AI+机器人（第8天）→ 不再是新概念 ✅
- ✅ 准确区分"新增概念"vs"老概念数据缺失"

## 日志示例

```
10:23:15 | INFO | 开始采集 2025-12-10 热门概念板块数据...
10:23:15 | INFO | 获取所有概念板块列表（同花顺）...
10:23:16 | INFO | 成功获取概念板块列表，共 374 个概念
10:23:16 | INFO | 开始处理 374 个概念板块...
10:23:18 | INFO | 🆕 发现全新概念: AI+机器人 (2个交易日数据，涨幅: 28.50%)
10:23:22 | INFO | 🆕 新概念: 量子通信 (出现第3天，涨幅: 15.20%)
10:24:01 | INFO | 成功采集 50 个热门概念板块（交易日: 2025-12-10，按累计涨幅排序）
10:24:01 | INFO | 🆕 其中包含 2 个新概念（首次出现≤7天）
10:24:01 | INFO |   [1] 人工智能: 涨幅 10.23%
10:24:01 | INFO |   [2] AI+机器人: 涨幅 28.50% 🆕
10:24:01 | INFO |   [3] 芯片: 涨幅 8.76%
10:24:01 | INFO |   [4] 量子通信: 涨幅 15.20% 🆕
10:24:01 | INFO |   [5] 新能源: 涨幅 7.45%
```

## 前端查询示例

### 查询所有热门概念

```sql
SELECT *
FROM hot_concepts
WHERE trade_date = '2025-12-10'
ORDER BY rank;
```

### 仅查询新概念（单独列出）

```sql
SELECT
    concept_name,
    change_pct,
    first_seen_date,
    CURRENT_DATE - first_seen_date AS days_since_first_seen
FROM hot_concepts
WHERE trade_date = '2025-12-10'
  AND is_new_concept = true
ORDER BY rank;
```

返回：

```
concept_name | change_pct | first_seen_date | days_since_first_seen
-------------+------------+-----------------+----------------------
AI+机器人    |      28.50 | 2025-12-10      |                     0  (首次出现)
量子通信     |      15.20 | 2025-12-08      |                     2  (第3天)
```

### 查询即将"毕业"的新概念（第6-7天）

```sql
SELECT
    concept_name,
    first_seen_date,
    CURRENT_DATE - first_seen_date + 1 AS day_number
FROM hot_concepts
WHERE trade_date = CURRENT_DATE
  AND is_new_concept = true
  AND CURRENT_DATE - first_seen_date >= 6
ORDER BY first_seen_date;
```

## 执行步骤

### 1. 在 Supabase 中执行表重建

```bash
docs/rebuild_hot_concepts_table.sql
```

### 2. 验证表结构

```sql
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'hot_concepts'
ORDER BY ordinal_position;
```

应该看到 `first_seen_date` 字段 ✅

### 3. 重新采集数据

```bash
cd backend
source venv/bin/activate
python3 ../scripts/collect-full-hot-concepts.py
```

### 4. 验证新概念识别

```sql
-- 查看所有新概念
SELECT
    concept_name,
    change_pct,
    is_new_concept,
    first_seen_date,
    CURRENT_DATE - first_seen_date + 1 AS day_number
FROM hot_concepts
WHERE trade_date = (SELECT MAX(trade_date) FROM hot_concepts)
  AND is_new_concept = true
ORDER BY rank;
```

## 总结

### 解决的问题

✅ **当天识别**：新概念第一次出现时立即标记
✅ **持续展示**：新概念在7天内持续显示为"新"
✅ **不会遗漏**：每个概念都有明确的首次出现日期记录
✅ **准确判断**：真正区分"新增概念"vs"老概念数据缺失"

### 新增字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `first_seen_date` | DATE | 该概念首次出现在同花顺API的日期 |

### 判断标准

```
is_new_concept = (今天 - first_seen_date).days ≤ 7
```

### 前端展示建议

```
🆕 新概念板块（本周新增）
━━━━━━━━━━━━━━━━━━━━━━━━━
1. AI+机器人       +28.50%  (首次出现)
2. 量子通信         +15.20%  (第3天)
```

这样就完美满足了您的需求：**有新概念板块出现，当天就要展示出来，不要遗漏！**
