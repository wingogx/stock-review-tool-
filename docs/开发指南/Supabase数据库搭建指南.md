# Supabase 数据库搭建指南

**任务**: Task 1.1 - 数据库搭建
**预计工时**: 0.5天
**更新时间**: 2025-12-07

---

## 📋 操作步骤

### Step 1: 创建 Supabase 账号和项目

1. **访问 Supabase 官网**
   - 打开浏览器，访问：https://supabase.com

2. **注册/登录账号**
   - 点击右上角 "Start your project"
   - 使用 GitHub/Google 账号登录（推荐）
   - 或使用邮箱注册

3. **创建新项目**
   - 登录后，点击 "New Project"
   - 填写项目信息：
     ```
     Project Name: short-term-review
     Database Password: <设置一个强密码，务必记住>
     Region: Northeast Asia (Seoul) - 选择离中国最近的节点
     Pricing Plan: Free (开发阶段够用)
     ```
   - 点击 "Create new project"
   - 等待 2-3 分钟，数据库初始化中...

---

### Step 2: 记录数据库连接信息

1. **进入项目设置**
   - 项目创建完成后，点击左侧菜单 "Project Settings" (齿轮图标)
   - 点击 "API" 标签页

2. **复制以下信息**（待会要用）：

   ```
   Project URL (URL):
   例如: https://xxxxxxxxxxxxx.supabase.co

   Project API keys > anon public:
   例如: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

   Project API keys > service_role (点击 "Reveal" 显示):
   例如: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

3. **更新项目根目录的 `.env` 文件**

   打开 `/Users/win/Documents/ai 编程/cc/短信复盘/.env`，更新以下内容：

   ```env
   # Tushare (已配置)
   TUSHARE_TOKEN=2876ea85cb005fb5fa17c809a98174f2d5aae8b1f830110a5ead6211

   # Supabase (新增以下内容)
   SUPABASE_URL=<粘贴你的 Project URL>
   SUPABASE_KEY=<粘贴你的 service_role key>
   SUPABASE_ANON_KEY=<粘贴你的 anon public key>

   # Server (已配置)
   PORT=8000
   ENV=development
   LOG_LEVEL=INFO
   ```

---

### Step 3: 执行数据库 Schema（创建 11 张表）

1. **打开 SQL Editor**
   - 在 Supabase 项目页面，点击左侧菜单 "SQL Editor"
   - 点击 "New query"

2. **复制 Schema SQL**

   打开本地文件：`/Users/win/Documents/ai 编程/cc/短信复盘/database/schema.sql`

   **完整复制文件内容**（约 500+ 行）

3. **执行 SQL**
   - 将复制的 SQL 粘贴到 SQL Editor 中
   - 点击右下角 "Run" 按钮（或按 Ctrl+Enter）
   - 等待执行完成（约 5-10 秒）

4. **查看执行结果**
   - 如果成功，会显示 "Success. No rows returned"
   - 如果报错，检查是否完整复制了 SQL

---

### Step 4: 验证表创建成功

1. **在 SQL Editor 中执行验证查询**：

   ```sql
   SELECT table_name
   FROM information_schema.tables
   WHERE table_schema = 'public'
   ORDER BY table_name;
   ```

2. **应该返回以下 11 张表**：

   ```
   1. market_index              -- 大盘指数
   2. market_sentiment           -- 市场情绪
   3. limit_stocks_detail        -- 涨跌停详细
   4. dragon_tiger_board         -- 龙虎榜
   5. dragon_tiger_seats         -- 龙虎榜席位
   6. institutional_seats        -- 机构席位汇总
   7. hot_money_ranking          -- 游资排名
   8. hot_concepts               -- 热门概念
   9. concept_stocks             -- 概念成分股
   10. watchlist_stocks          -- 自选股
   11. watchlist_monitoring      -- 自选股异动
   ```

3. **检查表结构**（可选）

   查看某张表的详细结构（以 market_index 为例）：

   ```sql
   SELECT
       column_name,
       data_type,
       character_maximum_length,
       is_nullable
   FROM information_schema.columns
   WHERE table_name = 'market_index'
   ORDER BY ordinal_position;
   ```

---

### Step 5: 配置 Row Level Security (RLS) - 可选

> **说明**: 开发阶段可以先跳过，生产环境建议配置

1. **在 SQL Editor 执行以下 SQL**：

   ```sql
   -- 为所有表启用 RLS
   ALTER TABLE market_index ENABLE ROW LEVEL SECURITY;
   ALTER TABLE market_sentiment ENABLE ROW LEVEL SECURITY;
   ALTER TABLE limit_stocks_detail ENABLE ROW LEVEL SECURITY;
   ALTER TABLE dragon_tiger_board ENABLE ROW LEVEL SECURITY;
   ALTER TABLE dragon_tiger_seats ENABLE ROW LEVEL SECURITY;
   ALTER TABLE institutional_seats ENABLE ROW LEVEL SECURITY;
   ALTER TABLE hot_money_ranking ENABLE ROW LEVEL SECURITY;
   ALTER TABLE hot_concepts ENABLE ROW LEVEL SECURITY;
   ALTER TABLE concept_stocks ENABLE ROW LEVEL SECURITY;
   ALTER TABLE watchlist_stocks ENABLE ROW LEVEL SECURITY;
   ALTER TABLE watchlist_monitoring ENABLE ROW LEVEL SECURITY;

   -- 创建匿名读取策略（允许所有人读取数据）
   CREATE POLICY "Allow anonymous read access" ON market_index
       FOR SELECT USING (true);

   CREATE POLICY "Allow anonymous read access" ON market_sentiment
       FOR SELECT USING (true);

   CREATE POLICY "Allow anonymous read access" ON limit_stocks_detail
       FOR SELECT USING (true);

   CREATE POLICY "Allow anonymous read access" ON dragon_tiger_board
       FOR SELECT USING (true);

   CREATE POLICY "Allow anonymous read access" ON dragon_tiger_seats
       FOR SELECT USING (true);

   CREATE POLICY "Allow anonymous read access" ON institutional_seats
       FOR SELECT USING (true);

   CREATE POLICY "Allow anonymous read access" ON hot_money_ranking
       FOR SELECT USING (true);

   CREATE POLICY "Allow anonymous read access" ON hot_concepts
       FOR SELECT USING (true);

   CREATE POLICY "Allow anonymous read access" ON concept_stocks
       FOR SELECT USING (true);

   CREATE POLICY "Allow anonymous read access" ON watchlist_stocks
       FOR SELECT USING (true);

   CREATE POLICY "Allow anonymous read access" ON watchlist_monitoring
       FOR SELECT USING (true);
   ```

---

## ✅ 验收标准

完成后，你应该能够：

1. ✅ **在 Supabase 项目中看到 11 张表**
   - 路径：左侧菜单 "Table Editor"
   - 能看到所有 11 张表的列表

2. ✅ **`.env` 文件已更新**
   - 包含 `SUPABASE_URL`
   - 包含 `SUPABASE_KEY`
   - 包含 `SUPABASE_ANON_KEY`

3. ✅ **验证查询返回 11 张表**
   ```sql
   SELECT COUNT(*) as table_count
   FROM information_schema.tables
   WHERE table_schema = 'public';
   -- 应返回: table_count = 11
   ```

---

## 🔧 常见问题

### Q1: 执行 SQL 时报错 "syntax error"
**A**: 确保完整复制了 `database/schema.sql` 文件内容，不要有遗漏

### Q2: 看不到 service_role key
**A**: 在 Project Settings > API 页面，找到 "service_role" 行，点击 "Reveal" 按钮显示

### Q3: 执行 SQL 后没有看到表
**A**:
1. 刷新页面
2. 点击左侧 "Table Editor" 查看
3. 或在 SQL Editor 执行验证查询

### Q4: 忘记了 Database Password
**A**:
1. 进入 Project Settings > Database
2. 点击 "Reset database password"
3. 设置新密码

---

## 📝 下一步

完成 Task 1.1 后，继续执行：
- **Task 1.2**: 后端项目初始化
- 需要用到此步骤中记录的 `SUPABASE_URL` 和 `SUPABASE_KEY`

---

**最后更新**: 2025-12-07
**状态**: ⏳ 待执行
