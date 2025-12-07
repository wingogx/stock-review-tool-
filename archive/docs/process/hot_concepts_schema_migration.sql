-- ============================================================
-- hot_concepts 表结构优化 SQL 脚本
-- 用途: 移除未使用的龙头股相关字段
-- 执行位置: Supabase SQL Editor
-- ============================================================

-- 方案A: 删除旧表，创建新表（适合测试环境，数据可丢失）
-- 注意: 使用此方案会丢失所有现有数据！

-- 删除旧表
DROP TABLE IF EXISTS hot_concepts;

-- 创建新表
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

-- 创建索引
CREATE INDEX idx_hot_concepts_trade_date ON hot_concepts(trade_date DESC);
CREATE INDEX idx_hot_concepts_rank ON hot_concepts(trade_date, rank);

-- 添加表注释
COMMENT ON TABLE hot_concepts IS '热门概念板块数据（基于5个交易日累计涨幅）';
COMMENT ON COLUMN hot_concepts.trade_date IS '实际交易日期（从API数据中提取）';
COMMENT ON COLUMN hot_concepts.concept_name IS '概念板块名称';
COMMENT ON COLUMN hot_concepts.change_pct IS '5个交易日累计涨幅（百分比）';
COMMENT ON COLUMN hot_concepts.concept_strength IS '概念强度（更精确的涨幅值）';
COMMENT ON COLUMN hot_concepts.rank IS '排名（基于5日累计涨幅降序）';


-- ============================================================
-- 方案B: 保留旧表数据，删除列（适合生产环境，保留数据）
-- 注意: 使用此方案会保留现有数据，但删除未使用的列
-- ============================================================

/*
-- 删除未使用的列
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

-- 添加表注释
COMMENT ON TABLE hot_concepts IS '热门概念板块数据（基于5个交易日累计涨幅）';
COMMENT ON COLUMN hot_concepts.trade_date IS '实际交易日期（从API数据中提取）';
COMMENT ON COLUMN hot_concepts.concept_name IS '概念板块名称';
COMMENT ON COLUMN hot_concepts.change_pct IS '5个交易日累计涨幅（百分比）';
COMMENT ON COLUMN hot_concepts.concept_strength IS '概念强度（更精确的涨幅值）';
COMMENT ON COLUMN hot_concepts.rank IS '排名（基于5日累计涨幅降序）';
*/

-- ============================================================
-- 验证表结构
-- ============================================================

-- 查看表结构
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'hot_concepts'
-- ORDER BY ordinal_position;

-- 查看索引
-- SELECT indexname, indexdef
-- FROM pg_indexes
-- WHERE tablename = 'hot_concepts';
