-- ============================================================
-- hot_concepts 表完全重建脚本
-- 用途: 删除旧表及所有历史数据，创建优化后的新表结构
-- 执行位置: Supabase SQL Editor
-- 警告: 此操作将删除所有历史数据，不可恢复！
-- ============================================================

-- 第一步：删除旧表（包括所有数据）
DROP TABLE IF EXISTS hot_concepts CASCADE;

-- 第二步：创建优化后的新表
CREATE TABLE hot_concepts (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    concept_name TEXT NOT NULL,
    change_pct NUMERIC(10, 2) NOT NULL,
    concept_strength NUMERIC(10, 4) NOT NULL,
    rank INTEGER NOT NULL,
    is_new_concept BOOLEAN NOT NULL DEFAULT false,
    first_seen_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (trade_date, concept_name)
);

-- 第三步：创建索引（提升查询性能）
CREATE INDEX idx_hot_concepts_trade_date ON hot_concepts(trade_date DESC);
CREATE INDEX idx_hot_concepts_rank ON hot_concepts(trade_date, rank);
CREATE INDEX idx_hot_concepts_new_concepts ON hot_concepts(trade_date, is_new_concept) WHERE is_new_concept = true;

-- 第四步：添加表和字段注释（便于理解）
COMMENT ON TABLE hot_concepts IS '热门概念板块数据（基于5个交易日累计涨幅）';
COMMENT ON COLUMN hot_concepts.id IS '主键ID';
COMMENT ON COLUMN hot_concepts.trade_date IS '实际交易日期（从API数据中提取，非系统当前日期）';
COMMENT ON COLUMN hot_concepts.concept_name IS '概念板块名称（同花顺）';
COMMENT ON COLUMN hot_concepts.change_pct IS '5个交易日累计涨幅（百分比，如 2.83 表示 2.83%）';
COMMENT ON COLUMN hot_concepts.concept_strength IS '概念强度（更精确的涨幅值，如 2.8345）';
COMMENT ON COLUMN hot_concepts.rank IS '排名（基于5日累计涨幅降序，1为涨幅最大）';
COMMENT ON COLUMN hot_concepts.is_new_concept IS '是否为新概念（首次出现距今≤7天的概念）';
COMMENT ON COLUMN hot_concepts.first_seen_date IS '该概念首次出现在同花顺API的日期';
COMMENT ON COLUMN hot_concepts.created_at IS '记录创建时间';
COMMENT ON COLUMN hot_concepts.updated_at IS '记录更新时间';

-- 第五步：验证表结构
SELECT
    column_name AS "字段名",
    data_type AS "数据类型",
    is_nullable AS "允许空值",
    column_default AS "默认值"
FROM information_schema.columns
WHERE table_name = 'hot_concepts'
ORDER BY ordinal_position;

-- 第六步：验证索引
SELECT
    indexname AS "索引名",
    indexdef AS "索引定义"
FROM pg_indexes
WHERE tablename = 'hot_concepts';
