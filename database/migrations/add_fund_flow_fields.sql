-- 为 limit_stocks_detail 表添加资金流向字段
-- 执行时间: 2025-12-10
-- 说明: 添加主力净流入数据字段

ALTER TABLE limit_stocks_detail
ADD COLUMN IF NOT EXISTS main_net_inflow DECIMAL(20, 2),
ADD COLUMN IF NOT EXISTS main_net_inflow_pct DECIMAL(10, 4);

-- 添加字段注释
COMMENT ON COLUMN limit_stocks_detail.main_net_inflow IS '主力净流入（超大单+大单）';
COMMENT ON COLUMN limit_stocks_detail.main_net_inflow_pct IS '主力净流入占比(%)';
