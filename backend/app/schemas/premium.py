"""
明日溢价概率评分数据模型
"""

from pydantic import BaseModel
from typing import Optional


# ========== 各维度评分详情 ==========

class TechnicalScoreDetail(BaseModel):
    """技术面评分详情"""
    first_limit_time: Optional[str] = None      # 首次封板时间
    opening_times: int                          # 开板次数
    turnover_rate: Optional[float] = None       # 换手率(%)
    is_one_word: bool                           # 是否一字板
    time_score: float                           # 封板时间得分
    turnover_score: float                       # 换手率得分
    final_score: float                          # 技术面最终得分(-2 ~ +2)


class CapitalScoreDetail(BaseModel):
    """资金面评分详情"""
    sealed_amount: Optional[float] = None       # 封单金额(万元)
    amount: Optional[float] = None              # 成交额(万元)
    sealed_ratio: Optional[float] = None        # 封单比(封单/成交)
    main_net_inflow: Optional[float] = None     # 主力净流入(万元)
    main_net_inflow_pct: Optional[float] = None # 主力净流入占比(%)
    sealed_score: float                         # 封单比得分
    inflow_score: float                         # 主力净流入得分
    final_score: float                          # 资金面最终得分(-2 ~ +2)


class ThemeScoreDetail(BaseModel):
    """题材地位评分详情"""
    main_concept: Optional[str] = None          # 主概念名称
    is_in_top10: bool                           # 是否在前十热门概念
    is_main_line: bool                          # 是否主线板块
    ladder_status: str                          # 梯队状态: complete/normal/alone
    theme_hot_score: float                      # 题材热度得分
    ladder_score: float                         # 梯队状态得分
    final_score: float                          # 题材地位最终得分(-2 ~ +2)


class PositionScoreDetail(BaseModel):
    """位置风险评分详情"""
    continuous_days: int                        # 连板天数
    position_risk_level: str                    # 风险等级: 极高/高/中/低/极低
    final_score: float                          # 位置风险得分(-2 ~ +2)


class MarketScoreDetail(BaseModel):
    """市场环境评分详情"""
    emotion_stage: str                          # 情绪阶段
    emotion_stage_color: str                    # 阶段颜色
    final_score: float                          # 市场环境得分(-2 ~ +2)


# ========== 溢价评分结果 ==========

class PremiumScoreResult(BaseModel):
    """明日溢价概率评分结果"""
    # 基础信息
    stock_code: str
    stock_name: str
    trade_date: str

    # 总分和等级
    total_score: float                          # 总分(-9 ~ +9)
    premium_level: str                          # 溢价等级: 极高/高/偏高/中性/偏低/低
    premium_level_color: str                    # 等级颜色

    # 各维度得分
    technical_score: float                      # 技术面得分(-2 ~ +2)
    capital_score: float                        # 资金面得分(-2 ~ +2)
    theme_score: float                          # 题材地位得分(-2 ~ +2)
    position_score: float                       # 位置风险得分(-2 ~ +2)
    market_score: float                         # 市场环境得分(-1 ~ +1)

    # 详细评分信息
    technical_detail: TechnicalScoreDetail      # 技术面详情
    capital_detail: CapitalScoreDetail          # 资金面详情
    theme_detail: ThemeScoreDetail              # 题材地位详情
    position_detail: PositionScoreDetail        # 位置风险详情
    market_detail: MarketScoreDetail            # 市场环境详情


# ========== API响应 ==========

class PremiumScoreResponse(BaseModel):
    """溢价评分API响应"""
    success: bool
    data: PremiumScoreResult
