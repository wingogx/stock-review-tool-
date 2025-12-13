-- ============================================
-- 为 hot_concepts 表添加异动板块字段
-- 执行日期: 2025-12-12
-- ============================================

-- 1. 添加 is_anomaly 字段（是否为异动板块）
ALTER TABLE hot_concepts ADD COLUMN IF NOT EXISTS is_anomaly BOOLEAN DEFAULT FALSE;

-- 2. 添加 anomaly_type 字段（异动类型）
ALTER TABLE hot_concepts ADD COLUMN IF NOT EXISTS anomaly_type VARCHAR(20);

-- 3. 添加字段注释
COMMENT ON COLUMN hot_concepts.is_anomaly IS '是否为异动板块（TOP10之外的涨停/涨幅异动）';
COMMENT ON COLUMN hot_concepts.anomaly_type IS '异动类型：limit_up(涨停异动) / change_pct(涨幅异动)';

-- 4. 为异动字段创建索引（加速查询）
CREATE INDEX IF NOT EXISTS idx_hot_concepts_anomaly ON hot_concepts(is_anomaly) WHERE is_anomaly = TRUE;

-- ============================================
-- 完成！
-- ============================================

SELECT '✅ 异动字段已添加完成' AS status;
