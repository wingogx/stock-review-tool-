-- ============================================
-- 市场情绪表添加 market_status 字段
-- ============================================
-- 创建日期: 2025-12-09
-- 目的: 添加市场状态字段（强势/弱势/震荡）
--
-- market_status 字段说明:
-- - "强势": 上涨家数占比 >= 60%
-- - "弱势": 上涨家数占比 < 40%
-- - "震荡": 上涨家数占比在40%-60%之间
-- ============================================

-- 开始事务
BEGIN;

-- 添加 market_status 字段
ALTER TABLE market_sentiment
ADD COLUMN IF NOT EXISTS market_status VARCHAR(10);

-- 添加字段注释
COMMENT ON COLUMN market_sentiment.market_status IS '市场状态（强势/弱势/震荡）';

-- 创建索引（可选）
CREATE INDEX IF NOT EXISTS idx_market_sentiment_status
ON market_sentiment(market_status);

-- 提交事务
COMMIT;

-- ============================================
-- 验证脚本
-- ============================================
-- 执行以下查询验证字段是否成功添加：
--
-- SELECT column_name, data_type, is_nullable, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'market_sentiment'
-- ORDER BY ordinal_position;
--
-- 预期结果应包含新字段：
-- - market_status (character varying, YES, NULL)
