"""
市场数据相关的 Pydantic Schema
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import date


# ============================================
# 大盘指数 Schemas
# ============================================

class MarketIndexItem(BaseModel):
    """单个指数数据"""
    index_code: str = Field(..., description="指数代码")
    index_name: str = Field(..., description="指数名称")
    trade_date: str = Field(..., description="交易日期")
    open: Optional[float] = Field(None, description="开盘价", alias="open_price")
    high: Optional[float] = Field(None, description="最高价", alias="high_price")
    low: Optional[float] = Field(None, description="最低价", alias="low_price")
    close: Optional[float] = Field(None, description="收盘价", alias="close_price")
    change_pct: Optional[float] = Field(None, description="涨跌幅(%)")
    volume: Optional[float] = Field(None, description="成交量")
    amount: Optional[float] = Field(None, description="成交额")
    amplitude: Optional[float] = Field(None, description="振幅(%)")
    amount_change_pct: Optional[float] = Field(None, description="成交额环比变化率(%)")

    class Config:
        from_attributes = True
        populate_by_name = True


class MarketIndexResponse(BaseModel):
    """大盘指数响应"""
    success: bool = True
    data: List[MarketIndexItem]
    trade_date: str


# ============================================
# 市场情绪 Schemas
# ============================================

class SentimentScoreDetail(BaseModel):
    """情绪评分明细"""
    up_ratio_score: int = Field(..., description="上涨占比得分(-1/0/+1)")
    amount_change_score: int = Field(..., description="成交额变化得分(-1/0/+1)")
    limit_up_score: int = Field(..., description="涨停数得分(-1/0/+1): >=100→+1, 50-99→0, <50→-1")
    limit_down_score: int = Field(..., description="跌停数得分(-1/0/+1): <=5→+1, 6-15→0, >15→-1")
    explosion_rate_score: int = Field(..., description="炸板率得分(-1/0/+1)")
    total_score: int = Field(..., description="总得分(-5~+5)")
    sentiment_level: str = Field(..., description="情绪等级")
    sentiment_color: str = Field(..., description="情绪颜色标识")


class MarketSentimentItem(BaseModel):
    """市场情绪数据"""
    trade_date: str = Field(..., description="交易日期")
    total_amount: float = Field(..., description="两市总成交额(元)")
    total_amount_change: Optional[float] = Field(None, description="成交额环比变化(元)")
    total_amount_change_pct: Optional[float] = Field(None, description="成交额环比变化率(%)")
    up_count: int = Field(..., description="上涨家数")
    down_count: int = Field(..., description="下跌家数")
    flat_count: int = Field(0, description="平盘家数")
    up_down_ratio: float = Field(..., description="涨跌比")
    prev_up_count: Optional[int] = Field(None, description="昨日上涨家数")
    prev_down_count: Optional[int] = Field(None, description="昨日下跌家数")
    limit_up_count: int = Field(..., description="涨停数量")
    limit_down_count: int = Field(..., description="跌停数量")
    prev_limit_up_count: Optional[int] = Field(None, description="昨日涨停数量")
    prev_limit_down_count: Optional[int] = Field(None, description="昨日跌停数量")
    prev_explosion_rate: Optional[float] = Field(None, description="昨日炸板率(%)")
    continuous_limit_distribution: Dict[str, int] = Field(..., description="连板分布")
    prev_continuous_limit_distribution: Optional[Dict[str, int]] = Field(None, description="前1日连板分布")
    prev2_continuous_limit_distribution: Optional[Dict[str, int]] = Field(None, description="前2日连板分布")
    exploded_count: int = Field(0, description="炸板数量")
    explosion_rate: float = Field(..., description="炸板率(%)")
    market_status: str = Field(default="震荡", description="市场状态: 强势/震荡/弱势")
    sentiment_score: Optional[SentimentScoreDetail] = Field(None, description="情绪评分明细")

    class Config:
        from_attributes = True


class MarketSentimentResponse(BaseModel):
    """市场情绪响应"""
    success: bool = True
    data: MarketSentimentItem


# ============================================
# 市场统计 Schemas
# ============================================

class MarketStatsItem(BaseModel):
    """市场统计数据"""
    trade_date: str
    total_amount_yi: float = Field(..., description="两市总成交额(亿)")
    up_count: int = Field(..., description="上涨家数")
    down_count: int = Field(..., description="下跌家数")
    limit_up_count: int = Field(..., description="涨停数量")
    limit_down_count: int = Field(..., description="跌停数量")
    up_down_ratio: float = Field(..., description="涨跌比")
    market_status: str = Field(..., description="市场状态: 强势/震荡/弱势")


class MarketStatsResponse(BaseModel):
    """市场统计响应"""
    success: bool = True
    data: MarketStatsItem
