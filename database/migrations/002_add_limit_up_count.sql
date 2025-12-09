-- ============================================
-- 迁移: 为 hot_concepts 表添加涨停股数量字段
-- 版本: 002
-- 创建日期: 2025-12-09
-- ============================================

-- 添加涨停股数量字段
ALTER TABLE hot_concepts
ADD COLUMN IF NOT EXISTS limit_up_count INT;

-- 添加成分股总数字段
ALTER TABLE hot_concepts
ADD COLUMN IF NOT EXISTS total_count INT;

-- 添加注释
COMMENT ON COLUMN hot_concepts.limit_up_count IS '该概念今日涨停股数量';
COMMENT ON COLUMN hot_concepts.total_count IS '该概念成分股总数';

-- 创建索引（可选，用于按涨停数排序）
CREATE INDEX IF NOT EXISTS idx_hot_concepts_limit_up_count
ON hot_concepts(limit_up_count DESC NULLS LAST);
