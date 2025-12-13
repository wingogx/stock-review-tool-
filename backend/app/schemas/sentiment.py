"""
情绪分析数据模型
"""

from pydantic import BaseModel
from typing import List, Optional


# ========== 模块1：情绪周期仪表盘 ==========

class PromotionDetail(BaseModel):
    """晋级率详情"""
    from_days: int                          # 从N板
    to_days: int                            # 到N+1板
    yesterday_count: int                    # 昨日N板数量
    today_count: int                        # 今日N+1板数量
    rate: float                             # 晋级率(%)


class PremiumStats(BaseModel):
    """昨日涨停溢价统计"""
    avg_premium: Optional[float] = None           # 整体溢价率(%)
    avg_open_premium: Optional[float] = None      # 开盘溢价率(%)
    first_board_premium: Optional[float] = None   # 首板溢价率(%)
    high_board_premium: Optional[float] = None    # 高位板溢价率(%)
    big_loss_rate: Optional[float] = None         # 大面率(%)
    high_board_big_loss_rate: Optional[float] = None  # 高位大面率(%)


class StageDetails(BaseModel):
    """情绪阶段判断详情 (v2.3)"""
    factor_scores: Optional[dict] = None    # 各因子得分
    total_score: Optional[int] = None       # 总分
    had_recent_peak: Optional[bool] = None  # 最近是否有高峰
    is_deteriorating: Optional[bool] = None # 是否恶化中
    stage_raw: Optional[str] = None         # 原始阶段（不带惯性）
    used_inertia: Optional[bool] = None     # 是否使用了惯性
    previous_stage: Optional[str] = None    # 昨日阶段


class EmotionDashboard(BaseModel):
    """情绪周期仪表盘"""
    space_height: int                       # 空间板高度（最高连板数）
    space_height_change: Optional[int] = None  # 空间板高度变化
    limit_up_count: int                     # 涨停数
    limit_up_change: Optional[int] = None   # 涨停数变化
    explosion_rate: float                   # 炸板率(%)
    explosion_rate_change: Optional[float] = None  # 炸板率变化
    overall_promotion_rate: Optional[float] = None  # 整体晋级率(%)
    promotion_details: List[PromotionDetail]  # 分层晋级率
    emotion_stage: str                      # 情绪阶段: 冰点期/回暖期/加速期/高潮期/退潮期
    emotion_stage_color: str                # 阶段颜色: blue/yellow/orange/red/green
    premium_stats: Optional[PremiumStats] = None  # 昨日涨停溢价统计
    stage_details: Optional[StageDetails] = None  # 情绪阶段判断详情


# ========== 模块2：昨日涨停表现 ==========

class BigLossStock(BaseModel):
    """大面个股"""
    stock_code: str
    stock_name: str
    today_change_pct: float                 # 今日涨跌幅
    yesterday_continuous_days: int          # 昨日连板数（1=首板）
    yesterday_opening_times: Optional[int] = None  # 昨日炸板次数
    concepts: List[str]                     # 所属概念


class YesterdayPerformance(BaseModel):
    """昨日涨停表现"""
    yesterday_limit_up_count: int           # 昨日涨停数
    today_avg_change: Optional[float] = None  # 今日平均涨幅
    up_count: int                           # 上涨家数
    down_count: int                         # 下跌家数
    big_loss_count: int                     # 大面数量（跌>5%）
    big_loss_rate: float                    # 大面率(%)
    big_loss_stocks: List[BigLossStock]     # 大面个股列表


# ========== 模块3：概念梯队分析 ==========

class LadderItem(BaseModel):
    """梯队层级"""
    days: int                               # 连板天数
    count: int                              # 该层级股票数量
    stocks: List[str]                       # 股票名称列表


class ConceptLadderItem(BaseModel):
    """概念梯队项"""
    concept_name: str                       # 概念名称
    max_continuous_days: int                # 最高连板数
    total_limit_up_count: int               # 涨停总数
    concept_change_pct: Optional[float] = None  # 板块涨幅
    ladder_status: str                      # 梯队状态: complete/normal/alone
    is_main_line: bool                      # 是否主线板块（TOP10 且 涨停数>=8）
    ladder: List[LadderItem]                # 梯队分布


class ConceptLadder(BaseModel):
    """概念梯队分析"""
    available: bool                         # 是否可用（空间板>=4板）
    concepts: List[ConceptLadderItem]       # 概念梯队列表


# ========== 模块4：龙头股深度分析 ==========

class TechnicalAnalysis(BaseModel):
    """技术面分析"""
    first_limit_time: Optional[str] = None  # 首次封板时间
    first_limit_time_level: str             # 首封评级: strong/normal/weak
    last_limit_time: Optional[str] = None   # 最后封板时间
    opening_times: int                      # 开板次数
    opening_times_level: str                # 开板评级: strong/normal/weak
    turnover_rate: Optional[float] = None   # 换手率
    turnover_rate_level: str                # 换手评级: strong/normal/weak
    amount: Optional[float] = None          # 成交额


class CapitalAnalysis(BaseModel):
    """资金面分析"""
    main_net_inflow: Optional[float] = None  # 主力净流入
    main_net_inflow_level: str              # 净流入评级: strong/normal/weak
    main_net_inflow_pct: Optional[float] = None  # 主力净流入占比
    sealed_amount: Optional[float] = None   # 封单金额
    sealed_ratio: Optional[float] = None    # 封单比（封单/成交）
    sealed_ratio_level: str                 # 封单评级: strong/normal/weak


class StockLadder(BaseModel):
    """股票所属概念梯队"""
    concept_name: Optional[str] = None      # 主概念名称
    status: str                             # 梯队状态: complete/normal/alone
    follower_count: int                     # 跟风股数
    ladder_detail: List[LadderItem]         # 梯队详情


class LeaderEvaluation(BaseModel):
    """龙头综合评估"""
    positive_factors: List[str]             # 利好因素
    negative_factors: List[str]             # 风险因素
    conclusion: str                         # 结论: opportunity/neutral/risk
    conclusion_text: str                    # 结论文本


class LeaderAnalysisItem(BaseModel):
    """龙头股分析项"""
    stock_code: str
    stock_name: str
    continuous_days: int                    # 连板天数
    is_top: bool                            # 是否高标
    concepts: List[str]                     # 所属概念
    industry: Optional[str] = None          # 所属行业
    technical: TechnicalAnalysis            # 技术面分析
    capital: CapitalAnalysis                # 资金面分析
    ladder: StockLadder                     # 梯队情况
    evaluation: LeaderEvaluation            # 综合评估


# ========== API响应 ==========

class SentimentAnalysisData(BaseModel):
    """情绪分析数据"""
    emotion_dashboard: EmotionDashboard     # 情绪周期仪表盘
    yesterday_performance: YesterdayPerformance  # 昨日涨停表现
    concept_ladder: ConceptLadder           # 概念梯队分析
    leader_analysis: List[LeaderAnalysisItem]  # 龙头股深度分析


class SentimentAnalysisResponse(BaseModel):
    """情绪分析API响应"""
    success: bool
    trade_date: str
    data: SentimentAnalysisData
