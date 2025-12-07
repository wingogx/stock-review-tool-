# 🚀 快速开始指南

## 第一步：环境准备

### 1. 检查 Python 版本
```bash
python3 --version
# 需要 Python 3.9 或更高版本
```

### 2. 安装 Python 依赖
```bash
pip3 install -r requirements.txt
```

### 3. 检查 Node.js 版本（如果需要前端）
```bash
node --version
# 需要 Node.js 18 或更高版本
```

---

## 第二步：Supabase 配置

### 1. 创建 Supabase 项目

访问 https://supabase.com 并：
- 点击 "Start your project"
- 使用 GitHub 账号登录（推荐）
- 点击 "New Project"
- 填写项目信息：
  - Name: `stock-review` (或你喜欢的名字)
  - Database Password: 设置一个强密码（保存好）
  - Region: 选择 `Southeast Asia (Singapore)` (离中国最近)
- 点击 "Create new project"，等待 1-2 分钟

### 2. 获取 API 凭证

项目创建完成后：
1. 点击左侧 Settings ⚙️
2. 点击 API
3. 复制以下信息：
   - `Project URL` (类似: https://xxxxx.supabase.co)
   - `anon public` key (很长的字符串)

### 3. 创建数据库表

1. 点击左侧 SQL Editor 📝
2. 点击 "+ New query"
3. 复制 `database-schema.sql` 文件的全部内容
4. 粘贴到编辑器中
5. 点击 "Run" 按钮
6. 看到 "Success. No rows returned" 表示成功

### 4. 验证表是否创建成功

1. 点击左侧 Table Editor 📊
2. 应该能看到以下表：
   - market_index
   - limit_stats
   - dragon_tiger_board
   - dragon_tiger_seats
   - hot_concepts
   - watchlist_stocks
   - user_watchlist

---

## 第三步：配置环境变量

### 1. 创建 .env 文件

```bash
# 复制示例文件
cp .env.example .env

# 编辑 .env 文件
nano .env  # 或使用你喜欢的编辑器
```

### 2. 填入 Supabase 凭证

```env
SUPABASE_URL=https://你的项目id.supabase.co
SUPABASE_KEY=你的anon-public-key
```

保存文件（nano: Ctrl+O, Enter, Ctrl+X）

---

## 第四步：测试数据采集

### 1. 手动执行一次采集

```bash
# 确保在项目根目录
cd /Users/win/Documents/ai\ 编程/cc/短信复盘

# 执行数据采集
python3 data-collector.py
```

### 2. 预期输出

```
============================================================
🚀 开始采集 20250207 的股市数据
============================================================

📊 正在获取大盘指数数据...
✅ 上证指数: 3250.12
✅ 深证成指: 10234.56
✅ 创业板指: 2123.45
✅ 成功保存 3 条数据到 market_index

📈 正在获取涨跌停数据...
✅ 涨停: 45只, 跌停: 12只
✅ 成功保存 1 条数据到 limit_stats

🐉 正在获取龙虎榜数据...
✅ 获取到 67 条龙虎榜数据
✅ 成功保存 67 条数据到 dragon_tiger_board

🔥 正在获取热门概念板块数据...
✅ 获取到 20 个热门概念板块
✅ 成功保存 20 条数据到 hot_concepts

============================================================
✅ 数据采集完成!
============================================================
```

### 3. 验证数据

回到 Supabase，点击 Table Editor，检查各个表是否有数据。

---

## 第五步：设置定时任务

### 方式一：使用 APScheduler（推荐新手）

```bash
# 启动调度器
python3 scheduler.py

# 你会看到：
📅 股票数据采集调度器已启动
⏰ 执行时间: 每个交易日 16:00 (周一至周五)
```

保持这个终端窗口运行，每天下午 4 点会自动采集数据。

### 方式二：使用系统 Cron（推荐生产环境）

```bash
# 编辑 crontab
crontab -e

# 添加以下行（将路径改为你的实际路径）
0 16 * * 1-5 cd /Users/win/Documents/ai\ 编程/cc/短信复盘 && /usr/local/bin/python3 data-collector.py >> /tmp/stock-collector.log 2>&1

# 保存并退出
# vim: 按 i 进入编辑模式，按 ESC 后输入 :wq 保存退出
```

### 测试模式（可选）

如果想立即测试定时任务：

```bash
# 每分钟执行一次（用于测试）
python3 scheduler.py --test

# 手动执行一次
python3 scheduler.py --manual
```

---

## 第六步：查看数据（使用 Supabase Dashboard）

### 方法一：在 Supabase 控制台查看

1. 登录 Supabase
2. 点击 Table Editor
3. 选择要查看的表，如 `dragon_tiger_board`
4. 可以看到所有采集到的数据

### 方法二：使用 SQL 查询

1. 点击 SQL Editor
2. 输入查询语句：

```sql
-- 查看今天的龙虎榜数据
SELECT * FROM dragon_tiger_board
WHERE trade_date = CURRENT_DATE
ORDER BY change_pct DESC
LIMIT 10;

-- 查看大盘指数趋势（最近5天）
SELECT trade_date, index_name, close_price, change_pct
FROM market_index
WHERE trade_date >= CURRENT_DATE - INTERVAL '5 days'
ORDER BY trade_date DESC, index_name;

-- 查看涨停股票
SELECT * FROM limit_stats
WHERE trade_date = CURRENT_DATE;
```

---

## 常见问题排查

### ❌ 问题1: `ModuleNotFoundError: No module named 'akshare'`

**解决方案:**
```bash
pip3 install akshare
```

### ❌ 问题2: Supabase 连接失败

**检查清单:**
- ✅ .env 文件是否存在
- ✅ SUPABASE_URL 是否正确（包含 https://）
- ✅ SUPABASE_KEY 是否是 anon public key
- ✅ Supabase 项目是否正常运行

**测试连接:**
```python
from supabase import create_client
import os

url = "你的URL"
key = "你的KEY"

try:
    supabase = create_client(url, key)
    print("✅ 连接成功!")
except Exception as e:
    print(f"❌ 连接失败: {e}")
```

### ❌ 问题3: AKShare 数据获取失败

**可能原因:**
- 网络问题（需要访问国内网站）
- 调用频率过高（等待几秒后重试）
- 数据源暂时不可用

**解决方案:**
```python
import time

# 添加重试机制
max_retries = 3
for i in range(max_retries):
    try:
        df = ak.stock_zh_index_daily(symbol="sh000001")
        break
    except Exception as e:
        if i < max_retries - 1:
            print(f"重试 {i+1}/{max_retries}...")
            time.sleep(5)
        else:
            print(f"获取失败: {e}")
```

### ❌ 问题4: 定时任务没有执行

**检查清单:**
- ✅ 确认当前时间和时区设置
- ✅ 检查 cron 服务是否运行
- ✅ 查看日志文件

**调试命令:**
```bash
# 检查 cron 是否运行
pgrep cron

# 查看 crontab 列表
crontab -l

# 查看系统日志
tail -f /var/log/syslog | grep CRON  # Linux
tail -f /var/log/system.log | grep cron  # macOS
```

---

## 下一步

✅ 数据采集已经可以正常工作！

接下来你可以：

1. **开发前端界面** - 使用 Next.js 展示数据
2. **添加数据分析** - 计算技术指标、资金流向
3. **设置告警** - 监控特定股票的异动
4. **生成报告** - 自动生成每日复盘报告

需要帮助？查看 `README.md` 了解更多功能！

---

**祝你使用愉快！📈**
