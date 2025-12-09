-- ============================================
-- 热门概念板块表字段补充迁移脚本
-- ============================================
-- 创建日期: 2025-12-09
-- 目的: 添加数据采集脚本中使用但数据库表中缺失的字段
--
-- 添加字段:
-- 1. day_change_pct      - 当日涨幅
-- 2. consecutive_days    - 连续上榜次数（统计前10范围）
-- 3. concept_strength    - 概念强度（更精确的涨幅值）
-- 4. is_new_concept      - 是否新概念（历史数据不足5个交易日）
-- 5. first_seen_date     - 首次出现日期
-- ============================================

-- 开始事务
BEGIN;

-- 1. 添加当日涨幅字段
ALTER TABLE hot_concepts
ADD COLUMN IF NOT EXISTS day_change_pct DECIMAL(10, 4);

-- 2. 添加连续上榜次数字段
ALTER TABLE hot_concepts
ADD COLUMN IF NOT EXISTS consecutive_days INT DEFAULT 1;

-- 3. 添加概念强度字段
ALTER TABLE hot_concepts
ADD COLUMN IF NOT EXISTS concept_strength DECIMAL(10, 4);

-- 4. 添加是否新概念标记字段
ALTER TABLE hot_concepts
ADD COLUMN IF NOT EXISTS is_new_concept BOOLEAN DEFAULT FALSE;

-- 5. 添加首次出现日期字段
ALTER TABLE hot_concepts
ADD COLUMN IF NOT EXISTS first_seen_date DATE;

-- 添加字段注释
COMMENT ON COLUMN hot_concepts.day_change_pct IS '当日涨幅(%)';
COMMENT ON COLUMN hot_concepts.consecutive_days IS '连续上榜次数（统计前10范围）';
COMMENT ON COLUMN hot_concepts.concept_strength IS '概念强度（更精确的涨幅值）';
COMMENT ON COLUMN hot_concepts.is_new_concept IS '是否新概念（历史数据不足5个交易日）';
COMMENT ON COLUMN hot_concepts.first_seen_date IS '首次出现日期';

-- 6. 为新添加的字段创建索引（提升查询性能）
CREATE INDEX IF NOT EXISTS idx_hot_concepts_consecutive_days
ON hot_concepts(consecutive_days DESC);

CREATE INDEX IF NOT EXISTS idx_hot_concepts_is_new_concept
ON hot_concepts(is_new_concept)
WHERE is_new_concept = TRUE;

CREATE INDEX IF NOT EXISTS idx_hot_concepts_first_seen_date
ON hot_concepts(first_seen_date);

-- 7. 如果数据库中存在 strength_score 字段，将其值复制到 concept_strength
-- 注意：如果 strength_score 不存在，此步骤会被跳过（已注释）
-- UPDATE hot_concepts
-- SET concept_strength = strength_score
-- WHERE concept_strength IS NULL AND strength_score IS NOT NULL;

-- 提交事务
COMMIT;

-- ============================================
-- 验证脚本
-- ============================================
-- 执行以下查询验证字段是否成功添加：
--
-- SELECT column_name, data_type, is_nullable, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'hot_concepts'
-- ORDER BY ordinal_position;
--
-- 预期结果应包含以下新字段：
-- - day_change_pct (numeric, YES, NULL)
-- - consecutive_days (integer, YES, 1)
-- - concept_strength (numeric, YES, NULL)
-- - is_new_concept (boolean, YES, false)
-- - first_seen_date (date, YES, NULL)
