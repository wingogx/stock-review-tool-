-- ============================================
-- 新增表：昨日涨停股今日表现
-- 用途：计算情绪周期核心因子（溢价率、大面率等）
-- 日期：2025-12-12
-- ============================================

-- 创建表
CREATE TABLE IF NOT EXISTS yesterday_limit_performance (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,                    -- 今日日期（表现日期）
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50),

    -- 昨日涨停信息
    yesterday_continuous_days INT DEFAULT 1,     -- 昨日连板数（1=首板，2=2连板...）
    yesterday_is_strong_limit BOOLEAN,           -- 昨日是否一字板

    -- 今日表现
    today_open_pct DECIMAL(10, 4),               -- 今日开盘涨幅（集合竞价溢价）
    today_change_pct DECIMAL(10, 4),             -- 今日涨跌幅
    today_high_pct DECIMAL(10, 4),               -- 今日最高涨幅
    today_low_pct DECIMAL(10, 4),                -- 今日最低涨幅
    today_amount DECIMAL(20, 2),                 -- 今日成交额

    -- 今日状态标记
    is_limit_up BOOLEAN DEFAULT FALSE,           -- 今日是否涨停（晋级成功）
    is_limit_down BOOLEAN DEFAULT FALSE,         -- 今日是否跌停
    is_big_loss BOOLEAN DEFAULT FALSE,           -- 是否大面（跌幅>5%）
    is_big_high BOOLEAN DEFAULT FALSE,           -- 是否大涨（涨幅>5%但未涨停）

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(trade_date, stock_code)
);

-- 添加注释
COMMENT ON TABLE yesterday_limit_performance IS '昨日涨停股今日表现表，用于计算情绪周期因子';
COMMENT ON COLUMN yesterday_limit_performance.trade_date IS '今日日期（表现日期）';
COMMENT ON COLUMN yesterday_limit_performance.yesterday_continuous_days IS '昨日连板数：1=首板，2=2连板';
COMMENT ON COLUMN yesterday_limit_performance.today_open_pct IS '今日开盘涨幅，即集合竞价溢价';
COMMENT ON COLUMN yesterday_limit_performance.is_big_loss IS '大面标记：今日跌幅超过5%';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_ylp_trade_date ON yesterday_limit_performance(trade_date);
CREATE INDEX IF NOT EXISTS idx_ylp_yesterday_days ON yesterday_limit_performance(yesterday_continuous_days);
CREATE INDEX IF NOT EXISTS idx_ylp_big_loss ON yesterday_limit_performance(trade_date, is_big_loss);

-- ============================================
-- 创建视图：每日溢价统计
-- ============================================
CREATE OR REPLACE VIEW v_daily_premium_stats AS
SELECT
    trade_date,
    -- 整体统计
    COUNT(*) as total_count,                                    -- 昨日涨停总数
    ROUND(AVG(today_change_pct), 2) as avg_change_pct,         -- 平均涨跌幅（整体溢价）
    ROUND(AVG(today_open_pct), 2) as avg_open_pct,             -- 平均开盘溢价

    -- 首板统计
    COUNT(*) FILTER (WHERE yesterday_continuous_days = 1) as first_board_count,
    ROUND(AVG(today_change_pct) FILTER (WHERE yesterday_continuous_days = 1), 2) as first_board_premium,

    -- 2连板统计
    COUNT(*) FILTER (WHERE yesterday_continuous_days = 2) as second_board_count,
    ROUND(AVG(today_change_pct) FILTER (WHERE yesterday_continuous_days = 2), 2) as second_board_premium,

    -- 高位板统计（3板+）
    COUNT(*) FILTER (WHERE yesterday_continuous_days >= 3) as high_board_count,
    ROUND(AVG(today_change_pct) FILTER (WHERE yesterday_continuous_days >= 3), 2) as high_board_premium,

    -- 晋级统计
    COUNT(*) FILTER (WHERE is_limit_up = TRUE) as promotion_count,    -- 晋级成功数
    ROUND(100.0 * COUNT(*) FILTER (WHERE is_limit_up = TRUE) / NULLIF(COUNT(*), 0), 1) as promotion_rate,

    -- 大面统计
    COUNT(*) FILTER (WHERE is_big_loss = TRUE) as big_loss_count,     -- 大面数
    ROUND(100.0 * COUNT(*) FILTER (WHERE is_big_loss = TRUE) / NULLIF(COUNT(*), 0), 1) as big_loss_rate,

    -- 高位大面统计（3板+大面）
    COUNT(*) FILTER (WHERE yesterday_continuous_days >= 3 AND is_big_loss = TRUE) as high_board_big_loss_count,
    ROUND(100.0 * COUNT(*) FILTER (WHERE yesterday_continuous_days >= 3 AND is_big_loss = TRUE) /
          NULLIF(COUNT(*) FILTER (WHERE yesterday_continuous_days >= 3), 0), 1) as high_board_big_loss_rate

FROM yesterday_limit_performance
GROUP BY trade_date
ORDER BY trade_date DESC;

COMMENT ON VIEW v_daily_premium_stats IS '每日昨日涨停股溢价统计视图';

-- ============================================
-- 完成提示
-- ============================================
-- 执行成功后：
-- ✅ yesterday_limit_performance 表已创建
-- ✅ 3个索引已创建
-- ✅ v_daily_premium_stats 视图已创建
