-- ============================================
-- 股市短线复盘工具 - MVP 精简版数据库表结构
-- 版本: v1.0-MVP
-- 创建日期: 2025-12-07
-- 说明: 仅保留核心功能模块（指数、情绪、涨停池、概念板块）
-- ============================================

-- ============================================
-- 1. 大盘指数表
-- ============================================
CREATE TABLE market_index (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    index_code VARCHAR(20) NOT NULL,  -- SH000001(上证), SZ399001(深证), SZ399006(创业板)
    index_name VARCHAR(50),
    open_price DECIMAL(10, 2),
    high_price DECIMAL(10, 2),
    low_price DECIMAL(10, 2),
    close_price DECIMAL(10, 2),
    volume BIGINT,  -- 成交量
    amount DECIMAL(20, 2),  -- 成交额
    change_pct DECIMAL(10, 4),  -- 涨跌幅
    amplitude DECIMAL(10, 4),  -- 振幅 = (最高-最低)/昨收 * 100
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, index_code)
);

COMMENT ON TABLE market_index IS '大盘指数表 - 存储上证、深证、创业板指数数据';

-- ============================================
-- 2. 市场情绪分析表
-- ============================================
CREATE TABLE market_sentiment (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL UNIQUE,

    -- 成交数据
    total_amount DECIMAL(20, 2),  -- 全市场成交额
    sh_amount DECIMAL(20, 2),     -- 沪市成交额
    sz_amount DECIMAL(20, 2),     -- 深市成交额

    -- 涨跌统计
    up_count INT,                 -- 上涨家数
    down_count INT,               -- 下跌家数
    flat_count INT,               -- 平盘家数
    up_down_ratio DECIMAL(10, 4), -- 涨跌比

    -- 涨跌停统计
    limit_up_count INT,           -- 涨停数
    limit_down_count INT,         -- 跌停数

    -- 连板分布 (JSON 格式)
    -- 例如: {"1": 62, "2": 4, "3": 5, "4+": 2}
    continuous_limit_distribution JSONB,

    -- 炸板数据
    exploded_count INT,           -- 炸板数量（开过板的涨停）
    explosion_rate DECIMAL(10, 4), -- 炸板率 = 炸板数/涨停数

    -- 市场活跃度
    market_activity DECIMAL(10, 4), -- 市场活跃度（来自同花顺）

    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE market_sentiment IS '市场情绪分析表 - 涨跌比、连板分布、炸板率等';

-- ============================================
-- 3. 涨跌停个股详细表
-- ============================================
CREATE TABLE limit_stocks_detail (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50),

    -- 类型：涨停/跌停
    limit_type VARCHAR(10), -- 'limit_up' / 'limit_down'

    -- 基础数据
    change_pct DECIMAL(10, 4),
    close_price DECIMAL(10, 2),
    turnover_rate DECIMAL(10, 4),
    amount DECIMAL(20, 2),

    -- 涨停特有字段
    first_limit_time TIME,        -- 首次封板时间
    last_limit_time TIME,         -- 最后封板时间
    continuous_days INT,          -- 连板天数
    opening_times INT,            -- 开板次数（炸板次数）
    sealed_amount DECIMAL(20, 2), -- 封单金额

    -- 标签
    is_st BOOLEAN DEFAULT FALSE,
    is_new_stock BOOLEAN DEFAULT FALSE,  -- 是否次新股
    is_strong_limit BOOLEAN DEFAULT FALSE, -- 是否一字板

    -- 所属概念（数组）
    concepts TEXT[],

    -- 市值
    market_cap DECIMAL(20, 2),    -- 总市值
    circulation_market_cap DECIMAL(20, 2), -- 流通市值

    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, stock_code, limit_type)
);

COMMENT ON TABLE limit_stocks_detail IS '涨跌停个股详细表 - 涨停池/跌停池数据';

-- ============================================
-- 4. 热门概念板块表
-- ============================================
CREATE TABLE hot_concepts (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    concept_code VARCHAR(50),     -- 概念代码（如果有）
    concept_name VARCHAR(100) NOT NULL,

    -- 板块数据
    change_pct DECIMAL(10, 4),    -- 板块涨跌幅
    avg_change_pct DECIMAL(10, 4), -- 平均涨幅

    -- 成分股统计
    total_count INT,              -- 成分股总数
    up_count INT,                 -- 上涨家数
    down_count INT,               -- 下跌家数
    limit_up_count INT,           -- 涨停家数

    -- 龙头股（JSON 格式）
    -- 例如: [{"code": "600519", "name": "贵州茅台", "change_pct": 10.01}, ...]
    leading_stocks JSONB,

    -- 概念强度评分
    strength_score DECIMAL(10, 4), -- 平均涨幅 × 上涨家数

    -- 排名
    rank INT,                     -- 当日排名

    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, concept_name)
);

COMMENT ON TABLE hot_concepts IS '热门概念板块表 - 374个同花顺概念板块';

-- ============================================
-- 5. 概念成分股表（可选 - 如需要详细成分股列表）
-- ============================================
CREATE TABLE concept_stocks (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    concept_name VARCHAR(100) NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50),
    change_pct DECIMAL(10, 4),    -- 个股涨跌幅
    close_price DECIMAL(10, 2),
    is_leading BOOLEAN DEFAULT FALSE, -- 是否龙头股
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, concept_name, stock_code)
);

COMMENT ON TABLE concept_stocks IS '概念成分股表 - 存储每个概念板块的成分股';

-- ============================================
-- 6. 用户自选股配置表（保留以备后用）
-- ============================================
CREATE TABLE user_watchlist (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(50) DEFAULT 'default_user', -- 暂时用默认用户
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50),
    added_date TIMESTAMP DEFAULT NOW(),
    notes TEXT,  -- 用户备注
    UNIQUE(user_id, stock_code)
);

COMMENT ON TABLE user_watchlist IS '用户自选股配置表 - 预留功能';

-- ============================================
-- 索引优化
-- ============================================

-- 大盘指数索引
CREATE INDEX idx_market_index_date ON market_index(trade_date);
CREATE INDEX idx_market_index_code ON market_index(index_code);

-- 市场情绪索引
CREATE INDEX idx_market_sentiment_date ON market_sentiment(trade_date);

-- 涨跌停索引
CREATE INDEX idx_limit_stocks_date ON limit_stocks_detail(trade_date);
CREATE INDEX idx_limit_stocks_code ON limit_stocks_detail(stock_code);
CREATE INDEX idx_limit_stocks_type ON limit_stocks_detail(limit_type);
CREATE INDEX idx_limit_stocks_continuous ON limit_stocks_detail(continuous_days);

-- 热门概念索引
CREATE INDEX idx_hot_concepts_date ON hot_concepts(trade_date);
CREATE INDEX idx_hot_concepts_name ON hot_concepts(concept_name);
CREATE INDEX idx_hot_concepts_rank ON hot_concepts(rank);
CREATE INDEX idx_hot_concepts_strength ON hot_concepts(strength_score);

-- 概念成分股索引
CREATE INDEX idx_concept_stocks_date ON concept_stocks(trade_date);
CREATE INDEX idx_concept_stocks_concept ON concept_stocks(concept_name);
CREATE INDEX idx_concept_stocks_code ON concept_stocks(stock_code);

-- ============================================
-- 视图（可选 - 方便查询）
-- ============================================

-- 当日市场概览视图
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

COMMENT ON VIEW v_market_overview IS '当日市场概览视图 - 整合指数和情绪数据';

-- ============================================
-- 数据库初始化完成
-- ============================================

-- 插入测试数据（可选）
-- INSERT INTO user_watchlist (stock_code, stock_name, notes)
-- VALUES ('600519', '贵州茅台', '白酒龙头');
