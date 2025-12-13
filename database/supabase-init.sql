-- ============================================
-- 股市短线复盘工具 - Supabase 数据库初始化脚本
-- 版本: v1.5
-- 日期: 2025-12-12
-- 说明: 包含11张核心业务表及所有索引、视图和RLS策略
-- ============================================

-- 使用说明：
-- 1. 登录 Supabase Dashboard (https://supabase.com/dashboard)
-- 2. 选择你的项目
-- 3. 进入 SQL Editor
-- 4. 复制粘贴本脚本并执行
-- 5. 执行完成后，更新 .env 文件中的 SUPABASE_URL 和 SUPABASE_KEY

-- ============================================
-- 清理旧表（可选，如果是全新项目请跳过）
-- ============================================
-- 取消注释以下内容来删除旧表
/*
DROP VIEW IF EXISTS v_today_hot_money_active;
DROP VIEW IF EXISTS v_today_strong_continuous_stocks;
DROP VIEW IF EXISTS v_today_market_overview;

DROP TABLE IF EXISTS user_watchlist CASCADE;
DROP TABLE IF EXISTS watchlist_monitoring CASCADE;
DROP TABLE IF EXISTS watchlist_stocks CASCADE;
DROP TABLE IF EXISTS hot_concepts CASCADE;
DROP TABLE IF EXISTS hot_money_ranking CASCADE;
DROP TABLE IF EXISTS institutional_seats CASCADE;
DROP TABLE IF EXISTS dragon_tiger_seats CASCADE;
DROP TABLE IF EXISTS dragon_tiger_board CASCADE;
DROP TABLE IF EXISTS limit_stocks_detail CASCADE;
DROP TABLE IF EXISTS market_sentiment CASCADE;
DROP TABLE IF EXISTS market_index CASCADE;
*/

-- ============================================
-- 1. 大盘指数表
-- 存储沪深主要指数的日K线数据
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
    volume BIGINT,                    -- 成交量
    amount DECIMAL(20, 2),            -- 成交额
    change_pct DECIMAL(10, 4),        -- 涨跌幅
    amplitude DECIMAL(10, 4),         -- 振幅 = (最高-最低)/昨收 * 100
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, index_code)
);

COMMENT ON TABLE market_index IS '大盘指数历史数据表';

-- ============================================
-- 2. 市场情绪分析表
-- 存储每日市场整体情绪指标
-- ============================================
CREATE TABLE market_sentiment (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL UNIQUE,

    -- 成交数据
    total_amount DECIMAL(20, 2),      -- 全市场成交额
    sh_amount DECIMAL(20, 2),         -- 沪市成交额
    sz_amount DECIMAL(20, 2),         -- 深市成交额

    -- 涨跌统计
    up_count INT,                     -- 上涨家数
    down_count INT,                   -- 下跌家数
    flat_count INT,                   -- 平盘家数
    up_down_ratio DECIMAL(10, 4),     -- 涨跌比

    -- 涨跌停统计
    limit_up_count INT,               -- 涨停数
    limit_down_count INT,             -- 跌停数

    -- 连板分布 (JSON 格式)
    -- 例如: {"2连板": 15, "3连板": 8, "4连板": 3, "5连板以上": 2}
    continuous_limit_distribution JSONB,

    -- 炸板数据
    exploded_count INT,               -- 炸板数量（开过板的涨停）
    explosion_rate DECIMAL(10, 4),    -- 炸板率 = 炸板数/(涨停数+炸板数)

    -- 市场强度
    strong_limit_up_count INT,        -- 一字板数量
    weak_limit_up_count INT,          -- 弱势涨停（开板多次）

    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE market_sentiment IS '市场情绪分析表';

-- ============================================
-- 3. 涨跌停个股详细表
-- 存储每日涨停和跌停股票的详细信息
-- ============================================
CREATE TABLE limit_stocks_detail (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50),

    -- 类型：涨停/跌停
    limit_type VARCHAR(10),           -- 'limit_up' / 'limit_down'

    -- 基础数据
    change_pct DECIMAL(10, 4),
    close_price DECIMAL(10, 2),
    turnover_rate DECIMAL(10, 4),
    amount DECIMAL(20, 2),

    -- 涨停特有字段
    first_limit_time TIME,            -- 首次封板时间
    last_limit_time TIME,             -- 最后封板时间
    continuous_days INT,              -- 连板天数
    opening_times INT,                -- 开板次数（炸板次数）
    sealed_amount DECIMAL(20, 2),     -- 封单金额

    -- 标签
    is_st BOOLEAN DEFAULT FALSE,
    is_new_stock BOOLEAN DEFAULT FALSE,       -- 是否次新股
    is_strong_limit BOOLEAN DEFAULT FALSE,    -- 是否一字板

    -- 所属概念（数组）
    concepts TEXT[],

    -- 市值
    market_cap DECIMAL(20, 2),                -- 总市值
    circulation_market_cap DECIMAL(20, 2),    -- 流通市值

    -- 资金流向
    main_net_inflow DECIMAL(20, 2),           -- 主力净流入
    main_net_inflow_pct DECIMAL(10, 4),       -- 主力净流入占比(%)

    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, stock_code, limit_type)
);

COMMENT ON TABLE limit_stocks_detail IS '涨跌停个股详细数据表';

-- ============================================
-- 4. 龙虎榜数据表
-- 存储龙虎榜上榜股票基础信息
-- ============================================
CREATE TABLE dragon_tiger_board (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50),
    close_price DECIMAL(10, 2),
    change_pct DECIMAL(10, 4),
    turnover_rate DECIMAL(10, 4),
    total_amount DECIMAL(20, 2),
    lhb_buy_amount DECIMAL(20, 2),    -- 龙虎榜买入总额
    lhb_sell_amount DECIMAL(20, 2),   -- 龙虎榜卖出总额
    lhb_net_amount DECIMAL(20, 2),    -- 龙虎榜净额
    reason TEXT,                       -- 上榜原因
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, stock_code)
);

COMMENT ON TABLE dragon_tiger_board IS '龙虎榜主表';

-- ============================================
-- 5. 龙虎榜席位明细表
-- 存储龙虎榜买卖席位明细
-- ============================================
CREATE TABLE dragon_tiger_seats (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50),
    seat_name TEXT,                    -- 席位名称（营业部）
    buy_amount DECIMAL(20, 2),
    sell_amount DECIMAL(20, 2),
    net_amount DECIMAL(20, 2),
    seat_type VARCHAR(10),             -- '买入' / '卖出'
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE dragon_tiger_seats IS '龙虎榜席位明细表';

-- ============================================
-- 6. 机构席位统计表
-- 统计机构在龙虎榜的表现
-- ============================================
CREATE TABLE institutional_seats (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50),

    -- 机构买入统计
    institutional_buy_count INT,               -- 机构买入席位数
    institutional_buy_amount DECIMAL(20, 2),

    -- 机构卖出统计
    institutional_sell_count INT,              -- 机构卖出席位数
    institutional_sell_amount DECIMAL(20, 2),

    -- 净额
    institutional_net_amount DECIMAL(20, 2),

    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, stock_code)
);

COMMENT ON TABLE institutional_seats IS '机构席位统计表';

-- ============================================
-- 7. 游资席位排行表
-- 追踪活跃游资营业部排名
-- ============================================
CREATE TABLE hot_money_ranking (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    seat_name TEXT,                            -- 营业部名称

    -- 上榜统计
    appearance_count INT,                      -- 当日上榜次数
    total_buy_amount DECIMAL(20, 2),
    total_sell_amount DECIMAL(20, 2),
    net_amount DECIMAL(20, 2),

    -- 历史成功率（后续计算）
    success_rate DECIMAL(10, 4),               -- 成功率
    win_count INT,                             -- 盈利次数
    loss_count INT,                            -- 亏损次数

    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, seat_name)
);

COMMENT ON TABLE hot_money_ranking IS '游资席位排行表';

-- ============================================
-- 8. 热门概念板块表
-- 存储同花顺概念板块的每日表现
-- ============================================
CREATE TABLE hot_concepts (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    concept_name VARCHAR(100) NOT NULL,
    concept_code VARCHAR(50),

    -- 涨跌数据
    change_pct DECIMAL(10, 4),                 -- 板块涨跌幅
    avg_change_pct DECIMAL(10, 4),             -- 平均涨跌幅

    -- 龙头股（数组，前3名）
    leading_stocks TEXT[],

    -- 成分股统计
    stock_count INT,                           -- 成分股数量
    up_count INT,                              -- 上涨股票数
    down_count INT,                            -- 下跌股票数
    limit_up_count INT,                        -- 涨停股票数

    -- 成交数据
    total_amount DECIMAL(20, 2),               -- 板块成交额

    -- 概念强度评分
    concept_strength DECIMAL(10, 4),           -- 强度 = 平均涨幅 * 上涨家数

    -- 排名
    rank INT,                                  -- 当日概念排名

    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, concept_name)
);

COMMENT ON TABLE hot_concepts IS '热门概念板块表';

-- ============================================
-- 9. 自选股跟踪表
-- 存储自选股的历史行情数据
-- ============================================
CREATE TABLE watchlist_stocks (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50),
    open_price DECIMAL(10, 2),
    high_price DECIMAL(10, 2),
    low_price DECIMAL(10, 2),
    close_price DECIMAL(10, 2),
    volume BIGINT,
    amount DECIMAL(20, 2),
    change_pct DECIMAL(10, 4),
    turnover_rate DECIMAL(10, 4),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, stock_code)
);

COMMENT ON TABLE watchlist_stocks IS '自选股历史行情表';

-- ============================================
-- 10. 自选股监控表
-- 标记自选股的异动和特殊事件
-- ============================================
CREATE TABLE watchlist_monitoring (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50),

    -- 基础行情
    close_price DECIMAL(10, 2),
    change_pct DECIMAL(10, 4),
    turnover_rate DECIMAL(10, 4),
    amount DECIMAL(20, 2),

    -- 特殊标记
    is_on_dragon_tiger BOOLEAN DEFAULT FALSE,
    dragon_tiger_reason TEXT,

    is_in_hot_concept BOOLEAN DEFAULT FALSE,
    hot_concepts TEXT[],                       -- 所属热门概念列表

    is_new_high BOOLEAN DEFAULT FALSE,         -- 创60日新高
    is_new_low BOOLEAN DEFAULT FALSE,          -- 创60日新低

    -- 异动标记
    is_abnormal BOOLEAN DEFAULT FALSE,
    abnormal_reason TEXT,                      -- 异动原因

    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, stock_code)
);

COMMENT ON TABLE watchlist_monitoring IS '自选股监控标记表';

-- ============================================
-- 11. 用户自选股配置表
-- 存储用户的自选股列表
-- ============================================
CREATE TABLE user_watchlist (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50),
    added_date TIMESTAMP DEFAULT NOW(),
    notes TEXT,                                -- 用户备注
    alert_enabled BOOLEAN DEFAULT TRUE,        -- 是否开启提醒
    UNIQUE(user_id, stock_code)
);

COMMENT ON TABLE user_watchlist IS '用户自选股配置表';

-- ============================================
-- 创建索引（提升查询性能）
-- ============================================

-- 大盘指数索引
CREATE INDEX idx_market_index_date ON market_index(trade_date);
CREATE INDEX idx_market_index_code ON market_index(index_code);

-- 市场情绪索引
CREATE INDEX idx_market_sentiment_date ON market_sentiment(trade_date);

-- 涨跌停索引
CREATE INDEX idx_limit_stocks_date ON limit_stocks_detail(trade_date);
CREATE INDEX idx_limit_stocks_type ON limit_stocks_detail(limit_type);
CREATE INDEX idx_limit_stocks_continuous ON limit_stocks_detail(continuous_days);
CREATE INDEX idx_limit_stocks_code ON limit_stocks_detail(stock_code);

-- 龙虎榜索引
CREATE INDEX idx_dragon_tiger_date ON dragon_tiger_board(trade_date);
CREATE INDEX idx_dragon_tiger_code ON dragon_tiger_board(stock_code);

-- 席位索引
CREATE INDEX idx_seats_date ON dragon_tiger_seats(trade_date);
CREATE INDEX idx_seats_code ON dragon_tiger_seats(stock_code);

-- 机构席位索引
CREATE INDEX idx_institutional_date ON institutional_seats(trade_date);

-- 游资排行索引
CREATE INDEX idx_hot_money_date ON hot_money_ranking(trade_date);

-- 概念板块索引
CREATE INDEX idx_hot_concepts_date ON hot_concepts(trade_date);
CREATE INDEX idx_hot_concepts_rank ON hot_concepts(rank);
CREATE INDEX idx_hot_concepts_name ON hot_concepts(concept_name);

-- 自选股索引
CREATE INDEX idx_watchlist_date ON watchlist_stocks(trade_date);
CREATE INDEX idx_watchlist_code ON watchlist_stocks(stock_code);
CREATE INDEX idx_watchlist_monitoring_date ON watchlist_monitoring(trade_date);

-- ============================================
-- RLS (Row Level Security) 策略
-- 保护用户数据安全
-- ============================================

-- 启用自选股表的 RLS
ALTER TABLE user_watchlist ENABLE ROW LEVEL SECURITY;

-- 用户只能查看自己的自选股
CREATE POLICY "Users can view their own watchlist"
ON user_watchlist
FOR SELECT
USING (auth.uid() = user_id);

-- 用户只能插入自己的自选股
CREATE POLICY "Users can insert their own watchlist"
ON user_watchlist
FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- 用户只能删除自己的自选股
CREATE POLICY "Users can delete their own watchlist"
ON user_watchlist
FOR DELETE
USING (auth.uid() = user_id);

-- 用户只能更新自己的自选股
CREATE POLICY "Users can update their own watchlist"
ON user_watchlist
FOR UPDATE
USING (auth.uid() = user_id);

-- ============================================
-- 创建视图（方便查询常用数据）
-- ============================================

-- 今日市场总览视图
CREATE VIEW v_today_market_overview AS
SELECT
    m.trade_date,
    m.index_name,
    m.close_price,
    m.change_pct,
    m.amount,
    s.total_amount as market_total_amount,
    s.up_count,
    s.down_count,
    s.up_down_ratio,
    s.limit_up_count,
    s.limit_down_count,
    s.explosion_rate
FROM market_index m
LEFT JOIN market_sentiment s ON m.trade_date = s.trade_date
WHERE m.trade_date = (SELECT MAX(trade_date) FROM market_index);

-- 今日强势连板股视图
CREATE VIEW v_today_strong_continuous_stocks AS
SELECT
    trade_date,
    stock_code,
    stock_name,
    continuous_days,
    first_limit_time,
    opening_times,
    concepts
FROM limit_stocks_detail
WHERE trade_date = (SELECT MAX(trade_date) FROM limit_stocks_detail)
  AND limit_type = 'limit_up'
  AND continuous_days >= 2
ORDER BY continuous_days DESC, first_limit_time ASC;

-- 今日游资活跃排行视图
CREATE VIEW v_today_hot_money_active AS
SELECT
    trade_date,
    seat_name,
    appearance_count,
    net_amount,
    success_rate
FROM hot_money_ranking
WHERE trade_date = (SELECT MAX(trade_date) FROM hot_money_ranking)
  AND appearance_count >= 2
ORDER BY appearance_count DESC, net_amount DESC;

-- ============================================
-- 完成！
-- ============================================

-- 执行成功后，你应该看到：
-- ✅ 11 张表已创建
-- ✅ 所有索引已创建
-- ✅ RLS 策略已配置
-- ✅ 3 个视图已创建

-- 下一步：
-- 1. 复制 Supabase 项目的 URL 和 anon/service_role key
-- 2. 更新项目根目录的 .env 文件
-- 3. 运行数据采集脚本填充数据
