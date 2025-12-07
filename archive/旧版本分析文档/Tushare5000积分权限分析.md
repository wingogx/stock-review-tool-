# Tushare 5000积分权限分析报告

**测试日期**: 2025-12-07
**你的积分**: 5000
**结论**: ✅ **完全够用！建议作为主数据源**

---

## 📊 5000积分权限总览

### 积分等级对比

| 积分等级 | 每分钟频次 | 每日调用量 | API覆盖率 | 年费 |
|---------|----------|-----------|---------|------|
| 120积分（免费） | 50次 | 8000次 | 基础数据 | 0元 |
| 2000积分 | 200次 | 100000次/API | 60% API | 200元 |
| **5000积分（你的）** | **500次** | **常规数据无上限** | **90% API** | **500元** |
| 10000积分 | 1000次 | 特色数据300次/分钟 | 特色数据 | 1000元 |

### 5000积分的核心优势

1. ✅ **频次充足**: 每分钟500次（vs 2000积分的200次）
2. ✅ **无调用上限**: 常规数据无限制（vs 2000积分的100000次/天）
3. ✅ **覆盖率高**: 90%的API可调用
4. ✅ **数据质量**: 官方权威数据，稳定可靠

---

## ✅ 你的短线复盘项目需求对比

### 1️⃣ 龙虎榜数据 - ✅ 完全满足（Tushare优势）

| API | 数据内容 | 所需积分 | 你是否可用 | 对比AKShare |
|-----|---------|--------|-----------|------------|
| `top_list` | 龙虎榜每日明细 | 2000积分 | ✅ **可用** | AKShare也有 |
| `top_inst` | 龙虎榜机构明细 | 5000积分 | ✅ **可用** | ⭐ **Tushare独有优势** |

**Tushare 优势：**
- ✅ **直接提供机构席位分类**（AKShare需要解析营业部名称中的"机构专用"关键词）
- ✅ 机构买入/卖出金额、占比等详细数据
- ✅ 数据质量更稳定

**示例代码：**
```python
import tushare as ts

ts.set_token('你的token')
pro = ts.pro_api()

# 龙虎榜每日明细
df_list = pro.top_list(trade_date='20251207')

# 龙虎榜机构明细（5000积分独享）
df_inst = pro.top_inst(trade_date='20251207')
```

---

### 2️⃣ 涨停数据 - ⚠️ 部分满足（AKShare更详细）

| API | 数据内容 | 所需积分 | 你是否可用 | 对比AKShare |
|-----|---------|--------|-----------|------------|
| `stk_limit` | 每日涨跌停价格 | 2000积分 | ✅ **可用** | AKShare更详细 |
| `limit_list` | 涨停股票列表 | 2000积分 | ✅ **可用** | AKShare更详细 |
| `limit_step` | 连板天梯 | 8000积分 | ❌ **不可用** | AKShare免费有 |
| 炸板数据 | - | - | ❌ **无此API** | AKShare专有 |

**推荐方案：**
- ✅ **使用 AKShare** 获取涨停池数据
- 原因：AKShare 提供更详细的字段
  - ✅ 首次封板时间
  - ✅ 最后封板时间
  - ✅ 连板数
  - ✅ 开板次数
  - ✅ 炸板次数
  - ✅ 所属行业

**AKShare 示例：**
```python
import akshare as ak

# 涨停池（比Tushare更详细）
zt_df = ak.stock_zt_pool_em(date="20251207")

# 炸板数据（Tushare没有）
zbgc_df = ak.stock_zt_pool_zbgc_em(date="20251207")
```

---

### 3️⃣ 概念板块数据 - ❌ 不满足（继续用AKShare）

| API | 数据内容 | 所需积分 | 你是否可用 | 对比AKShare |
|-----|---------|--------|-----------|------------|
| `concept` | 概念分类 | **6000积分** | ❌ **不可用** | AKShare免费 |
| `concept_detail` | 概念详情 | **6000积分** | ❌ **不可用** | AKShare免费 |
| `ths_index` | 同花顺概念指数 | **6000积分** | ❌ **不可用** | AKShare免费 |

**推荐方案：**
- ✅ **使用 AKShare** 获取概念板块数据
- 原因：
  - ❌ Tushare 需要6000积分（你只有5000）
  - ✅ AKShare 免费且更全面（374个概念 vs Tushare的~300个）
  - ✅ AKShare 包含同花顺数据

**AKShare 示例：**
```python
# 同花顺概念板块（374个）
concepts_df = ak.stock_board_concept_name_ths()

# 概念成分股
stocks_df = ak.stock_board_concept_cons_em(symbol="AI概念")
```

---

### 4️⃣ 个股行情数据 - ✅ 完全满足（Tushare优势）

| API | 数据内容 | 所需积分 | 你是否可用 | 对比AKShare |
|-----|---------|--------|-----------|------------|
| `daily` | 日线行情 | 120积分 | ✅ **可用** | 数据质量相当 |
| `daily_basic` | 每日指标 | 2000积分 | ✅ **可用** | Tushare更全 |
| `adj_factor` | 复权因子 | 2000积分 | ✅ **可用** | Tushare更准确 |

**Tushare 优势：**
- ✅ 官方数据，质量稳定
- ✅ 历史数据完整（可追溯到2005年）
- ✅ 复权因子更准确

---

### 5️⃣ 市场统计数据 - ✅ 完全满足（Tushare优势）

| API | 数据内容 | 所需积分 | 你是否可用 | 对比AKShare |
|-----|---------|--------|-----------|------------|
| `daily_info` | 市场交易统计 | 2000积分 | ✅ **可用** | Tushare官方权威 |
| `stk_surv` | 市场概况 | 2000积分 | ✅ **可用** | Tushare官方权威 |

**Tushare 优势：**
- ✅ 全市场成交额
- ✅ 涨跌家数统计
- ✅ 换手率、市盈率等综合指标

---

## 🎯 最佳数据源组合方案

### 推荐方案：**Tushare（主）+ AKShare（补充）**

```
┌─────────────────────────────────────────────────┐
│          数据源分工表                              │
├─────────────────────────────────────────────────┤
│                                                 │
│  ✅ 使用 Tushare (5000积分)：                     │
│     1. 龙虎榜数据 - top_list, top_inst           │
│        → 机构席位直接获取，无需解析                 │
│     2. 个股行情 - daily, daily_basic             │
│        → 数据质量高，官方稳定                      │
│     3. 市场统计 - daily_info                     │
│        → 官方权威数据                             │
│     4. 财务数据 - income, balancesheet           │
│        → 如需要的话                               │
│                                                 │
│  ✅ 使用 AKShare (免费)：                         │
│     1. 涨停池详细数据 - stock_zt_pool_em          │
│        → 包含封板时间、连板数等详细字段             │
│     2. 概念板块数据 - stock_board_concept_name_ths │
│        → 374个概念，比Tushare更全                 │
│     3. 市场活跃度 - stock_market_activity_legu    │
│        → 同花顺独家数据                           │
│     4. 炸板数据 - stock_zt_pool_zbgc_em          │
│        → Tushare没有专门的炸板API                 │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 📋 功能覆盖度对比表

| 功能需求 | Tushare (5000积分) | AKShare (免费) | 推荐使用 |
|---------|-------------------|---------------|---------|
| 龙虎榜每日明细 | ✅ 可用 | ✅ 可用 | **Tushare** |
| 龙虎榜机构席位 | ✅ **直接分类** | ⚠️ 需解析 | **Tushare** ⭐ |
| 涨停池基础数据 | ✅ 可用 | ✅ 可用 | 都可以 |
| 涨停详细字段（封板时间等） | ⚠️ 字段少 | ✅ **详细** | **AKShare** ⭐ |
| 连板天梯 | ❌ 需8000积分 | ✅ 可计算 | **AKShare** |
| 炸板数据 | ❌ 无API | ✅ **专有** | **AKShare** ⭐ |
| 概念板块 | ❌ 需6000积分 | ✅ **374个** | **AKShare** ⭐ |
| 市场活跃度 | ⚠️ 无独立API | ✅ **独家** | **AKShare** ⭐ |
| 个股行情 | ✅ **官方稳定** | ✅ 可用 | **Tushare** |
| 市场统计 | ✅ **官方权威** | ✅ 可用 | **Tushare** |

---

## 💡 具体实施建议

### 1. 数据采集策略

创建混合数据源采集器，充分利用两个数据源的优势：

```python
class HybridDataCollector:
    def __init__(self):
        # 初始化 Tushare
        ts.set_token('你的token')
        self.pro = ts.pro_api()

    def collect_all_data(self):
        # 1. Tushare: 龙虎榜（利用5000积分优势）
        dragon_tiger = self.get_dragon_tiger_tushare()

        # 2. AKShare: 涨停池（字段更详细）
        limit_stocks = self.get_limit_stocks_akshare()

        # 3. AKShare: 概念板块（免费更全面）
        concepts = self.get_concepts_akshare()

        # 4. Tushare: 市场统计（官方权威）
        market_stats = self.get_market_stats_tushare()

        # 5. AKShare: 市场活跃度（独家数据）
        market_activity = self.get_market_sentiment_akshare()
```

### 2. 容错处理

添加双数据源容错机制：

```python
def get_dragon_tiger_data(self):
    """龙虎榜数据 - Tushare优先，AKShare备用"""
    try:
        # 优先使用 Tushare（机构席位分类更好）
        return self.get_dragon_tiger_tushare()
    except Exception as e:
        logger.warning(f"Tushare 失败，尝试 AKShare: {e}")
        # 备用 AKShare
        return self.get_dragon_tiger_akshare()
```

### 3. 成本优化

- ✅ Tushare 5000积分：500元/年（已投入）
- ✅ AKShare：完全免费
- ✅ 总成本：500元/年（仅Tushare）

对比商业数据源：
- ❌ Wind：10万+/年
- ❌ 同花顺 iFinD：数万/年
- ❌ 东方财富 Choice：数万/年

**节省成本：99,500元/年！**

---

## ⚠️ 5000积分的限制

### 无法访问的数据（需更高积分）

| 功能 | 所需积分 | 是否需要 | 解决方案 |
|-----|---------|---------|---------|
| 连板天梯 | 8000积分 | ⚠️ 可选 | AKShare可计算 |
| 概念板块 | 6000积分 | ✅ **需要** | ✅ **AKShare免费替代** |
| 最强板块 | 8000积分 | ⚠️ 可选 | AKShare可计算 |
| 分钟数据 | 单独付费 | ❌ 不需要 | - |

### 结论

**5000积分已完全满足你的短线复盘项目需求！**

唯一的"不足"是概念板块数据（需6000积分），但 AKShare 提供了免费且更全面的替代方案（374个概念）。

---

## 📊 数据质量对比

### Tushare 优势

1. ✅ **数据来源权威** - 直接来自交易所和监管机构
2. ✅ **历史数据完整** - 可追溯到2005年
3. ✅ **稳定性高** - 企业级服务，很少宕机
4. ✅ **机构席位分类** - 直接提供，无需解析

### AKShare 优势

1. ✅ **完全免费** - 无需任何费用
2. ✅ **字段详细** - 涨停数据包含封板时间、连板数等
3. ✅ **概念全面** - 374个概念（vs Tushare的~300个）
4. ✅ **独家数据** - 市场活跃度、炸板数据等

---

## ✅ 最终建议

### 对于你的5000积分Tushare账号：

1. ✅ **值得使用** - 充分利用5000积分的优势
2. ✅ **主数据源** - 龙虎榜、个股行情、市场统计用Tushare
3. ✅ **补充AKShare** - 概念板块、涨停详情、市场活跃度用AKShare
4. ✅ **成本最优** - 500元/年即可获得企业级数据质量

### 数据采集流程：

```
1. Tushare: 龙虎榜（含机构席位） ← 5000积分优势
2. AKShare: 涨停池（详细字段） ← 免费优势
3. AKShare: 概念板块（374个） ← 免费优势
4. Tushare: 市场统计（官方权威） ← 质量优势
5. AKShare: 市场活跃度（独家） ← 独家优势
```

---

## 📚 参考资源

- **Tushare 官方文档**: https://tushare.pro/document/1
- **积分权限表**: https://tushare.pro/document/1?doc_id=290
- **AKShare 官方文档**: https://akshare.akfamily.xyz/
- **混合采集器代码**: `data-collector-tushare-hybrid.py`

---

**创建时间**: 2025-12-07
**你的积分**: 5000（完全够用）
**推荐方案**: Tushare（主）+ AKShare（补充）

**核心结论：5000积分的Tushare + 免费的AKShare = 完美组合！** 🎉
