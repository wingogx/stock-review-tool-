# 短线复盘工具 - 产品需求文档 (PRD)

**文档版本**: v1.0
**创建日期**: 2025-12-07
**产品负责人**: Win
**文档状态**: ✅ 已确认

---

## 📋 目录

1. [产品概述](#1-产品概述)
2. [用户场景](#2-用户场景)
3. [核心功能](#3-核心功能)
4. [技术架构](#4-技术架构)
5. [数据源方案](#5-数据源方案)
6. [数据库设计](#6-数据库设计)
7. [功能优先级](#7-功能优先级)
8. [开发计划](#8-开发计划)
9. [成本分析](#9-成本分析)
10. [附录](#10-附录)

---

## 1. 产品概述

### 1.1 产品定位

**短线复盘工具** 是一款面向短线交易者的每日市场复盘分析系统，帮助用户快速了解当日市场热点、涨停板情况、龙虎榜动态和热门概念板块。

### 1.2 核心价值

- ✅ **节省时间**: 自动采集和整理当日市场数据，无需手动查找
- ✅ **全面分析**: 覆盖大盘、个股、板块、资金等多个维度
- ✅ **热点捕捉**: 快速识别市场热点和龙头股票
- ✅ **数据可视化**: 直观展示市场情绪和趋势变化

### 1.3 目标用户

- **主要用户**: 短线交易者、日内交易者
- **次要用户**: 个人投资者、股票爱好者
- **用户画像**:
  - 关注市场热点和题材炒作
  - 需要每日复盘总结
  - 有一定的技术分析基础

### 1.4 产品形态

- **平台**: Web 网页应用
- **设备**: PC 端为主（支持移动端响应式）
- **部署**: 云端部署（Vercel + Supabase）
- **更新频率**: 每个交易日 16:00 自动更新

---

## 2. 用户场景

### 2.1 每日复盘场景

**场景描述**:
小张是一名短线交易者，每天收盘后（16:00）需要复盘当日市场情况，了解涨停板、龙虎榜和热门概念，为第二天的交易做准备。

**使用流程**:
1. 打开短线复盘工具网页
2. 查看大盘指数涨跌情况
3. 浏览市场情绪指标（涨跌比、连板分布、炸板率）
4. 查看涨停池列表，筛选强势股票
5. 查看龙虎榜，关注机构和游资动向
6. 查看热门概念板块，识别市场热点
7. 检查自选股是否上龙虎榜或在热门概念中

**预期收益**:
- 节省 60% 的复盘时间（从30分钟减少到10分钟）
- 不错过市场热点和强势股票
- 数据全面且准确

---

### 2.2 热点追踪场景

**场景描述**:
小李发现某个概念板块连续上涨，想了解该板块的龙头股、成分股和资金流向。

**使用流程**:
1. 在"热门概念板块"区查看该概念的涨跌幅
2. 点击概念名称查看成分股列表
3. 查看龙头股 TOP3 和涨幅排名
4. 查看该概念中有哪些股票上龙虎榜
5. 分析机构和游资的参与情况

**预期收益**:
- 快速找到板块龙头股
- 了解资金流向和主力动向
- 辅助交易决策

---

### 2.3 自选股监控场景

**场景描述**:
小王有自己的自选股池，想知道自选股中是否有股票涨停、上龙虎榜或进入热门概念。

**使用流程**:
1. 在"自选股监控"区查看自选股列表
2. 系统自动标记：
   - 是否涨停 ⭐
   - 是否上龙虎榜 🏆
   - 是否在热门概念中 🔥
3. 点击查看详细信息

**预期收益**:
- 及时发现自选股异动
- 避免错过重要信息
- 提高交易效率

---

## 3. 核心功能

### 3.1 功能模块总览

| 模块 | 功能描述 | 优先级 |
|-----|---------|--------|
| **大盘指数区** | 显示上证、深证、创业板指数和K线图 | P0 |
| **市场情绪区** | 涨跌比、连板分布、炸板率、市场活跃度 | P0 |
| **涨跌停列表** | 涨停池、跌停池详细信息 | P0 |
| **龙虎榜区** | 龙虎榜明细、机构席位、游资排行 | P0 |
| **热门概念区** | 概念板块、龙头股、概念强度评分 | P0 |
| **自选股监控** | 自选股行情、异动标记 | P1 |
| **数据导出** | 导出复盘报告（PDF/Excel） | P2 |
| **历史对比** | 查看历史数据和趋势对比 | P2 |

---

### 3.2 功能详细说明

#### 3.2.1 大盘指数区 (P0)

**功能描述**:
展示三大指数（上证、深证、创业板）的当日行情和走势图。

**数据字段**:
- 指数名称
- 当前点位
- 涨跌幅（%）
- 涨跌点数
- 振幅（%）
- 成交额（亿元）
- 5-10日 K 线图（迷你图）

**数据来源**: Tushare Pro

**展示形式**:
```
┌─────────────────────────────────────┐
│  上证指数          3,245.67  +1.23% │
│  开: 3,210  高: 3,250  低: 3,205    │
│  振幅: 1.40%  成交额: 4,523亿       │
│  [迷你K线图]                        │
└─────────────────────────────────────┘
```

---

#### 3.2.2 市场情绪区 (P0)

**功能描述**:
通过多个指标综合反映市场情绪。

**数据字段**:

| 指标 | 说明 | 计算方式 |
|-----|------|---------|
| 全市场成交额 | 沪深两市总成交额 | 汇总所有股票成交额 |
| 涨跌家数 | 上涨/下跌股票数量 | 统计涨跌幅 > 0 / < 0 |
| 涨跌比 | 上涨家数 / 下跌家数 | 反映市场强弱 |
| 涨停家数 | 涨停股票数量 | 从涨停池统计 |
| 跌停家数 | 跌停股票数量 | 筛选涨跌幅 <= -9.5% |
| 连板分布 | 2连板、3连板等分布 | 统计连板天数 |
| 炸板率 | 炸板数 / 涨停数 | 反映封板强度 |
| 市场活跃度 | 同花顺独家指标 | AKShare 获取 |

**数据来源**:
- Tushare Pro（市场统计）
- AKShare（涨停池、炸板、市场活跃度）

**展示形式**:
```
┌─────────────────────────────────────┐
│  市场成交额: 12,345 亿               │
│  涨跌家数: 2,845 / 1,823  (1.56)    │
│  涨停/跌停: 73 / 12                  │
│  连板分布: 1板(62) 2板(4) 3板(5)    │
│  炸板率: 28.8%  活跃度: 79.86%      │
└─────────────────────────────────────┘
```

---

#### 3.2.3 涨跌停个股列表 (P0)

**功能描述**:
展示当日所有涨停和跌停股票的详细信息。

**涨停池字段**:
- 股票代码
- 股票名称
- 涨跌幅（%）
- 收盘价（元）
- 成交额（万元）
- 换手率（%）
- 首次封板时间（HH:MM:SS）
- 最后封板时间（HH:MM:SS）
- 连板天数
- 开板次数（炸板次数）
- 所属概念
- 所属行业

**筛选功能**:
- ✅ 过滤 ST 股票
- ✅ 过滤次新股（上市 < 1年）
- ✅ 按连板数排序
- ✅ 按封板时间排序
- ✅ 按成交额排序

**数据来源**: AKShare（字段最详细）

**展示形式**:
```
┌───────────────────────────────────────────────────────────┐
│ 代码     名称    涨幅   价格  成交额  换手  封板时间  连板 │
├───────────────────────────────────────────────────────────┤
│ 300999  金龙鱼  10.01% 15.23  8.5亿  12%  09:31:25   3连板│
│ 600519  贵州茅台 10.00% 1780  12亿   5%   09:45:12   首板 │
│ ...                                                       │
└───────────────────────────────────────────────────────────┘
```

---

#### 3.2.4 龙虎榜区 (P0)

**功能描述**:
展示龙虎榜上榜股票和席位明细，分析机构和游资动向。

**龙虎榜明细字段**:
- 股票代码/名称
- 收盘价
- 涨跌幅
- 上榜原因（日涨幅偏离值、连续三个交易日等）
- 买入前5席位
- 卖出前5席位
- 总买入额（万元）
- 总卖出额（万元）
- 净买入额（万元）

**席位明细字段**:
- 营业部名称
- 买入金额（万元）
- 卖出金额（万元）
- 净买入额（万元）
- 席位类型（机构 / 游资）⭐

**机构席位统计**:
- 机构买入席位数
- 机构卖出席位数
- 机构净买入金额
- 机构买入 TOP5 股票

**游资席位排行**:
- 营业部名称
- 上榜次数
- 总买入金额
- 成功率（次日上涨概率）

**数据来源**: Tushare Pro（核心优势：机构席位自动分类）

**展示形式**:
```
┌─────────────────────────────────────────────────────┐
│ 300999 金龙鱼  涨停  上榜原因: 日涨幅偏离值达7%       │
├─────────────────────────────────────────────────────┤
│ 买入前5席位:                                         │
│  1. 机构专用                    买入 5,000万  ⭐机构 │
│  2. 华泰证券深圳益田路            买入 3,200万  游资  │
│  3. 国泰君安上海江苏路            买入 2,800万  游资  │
│                                                     │
│ 卖出前5席位:                                         │
│  1. 中信证券北京总部             卖出 4,500万  游资  │
│  ...                                                │
└─────────────────────────────────────────────────────┘
```

---

#### 3.2.5 热门概念板块区 (P0)

**功能描述**:
展示当日热门概念板块、龙头股和板块强度。

**概念板块字段**:
- 板块名称
- 板块涨跌幅（%）
- 平均涨幅（%）
- 上涨家数 / 下跌家数
- 涨停家数
- 龙头股 TOP3（股票名称 + 涨幅）
- 前三权重股（可选）
- 概念强度评分（平均涨幅 × 上涨家数）
- 关联自选股（如果用户有自选股在该概念中）

**龙头股识别规则**:
- 取该概念中涨幅最高的前3只股票
- 优先显示涨停股票

**概念强度评分**:
```
概念强度 = 平均涨幅 × 上涨家数
```

**排序方式**:
- 默认按板块涨跌幅排序
- 可按概念强度评分排序
- 可按涨停家数排序

**数据来源**: AKShare（374个热门题材概念）

**展示形式**:
```
┌─────────────────────────────────────────────────────┐
│ AI概念                            涨跌幅: +5.23%    │
│ 上涨: 35家  下跌: 8家  涨停: 5家                     │
│ 龙头股: 科大讯飞(+10.01%) 海康威视(+9.87%)          │
│ 概念强度: 182.5  ⭐⭐⭐                              │
│ 关联自选: 你有 2 只股票在该概念中                    │
└─────────────────────────────────────────────────────┘
```

---

#### 3.2.6 自选股监控区 (P1)

**功能描述**:
监控用户自选股的行情和异动情况。

**监控字段**:
- 股票代码/名称
- 当前价格
- 涨跌幅（%）
- 成交额（亿元）
- 换手率（%）
- 是否涨停 ⭐
- 是否上龙虎榜 🏆
- 是否在热门概念中 🔥
- 所属概念列表
- 是否创新高/新低

**自动标记规则**:
- ⭐ 涨停：涨跌幅 >= 9.5%
- 🏆 上龙虎榜：在龙虎榜表中查询
- 🔥 热门概念：在热门概念TOP10的成分股中

**数据来源**:
- Tushare Pro（个股行情）
- 关联龙虎榜和概念表（SQL JOIN）

**展示形式**:
```
┌─────────────────────────────────────────────────────┐
│ 000001 平安银行  14.25元  +2.34%  成交额: 45亿       │
│ 换手率: 2.5%                                         │
│ 🔥 在热门概念: 金融科技、银行                         │
│ 📊 60日新高                                          │
│                                                     │
│ 300999 金龙鱼   15.23元  +10.01%  成交额: 8.5亿     │
│ ⭐ 涨停  🏆 龙虎榜  🔥 热门概念: 食品饮料            │
│ 📈 3连板                                             │
└─────────────────────────────────────────────────────┘
```

---

## 4. 技术架构

### 4.1 技术栈

| 层级 | 技术选型 | 说明 |
|-----|---------|------|
| **前端** | Next.js 15 | React 框架，支持 SSR |
| | TypeScript | 类型安全 |
| | Tailwind CSS | 样式框架 |
| | Shadcn/ui | UI 组件库 |
| | Recharts / Chart.js | 数据可视化 |
| **后端** | FastAPI | Python 异步 API 框架 |
| | Python 3.10+ | 主要语言 |
| | APScheduler | 定时任务调度 |
| **数据库** | Supabase (PostgreSQL) | 云端数据库 + 实时订阅 |
| **数据源** | Tushare Pro (6000+积分) | 龙虎榜、个股行情、市场统计 |
| | AKShare (免费) | 涨停池、概念板块、市场活跃度 |
| **部署** | Vercel | 前端托管 |
| | Railway / Render | 后端托管 |
| | Supabase Cloud | 数据库托管 |

---

### 4.2 系统架构图

```
┌─────────────────────────────────────────────────────┐
│                   用户浏览器                          │
│                  (Next.js 前端)                      │
└────────────────┬────────────────────────────────────┘
                 │ HTTP/HTTPS
                 ↓
┌─────────────────────────────────────────────────────┐
│                FastAPI 后端                          │
│  ┌─────────────────────────────────────────────┐   │
│  │  API 路由层                                  │   │
│  │  - /api/market-index  (大盘指数)             │   │
│  │  - /api/limit-stocks  (涨停池)               │   │
│  │  - /api/dragon-tiger  (龙虎榜)               │   │
│  │  - /api/hot-concepts  (热门概念)             │   │
│  │  - /api/watchlist     (自选股)               │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │  数据采集层 (Data Collector)                 │   │
│  │  - Tushare Collector (龙虎榜、行情)          │   │
│  │  - AKShare Collector (涨停、概念)            │   │
│  │  - 混合采集器 (HybridDataCollector)          │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │  调度器层 (APScheduler)                      │   │
│  │  - 每日 16:00 触发数据采集                    │   │
│  └─────────────────────────────────────────────┘   │
└────────────────┬────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────┐
│              Supabase (PostgreSQL)                   │
│  ┌─────────────────────────────────────────────┐   │
│  │  数据表 (11张表)                             │   │
│  │  - market_index (大盘指数)                   │   │
│  │  - market_sentiment (市场情绪)               │   │
│  │  - limit_stocks_detail (涨停明细)            │   │
│  │  - dragon_tiger_board (龙虎榜)               │   │
│  │  - institutional_seats (机构席位)            │   │
│  │  - hot_money_ranking (游资排行)              │   │
│  │  - hot_concepts (热门概念)                   │   │
│  │  - watchlist_stocks (自选股)                 │   │
│  │  - ... (其他表)                              │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
                 ↑
                 │
    ┌────────────┴────────────┐
    │                         │
    ↓                         ↓
┌──────────┐           ┌──────────┐
│ Tushare  │           │ AKShare  │
│  6000+   │           │   免费   │
│  积分    │           │          │
└──────────┘           └──────────┘
```

---

### 4.3 数据流程图

```
每日 16:00 自动触发
         │
         ↓
┌─────────────────────┐
│  APScheduler 调度器  │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  混合数据采集器      │
│  (HybridCollector)  │
└──────────┬──────────┘
           │
           ├─────────────────────────────┐
           │                             │
           ↓                             ↓
    ┌──────────┐                  ┌──────────┐
    │ Tushare  │                  │ AKShare  │
    │  采集器  │                  │  采集器  │
    └─────┬────┘                  └─────┬────┘
          │                             │
          │ 1. 龙虎榜（机构席位）         │ 1. 涨停池（详细字段）
          │ 2. 个股行情                 │ 2. 概念板块（374个）
          │ 3. 市场统计                 │ 3. 市场活跃度
          │                             │ 4. 炸板数据
          │                             │
          └─────────┬───────────────────┘
                    │
                    ↓
         ┌─────────────────┐
         │  数据清洗和转换  │
         └─────────┬───────┘
                   │
                   ↓
         ┌─────────────────┐
         │   Supabase DB   │
         │    写入数据      │
         └─────────┬───────┘
                   │
                   ↓
         ┌─────────────────┐
         │  前端 API 请求   │
         │    读取数据      │
         └─────────────────┘
```

---

## 5. 数据源方案

### 5.1 数据源选型

经过全面对比和 Token 验证，最终确定：

**主数据源**: Tushare Pro (6000+ 积分) + AKShare (免费)

### 5.2 Tushare Pro (6000+ 积分)

**优势**:
- ✅ 官方数据源，稳定可靠
- ✅ 龙虎榜机构席位**自动分类**（核心优势）
- ✅ 历史数据完整（可追溯到2005年）
- ✅ 每分钟500次调用，常规数据无限额

**负责的数据**:
1. 龙虎榜每日明细 (`top_list`)
2. 龙虎榜机构明细 (`top_inst`) ⭐ 核心优势
3. 个股日线行情 (`daily`)
4. 每日指标数据 (`daily_basic`)
5. 市场交易统计 (`daily_info`)

**成本**: 500元/年（已投入）

---

### 5.3 AKShare (免费)

**优势**:
- ✅ 完全免费，无需 Token
- ✅ 涨停池字段最详细（封板时间、连板数等）
- ✅ 概念板块最全面（374个热门题材概念）
- ✅ 独家市场活跃度数据
- ✅ 炸板数据专有 API

**负责的数据**:
1. 涨停池详细数据 (`stock_zt_pool_em`) ⭐
2. 炸板数据 (`stock_zt_pool_zbgc_em`) ⭐
3. 概念板块 (`stock_board_concept_name_ths`) ⭐
4. 概念成分股 (`stock_board_concept_cons_em`)
5. 市场活跃度 (`stock_market_activity_legu`) ⭐

**成本**: 0元

---

### 5.4 数据源分工表

| 功能模块 | 使用数据源 | 原因 |
|---------|-----------|------|
| 大盘指数 | Tushare | 官方数据更准确 |
| 市场统计 | Tushare | 官方权威 |
| 涨停池 | **AKShare** ⭐ | 字段最详细（封板时间、连板数） |
| 炸板数据 | **AKShare** ⭐ | Tushare 无此 API |
| 龙虎榜 | **Tushare** ⭐ | 机构席位自动分类 |
| 概念板块 | **AKShare** ⭐ | 374个热门题材（vs Tushare的地域/行业概念） |
| 市场活跃度 | **AKShare** ⭐ | 同花顺独家数据 |
| 个股行情 | Tushare | 官方稳定 |

---

### 5.5 为什么不用纯 Tushare？

虽然你有 6000+ 积分，可以调用 Tushare 的概念板块 API，但仍建议概念数据用 AKShare：

| 对比项 | Tushare 概念 | AKShare 概念 |
|-------|-------------|-------------|
| **概念类型** | 地域（安徽、北京）+ 行业 | **热门题材**（AI、ChatGPT、新能源）⭐ |
| **数量** | 1234个 | 374个（精选） |
| **涨跌幅** | ❌ 无 | ✅ 有 |
| **龙头股识别** | ⚠️ 需额外处理 | ✅ 直接可用 |
| **适用性** | 长线投资 | **短线复盘** ⭐ |

**关键原因**: 短线复盘需要的是**热门题材概念**（AI、新能源汽车、ChatGPT等），而不是静态的地域/行业分类。

---

## 6. 数据库设计

### 6.1 数据库选型

**Supabase (PostgreSQL)**

**选择原因**:
- ✅ 基于 PostgreSQL，功能强大
- ✅ 提供实时订阅功能
- ✅ 自带 Auth 和 Row Level Security
- ✅ 免费额度充足（500MB 数据库）
- ✅ 自动备份和恢复

---

### 6.2 数据表设计（11张表）

#### 6.2.1 核心数据表

**1. market_index** - 大盘指数

```sql
CREATE TABLE market_index (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    index_code VARCHAR(20) NOT NULL,  -- 指数代码（如 000001.SH）
    index_name VARCHAR(50) NOT NULL,  -- 指数名称（如 上证指数）
    open_price DECIMAL(10, 2),
    close_price DECIMAL(10, 2),
    high_price DECIMAL(10, 2),
    low_price DECIMAL(10, 2),
    volume BIGINT,                    -- 成交量
    turnover DECIMAL(20, 2),          -- 成交额
    change_pct DECIMAL(10, 4),        -- 涨跌幅
    amplitude DECIMAL(10, 4),         -- 振幅
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, index_code)
);
```

---

**2. market_sentiment** - 市场情绪

```sql
CREATE TABLE market_sentiment (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL UNIQUE,
    total_amount DECIMAL(20, 2),              -- 全市场成交额
    sh_amount DECIMAL(20, 2),                 -- 沪市成交额
    sz_amount DECIMAL(20, 2),                 -- 深市成交额
    up_count INT,                             -- 上涨家数
    down_count INT,                           -- 下跌家数
    flat_count INT,                           -- 平盘家数
    up_down_ratio DECIMAL(10, 4),             -- 涨跌比
    limit_up_count INT,                       -- 涨停家数
    limit_down_count INT,                     -- 跌停家数
    continuous_limit_distribution JSONB,      -- 连板分布 {"1": 62, "2": 4, "3": 5}
    exploded_count INT,                       -- 炸板数量
    explosion_rate DECIMAL(10, 4),            -- 炸板率
    market_activity DECIMAL(10, 4),           -- 市场活跃度（%）
    suspended_count INT,                      -- 停牌数量
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

**3. limit_stocks_detail** - 涨停股票明细

```sql
CREATE TABLE limit_stocks_detail (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50) NOT NULL,
    limit_type VARCHAR(10) NOT NULL,      -- 'limit_up' / 'limit_down'
    close_price DECIMAL(10, 2),
    change_pct DECIMAL(10, 4),
    turnover DECIMAL(20, 2),              -- 成交额
    turnover_rate DECIMAL(10, 4),         -- 换手率
    first_limit_time TIME,                -- 首次封板时间 ⭐
    last_limit_time TIME,                 -- 最后封板时间 ⭐
    continuous_days INT DEFAULT 1,        -- 连板天数 ⭐
    opening_times INT DEFAULT 0,          -- 开板次数（炸板次数）⭐
    industry VARCHAR(50),                 -- 所属行业
    concepts TEXT[],                      -- 所属概念（数组）
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, stock_code, limit_type)
);
```

---

**4. dragon_tiger_board** - 龙虎榜明细

```sql
CREATE TABLE dragon_tiger_board (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50) NOT NULL,
    close_price DECIMAL(10, 2),
    change_pct DECIMAL(10, 4),
    turnover DECIMAL(20, 2),
    total_buy DECIMAL(20, 2),         -- 总买入额
    total_sell DECIMAL(20, 2),        -- 总卖出额
    net_amount DECIMAL(20, 2),        -- 净买入额
    reason TEXT,                      -- 上榜原因
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, stock_code)
);
```

---

**5. dragon_tiger_seats** - 龙虎榜席位明细

```sql
CREATE TABLE dragon_tiger_seats (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    seat_name TEXT NOT NULL,          -- 营业部名称
    seat_type VARCHAR(20),            -- 'institution' / 'hot_money'
    buy_amount DECIMAL(20, 2),        -- 买入金额
    sell_amount DECIMAL(20, 2),       -- 卖出金额
    net_amount DECIMAL(20, 2),        -- 净买入额
    rank_type VARCHAR(10),            -- 'buy' / 'sell'
    rank INT,                         -- 排名（1-5）
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

**6. institutional_seats** - 机构席位统计

```sql
CREATE TABLE institutional_seats (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    exalter VARCHAR(200),             -- 营业部名称
    buy_amount DECIMAL(20, 2),        -- 买入金额
    buy_rate DECIMAL(10, 4),          -- 买入占比
    sell_amount DECIMAL(20, 2),       -- 卖出金额
    sell_rate DECIMAL(10, 4),         -- 卖出占比
    net_buy DECIMAL(20, 2),           -- 净买入额
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, stock_code, exalter)
);
```

---

**7. hot_money_ranking** - 游资席位排行

```sql
CREATE TABLE hot_money_ranking (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    seat_name TEXT NOT NULL,
    appear_count INT DEFAULT 1,       -- 上榜次数
    total_buy DECIMAL(20, 2),         -- 总买入金额
    total_sell DECIMAL(20, 2),        -- 总卖出金额
    net_amount DECIMAL(20, 2),        -- 净买入额
    win_rate DECIMAL(10, 4),          -- 成功率（次日上涨概率）
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, seat_name)
);
```

---

**8. hot_concepts** - 热门概念板块

```sql
CREATE TABLE hot_concepts (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    concept_name VARCHAR(100) NOT NULL,
    change_pct DECIMAL(10, 4),        -- 板块涨跌幅
    avg_change DECIMAL(10, 4),        -- 平均涨幅
    up_count INT,                     -- 上涨家数
    down_count INT,                   -- 下跌家数
    limit_up_count INT DEFAULT 0,     -- 涨停家数
    leading_stocks TEXT[],            -- 龙头股 TOP3
    top_weights TEXT[],               -- 前三权重股（可选）
    strength_score DECIMAL(10, 4),    -- 概念强度评分
    total_stocks INT,                 -- 成分股总数
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, concept_name)
);
```

---

**9. concept_stocks** - 概念成分股

```sql
CREATE TABLE concept_stocks (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    concept_name VARCHAR(100) NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50) NOT NULL,
    change_pct DECIMAL(10, 4),
    close_price DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, concept_name, stock_code)
);
```

---

**10. watchlist_stocks** - 自选股监控

```sql
CREATE TABLE watchlist_stocks (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50),
    add_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, stock_code)
);
```

---

**11. watchlist_monitoring** - 自选股异动监控

```sql
CREATE TABLE watchlist_monitoring (
    id BIGSERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    user_id UUID REFERENCES auth.users(id),
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50),
    close_price DECIMAL(10, 2),
    change_pct DECIMAL(10, 4),
    turnover DECIMAL(20, 2),
    turnover_rate DECIMAL(10, 4),
    is_limit_up BOOLEAN DEFAULT FALSE,    -- 是否涨停
    is_dragon_tiger BOOLEAN DEFAULT FALSE, -- 是否上龙虎榜
    is_hot_concept BOOLEAN DEFAULT FALSE,  -- 是否在热门概念
    hot_concepts TEXT[],                   -- 所属热门概念列表
    is_new_high BOOLEAN DEFAULT FALSE,     -- 是否创新高
    is_new_low BOOLEAN DEFAULT FALSE,      -- 是否创新低
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(trade_date, user_id, stock_code)
);
```

---

### 6.3 索引设计

```sql
-- 交易日期索引（所有表）
CREATE INDEX idx_market_index_date ON market_index(trade_date);
CREATE INDEX idx_market_sentiment_date ON market_sentiment(trade_date);
CREATE INDEX idx_limit_stocks_date ON limit_stocks_detail(trade_date);
CREATE INDEX idx_dragon_tiger_date ON dragon_tiger_board(trade_date);
CREATE INDEX idx_hot_concepts_date ON hot_concepts(trade_date);

-- 股票代码索引
CREATE INDEX idx_limit_stocks_code ON limit_stocks_detail(stock_code);
CREATE INDEX idx_dragon_tiger_code ON dragon_tiger_board(stock_code);
CREATE INDEX idx_watchlist_code ON watchlist_stocks(stock_code);

-- 用户索引
CREATE INDEX idx_watchlist_user ON watchlist_stocks(user_id);
CREATE INDEX idx_monitoring_user ON watchlist_monitoring(user_id);

-- 组合索引
CREATE INDEX idx_limit_stocks_date_code ON limit_stocks_detail(trade_date, stock_code);
CREATE INDEX idx_dragon_tiger_date_code ON dragon_tiger_board(trade_date, stock_code);
```

---

## 7. 功能优先级

### 7.1 MVP 阶段（P0 - 必须实现）

**目标**: 实现核心复盘功能，满足基本使用需求

**功能列表**:
1. ✅ 大盘指数展示（上证、深证、创业板）
2. ✅ 市场情绪统计（涨跌比、涨停数、连板分布、炸板率）
3. ✅ 涨停池列表（包含封板时间、连板数等详细字段）
4. ✅ 龙虎榜明细（机构席位自动识别）
5. ✅ 热门概念 TOP10（含龙头股）
6. ✅ 数据自动采集（每日16:00）
7. ✅ 基础数据展示（表格形式）

**开发周期**: 2-3周

---

### 7.2 增强阶段（P1 - 重要但不紧急）

**目标**: 增强用户体验，提供更多分析功能

**功能列表**:
1. ✅ 自选股监控（异动自动标记）
2. ✅ 游资席位排行（上榜次数、成功率）
3. ✅ 概念强度评分和排序
4. ✅ 数据可视化（K线图、趋势图）
5. ✅ 筛选和排序功能（按连板数、封板时间等）
6. ✅ 移动端响应式布局

**开发周期**: 2周

---

### 7.3 优化阶段（P2 - 可选功能）

**目标**: 提供高级功能，提升产品竞争力

**功能列表**:
1. ⏭️ 历史数据对比（对比昨日、上周）
2. ⏭️ 数据导出（PDF/Excel 复盘报告）
3. ⏭️ 自定义提醒（涨停提醒、龙虎榜提醒）
4. ⏭️ 多账户支持（不同自选股池）
5. ⏭️ 移动端 App（可选）

**开发周期**: 按需开发

---

## 8. 开发计划

### 8.1 Phase 1: 基础设施搭建（Week 1）

**任务清单**:
- [x] 数据源验证（Tushare Token 测试）✅
- [ ] Supabase 数据库创建
- [ ] 执行数据库 Schema（11张表）
- [ ] Next.js 项目初始化
- [ ] FastAPI 项目初始化
- [ ] 环境变量配置

**交付物**:
- Supabase 数据库已创建并配置
- 前后端项目框架搭建完成

---

### 8.2 Phase 2: 数据采集开发（Week 1-2）

**任务清单**:
- [ ] 实现 Tushare 数据采集器
  - [ ] 龙虎榜数据采集
  - [ ] 个股行情采集
  - [ ] 市场统计采集
- [ ] 实现 AKShare 数据采集器
  - [ ] 涨停池采集
  - [ ] 概念板块采集
  - [ ] 市场活跃度采集
- [ ] 实现混合数据采集器（HybridDataCollector）
- [ ] 配置 APScheduler 定时任务（每日16:00）
- [ ] 数据清洗和转换逻辑
- [ ] 写入 Supabase 数据库
- [ ] 错误处理和日志记录

**交付物**:
- 数据采集脚本可正常运行
- 每日16:00自动采集数据
- 数据成功写入数据库

---

### 8.3 Phase 3: 后端 API 开发（Week 2-3）

**任务清单**:
- [ ] 实现 API 路由
  - [ ] `/api/market-index` - 大盘指数
  - [ ] `/api/market-sentiment` - 市场情绪
  - [ ] `/api/limit-stocks` - 涨停池
  - [ ] `/api/dragon-tiger` - 龙虎榜
  - [ ] `/api/hot-concepts` - 热门概念
  - [ ] `/api/watchlist` - 自选股
- [ ] 数据查询优化（SQL 性能优化）
- [ ] API 文档（Swagger/OpenAPI）
- [ ] 单元测试

**交付物**:
- 所有 API 接口可正常访问
- API 文档完善
- 测试覆盖率 > 80%

---

### 8.4 Phase 4: 前端开发（Week 3-4）

**任务清单**:
- [ ] 页面布局设计
  - [ ] 大盘指数区
  - [ ] 市场情绪区
  - [ ] 涨停池列表
  - [ ] 龙虎榜区
  - [ ] 热门概念区
  - [ ] 自选股监控区
- [ ] 组件开发（使用 Shadcn/ui）
- [ ] 数据可视化（K线图、趋势图）
- [ ] 响应式布局
- [ ] 前后端集成
- [ ] 交互优化

**交付物**:
- 前端页面完整
- 数据展示正常
- 交互流畅

---

### 8.5 Phase 5: 测试和部署（Week 4-5）

**任务清单**:
- [ ] 功能测试（手动测试）
- [ ] 兼容性测试（Chrome、Safari、Firefox）
- [ ] 性能测试（加载速度、查询速度）
- [ ] 数据准确性验证
- [ ] 部署到生产环境
  - [ ] 前端部署到 Vercel
  - [ ] 后端部署到 Railway/Render
  - [ ] 配置域名和 SSL
- [ ] 监控和日志配置
- [ ] 用户文档编写

**交付物**:
- 产品上线并可访问
- 所有功能正常运行
- 用户文档完善

---

## 9. 成本分析

### 9.1 数据源成本

| 数据源 | 类型 | 成本 | 说明 |
|-------|------|------|------|
| Tushare Pro | 付费 | **500元/年** | 6000+积分，已投入 |
| AKShare | 免费 | **0元** | 完全免费 |
| **总计** | - | **500元/年** | - |

---

### 9.2 基础设施成本

| 服务 | 免费额度 | 付费价格 | 预计成本 |
|-----|---------|---------|---------|
| **Supabase** | 500MB 数据库 + 2GB 存储 | $25/月（Pro版） | **0元**（免费版足够） |
| **Vercel** | 100GB 带宽/月 | $20/月（Pro版） | **0元**（免费版足够） |
| **Railway/Render** | 500小时/月 | $5-20/月 | **0元**（免费版足够） |
| **域名** | - | ¥50-100/年 | **可选** |
| **总计** | - | - | **0-100元/年** |

---

### 9.3 总成本

| 类型 | 年度成本 |
|-----|---------|
| 数据源 | 500元 |
| 基础设施 | 0-100元 |
| **总计** | **500-600元/年** |

**对比商业数据源**:
- Wind: 100,000元/年
- 同花顺 iFinD: 30,000元/年
- **节省成本**: 99,400-99,500元/年 ⭐⭐⭐

---

## 10. 附录

### 10.1 相关文档

| 文档名称 | 路径 | 说明 |
|---------|------|------|
| 数据源对比分析 | `数据源对比分析.md` | 完整数据源对比 |
| Tushare 6000积分分析 | `Tushare6000积分更新说明.md` | Token 权限分析 |
| 数据可用性验证 | `数据可用性验证报告.md` | 数据验证报告 |
| 数据库设计 | `database-schema-enhanced.sql` | 数据库 SQL |
| 混合采集器 | `data-collector-tushare-hybrid.py` | 数据采集脚本 |
| Token 测试脚本 | `test-tushare-token.py` | Token 验证脚本 |

---

### 10.2 技术选型理由

**前端 - Next.js 15**
- ✅ React 最新框架，支持 SSR 和 SSG
- ✅ 内置路由和 API 路由
- ✅ 优秀的开发体验
- ✅ Vercel 原生支持，部署简单

**后端 - FastAPI**
- ✅ Python 异步框架，性能优异
- ✅ 自动生成 API 文档
- ✅ 类型提示支持
- ✅ 与数据采集脚本语言一致

**数据库 - Supabase**
- ✅ 基于 PostgreSQL，功能强大
- ✅ 提供实时订阅
- ✅ 自带认证和权限管理
- ✅ 免费额度充足

**数据源 - Tushare + AKShare**
- ✅ 数据质量最高（官方 + 爬虫）
- ✅ 功能最全（互补）
- ✅ 成本最优（500元/年）

---

### 10.3 风险评估

| 风险 | 影响 | 概率 | 应对措施 |
|-----|------|------|---------|
| **数据源不稳定** | 高 | 中 | 双数据源容错，AKShare 备用 |
| **API 限流** | 中 | 低 | 合理控制调用频率，缓存数据 |
| **数据准确性** | 高 | 低 | 数据验证和人工抽查 |
| **服务器宕机** | 中 | 低 | 使用云服务，自动恢复 |
| **成本超支** | 低 | 低 | 使用免费额度，按需升级 |

---

### 10.4 后续优化方向

1. **数据分析增强**
   - 机器学习预测涨停概率
   - 概念轮动分析
   - 资金流向追踪

2. **用户体验优化**
   - 个性化首页
   - 智能推荐热门股票
   - 多种主题皮肤

3. **社交功能**
   - 用户交流社区
   - 复盘笔记分享
   - 策略讨论

4. **移动端**
   - 独立移动 App
   - 实时推送提醒
   - 离线缓存

---

## 📝 更新日志

| 版本 | 日期 | 更新内容 | 作者 |
|-----|------|---------|------|
| v1.0 | 2025-12-07 | 初始版本，完整 PRD | AI Assistant |

---

**文档结束**

如有任何问题或建议，请联系产品负责人。
