-- ============================================
-- 热门概念板块表字段回滚脚本
-- ============================================
-- 创建日期: 2025-12-09
-- 目的: 回滚 add_hot_concepts_fields.sql 添加的字段
--
-- ⚠️ 警告: 执行此脚本将删除以下字段及其数据:
-- - day_change_pct
-- - consecutive_days
-- - concept_strength
-- - is_new_concept
-- - first_seen_date
-- ============================================

-- 开始事务
BEGIN;

-- 1. 删除索引
DROP INDEX IF EXISTS idx_hot_concepts_consecutive_days;
DROP INDEX IF EXISTS idx_hot_concepts_is_new_concept;
DROP INDEX IF EXISTS idx_hot_concepts_first_seen_date;

-- 2. 删除字段
ALTER TABLE hot_concepts DROP COLUMN IF EXISTS day_change_pct;
ALTER TABLE hot_concepts DROP COLUMN IF EXISTS consecutive_days;
ALTER TABLE hot_concepts DROP COLUMN IF EXISTS concept_strength;
ALTER TABLE hot_concepts DROP COLUMN IF EXISTS is_new_concept;
ALTER TABLE hot_concepts DROP COLUMN IF EXISTS first_seen_date;

-- 提交事务
COMMIT;

-- ============================================
-- 验证脚本
-- ============================================
-- 执行以下查询验证字段是否成功删除：
--
-- SELECT column_name, data_type
-- FROM information_schema.columns
-- WHERE table_name = 'hot_concepts'
-- ORDER BY ordinal_position;
--
-- 预期结果不应包含已删除的字段
