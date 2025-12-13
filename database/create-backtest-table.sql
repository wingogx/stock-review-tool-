-- 回测结果表：存储溢价评分预测 vs 次日实际表现
CREATE TABLE IF NOT EXISTS premium_score_backtest (
    -- 基础信息
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(6) NOT NULL,
    stock_name VARCHAR(50) NOT NULL,
    trade_date DATE NOT NULL,  -- 评测日期（涨停日）

    -- 评分数据
    continuous_days INTEGER NOT NULL,  -- 连板天数
    total_score DECIMAL(5,2) NOT NULL,  -- 总分（10分制）
    premium_level VARCHAR(10) NOT NULL,  -- 溢价等级（极高/高/偏高/中性/偏低/低）

    -- 各维度得分
    technical_score DECIMAL(5,2) NOT NULL,  -- 技术面得分
    capital_score DECIMAL(5,2) NOT NULL,    -- 资金面得分
    theme_score DECIMAL(5,2) NOT NULL,      -- 题材地位得分
    position_score DECIMAL(5,2) NOT NULL,   -- 位置风险得分
    market_score DECIMAL(5,2) NOT NULL,     -- 市场环境得分

    -- 次日实际表现
    next_trade_date DATE,  -- 次日交易日期
    next_day_change_pct DECIMAL(8,2),  -- 次日涨跌幅
    next_day_close_price DECIMAL(10,2),  -- 次日收盘价
    is_next_day_limit_up BOOLEAN DEFAULT FALSE,  -- 次日是否涨停
    is_next_day_limit_down BOOLEAN DEFAULT FALSE,  -- 次日是否跌停
    next_day_turnover_rate DECIMAL(8,2),  -- 次日换手率

    -- 预测准确性分析
    prediction_result VARCHAR(20),  -- 预测结果：正确/错误/中性
    is_profitable BOOLEAN,  -- 是否盈利（次日涨跌幅>0）

    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 唯一约束：同一只股票同一天只能有一条评测记录
    UNIQUE(stock_code, trade_date)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_backtest_trade_date ON premium_score_backtest(trade_date);
CREATE INDEX IF NOT EXISTS idx_backtest_stock_code ON premium_score_backtest(stock_code);
CREATE INDEX IF NOT EXISTS idx_backtest_score ON premium_score_backtest(total_score);
CREATE INDEX IF NOT EXISTS idx_backtest_level ON premium_score_backtest(premium_level);
CREATE INDEX IF NOT EXISTS idx_backtest_next_pct ON premium_score_backtest(next_day_change_pct);

-- 添加注释
COMMENT ON TABLE premium_score_backtest IS '溢价评分回测表：记录评分预测与次日实际表现';
COMMENT ON COLUMN premium_score_backtest.trade_date IS '评测日期（涨停当日）';
COMMENT ON COLUMN premium_score_backtest.total_score IS '总分（0-10分制）';
COMMENT ON COLUMN premium_score_backtest.next_day_change_pct IS '次日涨跌幅（%）';
COMMENT ON COLUMN premium_score_backtest.prediction_result IS '预测结果：correct(正确)/wrong(错误)/neutral(中性)';

-- 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_backtest_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_backtest_timestamp
    BEFORE UPDATE ON premium_score_backtest
    FOR EACH ROW
    EXECUTE FUNCTION update_backtest_updated_at();
