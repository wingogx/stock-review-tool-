-- ============================================
-- 数据库迁移脚本：从完整版迁移到 MVP 版
-- 执行时间: 2025-12-07
-- 操作: 删除不需要的表，保留核心表
-- ============================================

-- ============================================
-- Step 1: 删除不需要的表（龙虎榜相关、自选股监控相关）
-- ============================================

DROP TABLE IF EXISTS dragon_tiger_board CASCADE;
DROP TABLE IF EXISTS dragon_tiger_seats CASCADE;
DROP TABLE IF EXISTS institutional_seats CASCADE;
DROP TABLE IF EXISTS hot_money_ranking CASCADE;
DROP TABLE IF EXISTS watchlist_stocks CASCADE;
DROP TABLE IF EXISTS watchlist_monitoring CASCADE;

-- ============================================
-- Step 2: 验证保留的表
-- ============================================

-- 检查保留的表是否存在
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- 应该返回以下 6 张表:
-- 1. market_index
-- 2. market_sentiment
-- 3. limit_stocks_detail
-- 4. hot_concepts
-- 5. concept_stocks (如果有)
-- 6. user_watchlist

-- ============================================
-- Step 3: 添加 MVP 版本缺失的字段（如果需要）
-- ============================================

-- 检查 market_sentiment 表是否有 market_activity 字段
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'market_sentiment'
        AND column_name = 'market_activity'
    ) THEN
        ALTER TABLE market_sentiment
        ADD COLUMN market_activity DECIMAL(10, 4);
    END IF;
END $$;

-- ============================================
-- Step 4: 创建视图（如果不存在）
-- ============================================

-- 删除旧视图（如果存在）
DROP VIEW IF EXISTS v_market_overview;

-- 创建市场概览视图
CREATE OR REPLACE VIEW v_market_overview AS
SELECT
    ms.trade_date,
    ms.total_amount,
    ms.up_count,
    ms.down_count,
    ms.up_down_ratio,
    ms.limit_up_count,
    ms.limit_down_count,
    ms.explosion_rate,
    ms.market_activity,
    mi_sh.close_price as sh_index,
    mi_sh.change_pct as sh_change_pct,
    mi_sz.close_price as sz_index,
    mi_sz.change_pct as sz_change_pct,
    mi_cy.close_price as cy_index,
    mi_cy.change_pct as cy_change_pct
FROM market_sentiment ms
LEFT JOIN market_index mi_sh ON ms.trade_date = mi_sh.trade_date AND mi_sh.index_code = 'SH000001'
LEFT JOIN market_index mi_sz ON ms.trade_date = mi_sz.trade_date AND mi_sz.index_code = 'SZ399001'
LEFT JOIN market_index mi_cy ON ms.trade_date = mi_cy.trade_date AND mi_cy.index_code = 'SZ399006';

-- ============================================
-- Step 5: 添加表注释
-- ============================================

COMMENT ON TABLE market_index IS 'MVP - 大盘指数表';
COMMENT ON TABLE market_sentiment IS 'MVP - 市场情绪分析表';
COMMENT ON TABLE limit_stocks_detail IS 'MVP - 涨跌停个股详细表';
COMMENT ON TABLE hot_concepts IS 'MVP - 热门概念板块表';
COMMENT ON TABLE user_watchlist IS 'MVP - 用户自选股配置表（预留）';

-- ============================================
-- 迁移完成
-- ============================================

-- 最终验证
SELECT
    'MVP 数据库迁移完成' as status,
    COUNT(*) as table_count
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE';

-- 应该返回 5-6 张表
