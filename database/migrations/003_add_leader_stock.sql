-- ============================================
-- 迁移: 为 hot_concepts 表添加龙头股字段
-- 版本: 003
-- 创建日期: 2025-12-09
-- ============================================

-- 添加龙头股代码字段
ALTER TABLE hot_concepts
ADD COLUMN IF NOT EXISTS leader_stock_code VARCHAR(20);

-- 添加龙头股名称字段
ALTER TABLE hot_concepts
ADD COLUMN IF NOT EXISTS leader_stock_name VARCHAR(50);

-- 添加龙头股连板数字段
ALTER TABLE hot_concepts
ADD COLUMN IF NOT EXISTS leader_continuous_days INT;

-- 添加龙头股当日涨幅字段
ALTER TABLE hot_concepts
ADD COLUMN IF NOT EXISTS leader_change_pct DECIMAL(10, 2);

-- 添加注释
COMMENT ON COLUMN hot_concepts.leader_stock_code IS '龙头股代码';
COMMENT ON COLUMN hot_concepts.leader_stock_name IS '龙头股名称';
COMMENT ON COLUMN hot_concepts.leader_continuous_days IS '龙头股连板天数';
COMMENT ON COLUMN hot_concepts.leader_change_pct IS '龙头股当日涨幅(%)';
