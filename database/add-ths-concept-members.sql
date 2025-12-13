-- 同花顺概念成分股表
-- 用于补全涨停股的概念板块信息

CREATE TABLE IF NOT EXISTS ths_concept_members (
    id SERIAL PRIMARY KEY,
    concept_code VARCHAR(20) NOT NULL,      -- 概念代码 (如 886078.TI)
    concept_name VARCHAR(100) NOT NULL,     -- 概念名称 (如 商业航天)
    stock_code VARCHAR(20) NOT NULL,        -- 成分股代码 (如 603601，不带后缀)
    stock_name VARCHAR(50),                 -- 成分股名称 (如 再升科技)
    updated_at TIMESTAMP DEFAULT NOW(),     -- 更新时间

    UNIQUE(concept_code, stock_code)
);

-- 索引：按股票代码查询所属概念（高频查询）
CREATE INDEX IF NOT EXISTS idx_ths_concept_members_stock_code ON ths_concept_members(stock_code);

-- 索引：按概念代码查询成分股
CREATE INDEX IF NOT EXISTS idx_ths_concept_members_concept_code ON ths_concept_members(concept_code);

-- 注释
COMMENT ON TABLE ths_concept_members IS '同花顺概念成分股映射表，用于补全涨停股概念';
COMMENT ON COLUMN ths_concept_members.concept_code IS '同花顺概念指数代码';
COMMENT ON COLUMN ths_concept_members.concept_name IS '概念名称';
COMMENT ON COLUMN ths_concept_members.stock_code IS '成分股代码（6位，不带交易所后缀）';
COMMENT ON COLUMN ths_concept_members.stock_name IS '成分股名称';
