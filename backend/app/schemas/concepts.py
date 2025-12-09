"""
概念板块相关的 Pydantic Schema
"""

from pydantic import BaseModel, Field
from typing import Optional, List


# ============================================
# 热门概念 Schemas
# ============================================

class HotConceptItem(BaseModel):
    """单个热门概念"""
    concept_name: str = Field(..., description="概念名称")
    trade_date: str = Field(..., description="交易日期")
    day_change_pct: Optional[float] = Field(None, description="当日涨幅(%)")
    change_pct: float = Field(..., description="近5日涨幅(%)")
    consecutive_days: Optional[int] = Field(None, description="连续上榜次数")
    concept_strength: Optional[float] = Field(None, description="概念强度")
    rank: Optional[int] = Field(None, description="排名")
    is_new_concept: Optional[bool] = Field(None, description="是否新概念")
    first_seen_date: Optional[str] = Field(None, description="首次出现日期")
    limit_up_count: Optional[int] = Field(None, description="涨停股数量")
    total_count: Optional[int] = Field(None, description="成分股总数")
    leader_stock_code: Optional[str] = Field(None, description="龙头股代码")
    leader_stock_name: Optional[str] = Field(None, description="龙头股名称")
    leader_continuous_days: Optional[int] = Field(None, description="龙头股连板天数")
    leader_change_pct: Optional[float] = Field(None, description="龙头股当日涨幅(%)")

    class Config:
        from_attributes = True


class HotConceptsResponse(BaseModel):
    """热门概念列表响应"""
    success: bool = True
    data: List[HotConceptItem]
    total: int


# ============================================
# 概念成分股 Schemas
# ============================================

class ConceptStockItem(BaseModel):
    """概念成分股"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    change_pct: float = Field(..., description="涨跌幅(%)")
    close_price: Optional[float] = Field(None, description="收盘价")
    turnover_rate: Optional[float] = Field(None, description="换手率")
    amount: Optional[float] = Field(None, description="成交额")
    is_limit_up: bool = Field(False, description="是否涨停")
    is_leader: bool = Field(False, description="是否龙头")

    class Config:
        from_attributes = True


class ConceptStocksResponse(BaseModel):
    """概念成分股响应"""
    success: bool = True
    concept_name: str
    data: List[ConceptStockItem]
    total: int


# ============================================
# 概念详情 Schemas
# ============================================

class ConceptDetailResponse(BaseModel):
    """概念详情响应"""
    success: bool = True
    concept_name: str
    trade_date: str
    change_pct: float
    concept_strength: Optional[float]
    rank: Optional[int]
    top_stocks: List[ConceptStockItem]
