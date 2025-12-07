-- ============================================================
-- 为 hot_concepts 表添加 is_new_concept 字段
-- 用途: 标识新概念板块（历史数据不足5个交易日）
-- 执行位置: Supabase SQL Editor
-- ============================================================

-- 添加 is_new_concept 字段（默认为 false）
ALTER TABLE hot_concepts
ADD COLUMN is_new_concept BOOLEAN NOT NULL DEFAULT false;

-- 添加字段注释
COMMENT ON COLUMN hot_concepts.is_new_concept IS '是否为新概念（历史数据不足5个交易日的概念）';

-- 创建索引（方便前端查询新概念）
CREATE INDEX idx_hot_concepts_new_concepts ON hot_concepts(trade_date, is_new_concept)
WHERE is_new_concept = true;

-- 验证表结构
SELECT
    column_name AS "字段名",
    data_type AS "数据类型",
    is_nullable AS "允许空值",
    column_default AS "默认值"
FROM information_schema.columns
WHERE table_name = 'hot_concepts'
ORDER BY ordinal_position;

-- 查看索引
SELECT
    indexname AS "索引名",
    indexdef AS "索引定义"
FROM pg_indexes
WHERE tablename = 'hot_concepts';
