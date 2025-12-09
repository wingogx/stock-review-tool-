-- 添加涨停股票新字段：涨停统计和所属行业
-- 执行日期：2025-12-10

-- 添加 limit_stats 列（涨停统计，如 "4/3" 表示累计涨停4次/连续涨停3天）
ALTER TABLE limit_stocks_detail ADD COLUMN IF NOT EXISTS limit_stats VARCHAR(50);

-- 添加 industry 列（所属行业）
ALTER TABLE limit_stocks_detail ADD COLUMN IF NOT EXISTS industry VARCHAR(100);

-- 添加注释
COMMENT ON COLUMN limit_stocks_detail.limit_stats IS '涨停统计，格式如 4/3';
COMMENT ON COLUMN limit_stocks_detail.industry IS '所属行业';
