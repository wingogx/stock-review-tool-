"""
涨停池相关的 Pydantic Schema
"""

from pydantic import BaseModel, Field
from typing import Optional, List


# ============================================
# 涨停股票 Schemas
# ============================================

class LimitStockItem(BaseModel):
    """单个涨停股票"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    trade_date: str = Field(..., description="交易日期")
    limit_type: str = Field(..., description="类型: limit_up/limit_down")
    change_pct: Optional[float] = Field(None, description="涨跌幅(%)")
    close_price: Optional[float] = Field(None, description="收盘价")
    turnover_rate: Optional[float] = Field(None, description="换手率(%)")
    amount: Optional[float] = Field(None, description="成交额")
    first_limit_time: Optional[str] = Field(None, description="首次封板时间")
    last_limit_time: Optional[str] = Field(None, description="最后封板时间")
    continuous_days: Optional[int] = Field(None, description="连板天数")
    opening_times: Optional[int] = Field(None, description="开板次数")
    sealed_amount: Optional[float] = Field(None, description="封单金额")
    market_cap: Optional[float] = Field(None, description="总市值")
    circulation_market_cap: Optional[float] = Field(None, description="流通市值")
    concepts: Optional[List[str]] = Field(default_factory=list, description="所属概念")
    is_strong_limit: Optional[bool] = Field(None, description="是否一字板")
    limit_stats: Optional[str] = Field(None, description="涨停统计")
    industry: Optional[str] = Field(None, description="所属行业")

    class Config:
        from_attributes = True


class LimitStocksResponse(BaseModel):
    """涨停股票列表响应"""
    success: bool = True
    data: List[LimitStockItem]
    total: int
    page: int
    page_size: int


# ============================================
# 涨停统计 Schemas
# ============================================

class LimitStatsItem(BaseModel):
    """涨停统计数据"""
    trade_date: str
    limit_up_count: int = Field(..., description="涨停数量")
    limit_down_count: int = Field(..., description="跌停数量")
    continuous_distribution: dict = Field(..., description="连板分布")
    strong_limit_count: int = Field(..., description="一字板数量")
    exploded_count: int = Field(..., description="炸板数量")
    explosion_rate: float = Field(..., description="炸板率(%)")


class LimitStatsResponse(BaseModel):
    """涨停统计响应"""
    success: bool = True
    data: LimitStatsItem
