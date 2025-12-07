# Task 1.1: 数据库搭建 - 检查清单

**开始时间**: _______
**完成时间**: _______

---

## ☑️ 操作步骤清单

### Step 1: 创建 Supabase 项目
- [ ] 访问 https://supabase.com
- [ ] 注册/登录账号
- [ ] 创建新项目 `short-term-review`
- [ ] 选择 Region: Northeast Asia (Seoul)
- [ ] 设置并记住 Database Password: __________________
- [ ] 等待项目初始化完成（2-3分钟）

---

### Step 2: 记录连接信息
- [ ] 进入 Project Settings > API
- [ ] 复制 Project URL:
  ```

  ```
- [ ] 复制 anon public key:
  ```

  ```
- [ ] 复制 service_role key (点击 Reveal):
  ```

  ```

---

### Step 3: 更新 .env 文件
- [ ] 打开 `/Users/win/Documents/ai 编程/cc/短信复盘/.env`
- [ ] 添加 `SUPABASE_URL=<你的URL>`
- [ ] 添加 `SUPABASE_KEY=<你的service_role key>`
- [ ] 添加 `SUPABASE_ANON_KEY=<你的anon key>`
- [ ] 保存文件

---

### Step 4: 执行数据库 Schema
- [ ] 在 Supabase 点击左侧 "SQL Editor"
- [ ] 点击 "New query"
- [ ] 打开本地 `database/schema.sql` 文件
- [ ] **完整复制**文件内容（约 500+ 行）
- [ ] 粘贴到 SQL Editor
- [ ] 点击 "Run" 执行
- [ ] 等待执行完成（看到 "Success" 提示）

---

### Step 5: 验证表创建
- [ ] 在 SQL Editor 执行以下验证查询:
  ```sql
  SELECT table_name
  FROM information_schema.tables
  WHERE table_schema = 'public'
  ORDER BY table_name;
  ```
- [ ] 确认返回 **11 张表**:
  - [ ] concept_stocks
  - [ ] dragon_tiger_board
  - [ ] dragon_tiger_seats
  - [ ] hot_concepts
  - [ ] hot_money_ranking
  - [ ] institutional_seats
  - [ ] limit_stocks_detail
  - [ ] market_index
  - [ ] market_sentiment
  - [ ] watchlist_monitoring
  - [ ] watchlist_stocks

---

### Step 6: 检查表结构（可选）
- [ ] 点击左侧 "Table Editor"
- [ ] 能看到所有 11 张表
- [ ] 随机点击一张表，能看到列定义

---

## ✅ 最终验收

- [ ] Supabase 项目已创建并可访问
- [ ] 数据库中有 11 张表
- [ ] `.env` 文件已更新，包含 3 个 Supabase 配置
- [ ] 验证查询执行成功

---

## 📸 截图存档（可选）

建议截图保存以下内容：
1. Supabase 项目仪表板（Dashboard）
2. Table Editor 显示 11 张表
3. 验证查询的执行结果

---

## 🔗 参考文档

- 详细操作指南: `docs/开发指南/Supabase数据库搭建指南.md`
- 数据库 Schema: `database/schema.sql`

---

## ⏭️ 完成后

✅ Task 1.1 完成！

**下一步**: Task 1.2 - 后端项目初始化

---

**完成日期**: _______
**耗时**: _______ 小时
**备注**:
