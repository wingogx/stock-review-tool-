# hot_concepts 数据库表优化总结

## 优化完成时间
2025-12-08

## 优化背景
由于移除了龙头股功能（数据源不兼容），当前表中存在大量始终为 NULL 或空值的字段，导致：
- 数据库存储空间浪费
- API 返回数据冗余
- 代码维护困难

## 已完成的代码优化

### 1. 更新了 `hot_concepts_collector.py`

#### 删除的代码：
- ✅ 移除 `json` 导入（不再需要）
- ✅ 删除 `get_limit_up_stocks()` 方法（用于获取涨停股池）
- ✅ 删除 `extract_leading_stocks_from_limit_up()` 方法（用于提取龙头股）
- ✅ 移除 `save_to_database()` 中的 leading_stocks 转换逻辑

#### 精简的数据结构：
**优化前：**
```python
concept_data = {
    "trade_date": actual_trade_date,
    "concept_name": concept_name,
    "change_pct": round(total_change_pct, 2),
    "stock_count": None,         # ❌ 未使用
    "up_count": None,            # ❌ 未使用
    "down_count": None,          # ❌ 未使用
    "limit_up_count": None,      # ❌ 未使用
    "leading_stocks": [],        # ❌ 未使用
    "concept_strength": round(concept_strength, 4),
    "rank": 0,
}
```

**优化后：**
```python
concept_data = {
    "trade_date": actual_trade_date,
    "concept_name": concept_name,
    "change_pct": round(total_change_pct, 2),
    "concept_strength": round(concept_strength, 4),
    "rank": 0,
}
```

#### 更新的文档：
- ✅ 更新模块 docstring，移除龙头股相关说明
- ✅ 更新类 docstring
- ✅ 更新方法 docstring，添加返回值说明

### 2. 创建的文档

- ✅ `database-optimization.md` - 完整的优化方案文档
- ✅ `hot_concepts_schema_migration.sql` - 数据库表结构迁移 SQL 脚本
- ✅ `hot_concepts_optimization_summary.md` - 本优化总结文档

## 待执行的数据库迁移

### 需要在 Supabase 中执行 SQL

**推荐方案（测试环境）：**
```sql
-- 删除旧表，创建新表（会丢失现有数据）
DROP TABLE IF EXISTS hot_concepts;

CREATE TABLE hot_concepts (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    concept_name TEXT NOT NULL,
    change_pct NUMERIC(10, 2) NOT NULL,
    concept_strength NUMERIC(10, 4) NOT NULL,
    rank INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (trade_date, concept_name)
);

CREATE INDEX idx_hot_concepts_trade_date ON hot_concepts(trade_date DESC);
CREATE INDEX idx_hot_concepts_rank ON hot_concepts(trade_date, rank);
```

**生产环境方案（保留数据）：**
```sql
-- 删除未使用的列（保留现有数据）
ALTER TABLE hot_concepts DROP COLUMN IF EXISTS stock_count;
ALTER TABLE hot_concepts DROP COLUMN IF EXISTS up_count;
ALTER TABLE hot_concepts DROP COLUMN IF EXISTS down_count;
ALTER TABLE hot_concepts DROP COLUMN IF EXISTS limit_up_count;
ALTER TABLE hot_concepts DROP COLUMN IF EXISTS leading_stocks;

-- 添加 NOT NULL 约束
ALTER TABLE hot_concepts ALTER COLUMN change_pct SET NOT NULL;
ALTER TABLE hot_concepts ALTER COLUMN concept_strength SET NOT NULL;
ALTER TABLE hot_concepts ALTER COLUMN rank SET NOT NULL;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_hot_concepts_trade_date ON hot_concepts(trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_hot_concepts_rank ON hot_concepts(trade_date, rank);
```

详细 SQL 脚本见：`docs/hot_concepts_schema_migration.sql`

## 优化后的表结构

### 字段列表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PRIMARY KEY | 主键 |
| trade_date | DATE | NOT NULL | 实际交易日期 |
| concept_name | TEXT | NOT NULL | 概念板块名称 |
| change_pct | NUMERIC(10,2) | NOT NULL | 5个交易日累计涨幅（%） |
| concept_strength | NUMERIC(10,4) | NOT NULL | 概念强度（精确涨幅值） |
| rank | INTEGER | NOT NULL | 排名 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新时间 |

### 索引

- `PRIMARY KEY (id)` - 主键索引
- `UNIQUE (trade_date, concept_name)` - 唯一约束，防止重复
- `idx_hot_concepts_trade_date` - 按交易日期降序
- `idx_hot_concepts_rank` - 按交易日期和排名

## 优化效果

### 存储空间
- **优化前**：13 个字段（5 个字段始终为 NULL/空）
- **优化后**：8 个字段（全部有效）
- **节省**：~38% 的字段数

### API 性能
- 减少数据传输量（移除5个空字段）
- 简化 JSON 序列化（不需要处理 leading_stocks 数组）

### 代码质量
- 删除 ~130 行未使用代码
- 简化数据结构
- 提高可维护性

## 后续步骤

1. **执行数据库迁移**
   - 在 Supabase SQL Editor 中执行迁移脚本
   - 验证表结构正确

2. **重新采集完整数据**
   ```bash
   cd backend
   source venv/bin/activate
   python3 -c "from app.services.collectors.hot_concepts_collector import collect_hot_concepts; collect_hot_concepts(top_n=50)"
   ```

3. **验证数据正确性**
   - 检查字段是否齐全
   - 验证数据类型
   - 确认索引已创建

## 相关文件

- 代码文件：`backend/app/services/collectors/hot_concepts_collector.py`
- 优化方案：`docs/database-optimization.md`
- SQL 脚本：`docs/hot_concepts_schema_migration.sql`
- 测试脚本：`scripts/test-5day-concepts.py`
