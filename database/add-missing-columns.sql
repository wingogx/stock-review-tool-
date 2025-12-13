-- ============================================
-- 补充缺失的列
-- 用于修复schema与采集器代码不匹配的问题
-- 执行日期: 2025-12-12
-- ============================================

-- 1. market_index 表添加均线字段
ALTER TABLE market_index ADD COLUMN IF NOT EXISTS ma5 DECIMAL(10, 2);
ALTER TABLE market_index ADD COLUMN IF NOT EXISTS ma10 DECIMAL(10, 2);
ALTER TABLE market_index ADD COLUMN IF NOT EXISTS ma20 DECIMAL(10, 2);

COMMENT ON COLUMN market_index.ma5 IS '5日均线';
COMMENT ON COLUMN market_index.ma10 IS '10日均线';
COMMENT ON COLUMN market_index.ma20 IS '20日均线';

-- 2. limit_stocks_detail 表添加行业字段
ALTER TABLE limit_stocks_detail ADD COLUMN IF NOT EXISTS industry VARCHAR(100);

COMMENT ON COLUMN limit_stocks_detail.industry IS '所属行业';

-- 3. market_sentiment 表添加市场状态和活跃度字段
ALTER TABLE market_sentiment ADD COLUMN IF NOT EXISTS market_status VARCHAR(20);
ALTER TABLE market_sentiment ADD COLUMN IF NOT EXISTS market_activity DECIMAL(10, 4);

COMMENT ON COLUMN market_sentiment.market_status IS '市场状态：强势/震荡/弱势';
COMMENT ON COLUMN market_sentiment.market_activity IS '市场活跃度（来自同花顺）';

-- ============================================
-- 完成！
-- ============================================

SELECT '✅ 缺失列已添加完成' AS status;
