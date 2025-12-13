-- ============================================
-- 补充更多缺失的列（第2批）
-- 执行日期: 2025-12-12
-- ============================================

-- 1. limit_stocks_detail 表添加涨停统计字段
ALTER TABLE limit_stocks_detail ADD COLUMN IF NOT EXISTS limit_stats VARCHAR(20);
ALTER TABLE limit_stocks_detail ADD COLUMN IF NOT EXISTS lu_desc TEXT;
ALTER TABLE limit_stocks_detail ADD COLUMN IF NOT EXISTS concepts_str TEXT;

COMMENT ON COLUMN limit_stocks_detail.limit_stats IS '涨停统计，格式 "1/1" (当前连板/历史最大连板)';
COMMENT ON COLUMN limit_stocks_detail.lu_desc IS '涨停原因/概念板块描述（Tushare）';
COMMENT ON COLUMN limit_stocks_detail.concepts_str IS '所属概念字符串（AKShare）';

-- 2. hot_concepts 表添加连续上榜天数和当日涨幅
ALTER TABLE hot_concepts ADD COLUMN IF NOT EXISTS consecutive_days INT DEFAULT 1;
ALTER TABLE hot_concepts ADD COLUMN IF NOT EXISTS day_change_pct DECIMAL(10, 4);

COMMENT ON COLUMN hot_concepts.consecutive_days IS '连续上榜天数';
COMMENT ON COLUMN hot_concepts.day_change_pct IS '当日涨跌幅';

-- ============================================
-- 完成！
-- ============================================

SELECT '✅ 第2批缺失列已添加完成' AS status;
