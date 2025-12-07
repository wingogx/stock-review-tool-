# hot_concepts 表结构优化方案

## 优化背景

由于移除了龙头股功能，当前表中存在大量始终为 NULL 或空值的字段，需要清理优化。

## 当前表结构（优化前）

```sql
CREATE TABLE hot_concepts (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    concept_name TEXT NOT NULL,
    change_pct NUMERIC(10, 2),              -- 5个交易日累计涨幅
    stock_count INTEGER,                    -- ❌ 未使用（龙头股功能已移除）
    up_count INTEGER,                       -- ❌ 未使用（龙头股功能已移除）
    down_count INTEGER,                     -- ❌ 未使用（龙头股功能已移除）
    limit_up_count INTEGER,                 -- ❌ 未使用（龙头股功能已移除）
    leading_stocks TEXT[],                  -- ❌ 未使用（龙头股功能已移除）
    concept_strength NUMERIC(10, 4),        -- 概念强度（精确涨幅）
    rank INTEGER,                           -- 排名
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (trade_date, concept_name)
);
```

## 优化后表结构

```sql
CREATE TABLE hot_concepts (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,               -- 实际交易日期
    concept_name TEXT NOT NULL,             -- 概念名称
    change_pct NUMERIC(10, 2) NOT NULL,     -- 5个交易日累计涨幅（百分比）
    concept_strength NUMERIC(10, 4) NOT NULL, -- 概念强度（更精确的涨幅值）
    rank INTEGER NOT NULL,                  -- 排名（按5日累计涨幅）
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (trade_date, concept_name)
);

-- 索引
CREATE INDEX idx_hot_concepts_trade_date ON hot_concepts(trade_date DESC);
CREATE INDEX idx_hot_concepts_rank ON hot_concepts(trade_date, rank);
```

## 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| trade_date | DATE | 实际交易日期（从API数据中提取） |
| concept_name | TEXT | 概念板块名称 |
| change_pct | NUMERIC(10,2) | 5个交易日累计涨幅（百分比，如 2.83） |
| concept_strength | NUMERIC(10,4) | 概念强度（更精确的涨幅值，如 2.8345） |
| rank | INTEGER | 排名（基于5日累计涨幅降序） |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

## 移除的字段

- `stock_count`: 成分股总数（龙头股功能已移除）
- `up_count`: 上涨股票数（龙头股功能已移除）
- `down_count`: 下跌股票数（龙头股功能已移除）
- `limit_up_count`: 涨停股票数（龙头股功能已移除）
- `leading_stocks`: 龙头股列表（龙头股功能已移除）

## 执行步骤

### 1. 在 Supabase 中执行表结构变更

```sql
-- 方案A: 删除旧表，创建新表（适合测试环境，数据可丢失）
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

-- 方案B: 保留旧表数据，删除列（适合生产环境，保留数据）
ALTER TABLE hot_concepts DROP COLUMN IF EXISTS stock_count;
ALTER TABLE hot_concepts DROP COLUMN IF EXISTS up_count;
ALTER TABLE hot_concepts DROP COLUMN IF EXISTS down_count;
ALTER TABLE hot_concepts DROP COLUMN IF EXISTS limit_up_count;
ALTER TABLE hot_concepts DROP COLUMN IF EXISTS leading_stocks;

-- 添加 NOT NULL 约束（如果还没有）
ALTER TABLE hot_concepts ALTER COLUMN change_pct SET NOT NULL;
ALTER TABLE hot_concepts ALTER COLUMN concept_strength SET NOT NULL;
ALTER TABLE hot_concepts ALTER COLUMN rank SET NOT NULL;

-- 创建索引（如果还没有）
CREATE INDEX IF NOT EXISTS idx_hot_concepts_trade_date ON hot_concepts(trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_hot_concepts_rank ON hot_concepts(trade_date, rank);
```

### 2. 更新 Python 代码

已在 `hot_concepts_collector.py` 中更新，移除未使用字段的赋值。

### 3. 重新采集完整数据

```bash
cd backend
source venv/bin/activate
python3 ../scripts/test-5day-concepts.py  # 采集前10个测试
# 或
python3 -c "from app.services.collectors.hot_concepts_collector import collect_hot_concepts; collect_hot_concepts(top_n=50)"  # 采集完整50个
```

## 优化效果

- 减少存储空间（移除5个未使用字段）
- 提高查询性能（减少返回数据量）
- 简化数据模型（只保留核心字段）
- 提升代码可维护性（去除冗余逻辑）
