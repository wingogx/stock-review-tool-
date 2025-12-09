# 数据库迁移脚本

## 目录

### 1. add_hot_concepts_fields.sql
**创建日期**: 2025-12-09
**状态**: ✅ 可用

**目的**: 为 `hot_concepts` 表添加数据采集脚本中使用但数据库表中缺失的字段

**添加字段**:
- `day_change_pct` - 当日涨幅 (DECIMAL)
- `consecutive_days` - 连续上榜次数 (INT)
- `concept_strength` - 概念强度 (DECIMAL)
- `is_new_concept` - 是否新概念 (BOOLEAN)
- `first_seen_date` - 首次出现日期 (DATE)

**执行方式**:

1. **通过 Supabase 控制台**:
   - 登录 Supabase Dashboard
   - 进入 SQL Editor
   - 复制 `add_hot_concepts_fields.sql` 内容
   - 点击 Run 执行

2. **通过 psql 命令行**:
   ```bash
   psql -h your-supabase-host \
        -U postgres \
        -d postgres \
        -f database/migrations/add_hot_concepts_fields.sql
   ```

3. **通过 Python 脚本**:
   ```python
   from app.utils.supabase_client import get_supabase

   with open('database/migrations/add_hot_concepts_fields.sql', 'r') as f:
       sql = f.read()

   supabase = get_supabase()
   supabase.rpc('exec_sql', {'sql': sql}).execute()
   ```

**验证**:
```sql
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'hot_concepts'
ORDER BY ordinal_position;
```

### 2. rollback_hot_concepts_fields.sql
**创建日期**: 2025-12-09
**状态**: ✅ 可用

**目的**: 回滚 `add_hot_concepts_fields.sql` 添加的字段

⚠️ **警告**: 执行此脚本将**永久删除**这些字段及其数据，无法恢复！

**执行方式**: 同上

---

## 迁移历史

| 日期 | 脚本名称 | 描述 | 状态 |
|------|---------|------|------|
| 2025-12-09 | add_hot_concepts_fields.sql | 添加热门概念板块缺失字段 | ⏭️ 待执行 |

---

## 注意事项

1. **执行顺序**: 严格按照文件名的日期/版本号顺序执行
2. **备份**: 执行迁移前务必备份数据库
3. **测试**: 在开发环境测试通过后再在生产环境执行
4. **事务**: 所有迁移脚本都使用事务，失败会自动回滚
5. **幂等性**: 使用 `IF NOT EXISTS` / `IF EXISTS` 确保可重复执行

---

## 常见问题

### Q: 迁移失败怎么办？
A: 脚本使用事务，失败会自动回滚。检查错误信息，修复后重新执行。

### Q: 如何查看当前数据库表结构？
A: 执行以下 SQL:
```sql
\d+ hot_concepts  -- psql
-- 或
SELECT * FROM information_schema.columns WHERE table_name = 'hot_concepts';
```

### Q: 新字段对现有数据有影响吗？
A: 不会。新字段都是 nullable 或有默认值，不影响现有记录。

### Q: 需要重启服务吗？
A: 不需要。数据库 schema 变更会立即生效。
