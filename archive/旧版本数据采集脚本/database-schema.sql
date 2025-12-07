-- ============================================
-- 股市复盘工具 - Supabase 数据库表结构
-- ============================================

-- 1. 大盘指数表
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
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, index_code)
);

-- 2. 涨跌停数据表
CREATE TABLE limit_stats (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    limit_up_count INT,  -- 涨停数量
    limit_down_count INT,  -- 跌停数量
    limit_up_stocks TEXT[],  -- 涨停股票列表(JSON或数组)
    limit_down_stocks TEXT[],  -- 跌停股票列表
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date)
);

-- 3. 龙虎榜数据表
CREATE TABLE dragon_tiger_board (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50),
    close_price DECIMAL(10, 2),
    change_pct DECIMAL(10, 4),
    turnover_rate DECIMAL(10, 4),
    total_amount DECIMAL(20, 2),  -- 总成交额
    lhb_buy_amount DECIMAL(20, 2),  -- 龙虎榜买入额
    lhb_sell_amount DECIMAL(20, 2),  -- 龙虎榜卖出额
    lhb_net_amount DECIMAL(20, 2),  -- 龙虎榜净买入额
    reason TEXT,  -- 上榜理由
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, stock_code)
);

-- 4. 龙虎榜席位明细表
CREATE TABLE dragon_tiger_seats (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50),
    seat_name TEXT,  -- 营业部名称
    buy_amount DECIMAL(20, 2),  -- 买入金额
    sell_amount DECIMAL(20, 2),  -- 卖出金额
    net_amount DECIMAL(20, 2),  -- 净额
    seat_type VARCHAR(10),  -- 买入/卖出
    created_at TIMESTAMP DEFAULT NOW()
);

-- 5. 热门概念板块表
CREATE TABLE hot_concepts (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    concept_name VARCHAR(100) NOT NULL,
    concept_code VARCHAR(50),
    change_pct DECIMAL(10, 4),  -- 板块涨跌幅
    leading_stock VARCHAR(10),  -- 龙头股票
    stock_count INT,  -- 成分股数量
    up_count INT,  -- 上涨股票数
    down_count INT,  -- 下跌股票数
    total_amount DECIMAL(20, 2),  -- 板块成交额
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, concept_name)
);

-- 6. 自选股跟踪表
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

-- 7. 用户自选股配置表
CREATE TABLE user_watchlist (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50),
    added_date TIMESTAMP DEFAULT NOW(),
    notes TEXT,
    UNIQUE(user_id, stock_code)
);

-- ============================================
-- 索引优化
-- ============================================

CREATE INDEX idx_market_index_date ON market_index(trade_date);
CREATE INDEX idx_dragon_tiger_date ON dragon_tiger_board(trade_date);
CREATE INDEX idx_watchlist_date ON watchlist_stocks(trade_date);
CREATE INDEX idx_hot_concepts_date ON hot_concepts(trade_date);

-- ============================================
-- RLS (Row Level Security) 策略（可选）
-- ============================================

-- 启用 RLS
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
