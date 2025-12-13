"""
板块分析数据模型
"""

from pydantic import BaseModel
from typing import List, Optional


class TrendSectorItem(BaseModel):
    """趋势板块项"""
    concept_name: str
    day_change_pct: Optional[float] = None      # 当日涨幅
    change_pct: Optional[float] = None          # 5日涨幅
    leader_stock_name: Optional[str] = None     # 龙头股名称
    leader_stock_code: Optional[str] = None     # 龙头股代码
    leader_continuous_days: Optional[int] = None  # 龙头股连板数


class EmotionSectorItem(BaseModel):
    """情绪板块项"""
    concept_name: str
    day_change_pct: Optional[float] = None      # 当日涨幅
    limit_up_count: Optional[int] = None        # 涨停数
    leader_stock_name: Optional[str] = None     # 龙头股名称
    leader_stock_code: Optional[str] = None     # 龙头股代码
    leader_continuous_days: Optional[int] = None  # 龙头股连板数


class MainSectorItem(BaseModel):
    """主线板块项（趋势+情绪交集）"""
    concept_name: str
    consecutive_main_days: int = 1              # 连续主线天数
    first_main_date: Optional[str] = None       # 上榜首日（本轮连续主线的起始日期）
    day_change_pct: Optional[float] = None      # 当日涨幅
    change_pct: Optional[float] = None          # 5日涨幅
    limit_up_count: Optional[int] = None        # 涨停数
    leader_stock_name: Optional[str] = None     # 龙头股名称
    leader_stock_code: Optional[str] = None     # 龙头股代码
    leader_continuous_days: Optional[int] = None  # 龙头股连板数


class AnomalySectorItem(BaseModel):
    """异动板块项"""
    concept_name: str
    day_change_pct: Optional[float] = None      # 当日涨幅
    limit_up_count: Optional[int] = None        # 涨停数
    leader_stock_name: Optional[str] = None     # 龙头股名称
    leader_stock_code: Optional[str] = None     # 龙头股代码
    leader_continuous_days: Optional[int] = None  # 龙头股连板数
    anomaly_type: str                           # 异动类型: limit_up / change_pct


class SectorAnalysisData(BaseModel):
    """板块分析数据"""
    trend_sectors: List[TrendSectorItem]        # 趋势板块（5日涨幅前5）
    emotion_sectors: List[EmotionSectorItem]    # 情绪板块（涨停数>10）
    main_sectors: List[MainSectorItem]          # 主线板块（趋势∩情绪）
    anomaly_sectors: List[AnomalySectorItem]    # 异动板块


class SectorAnalysisResponse(BaseModel):
    """板块分析API响应"""
    success: bool
    trade_date: str
    data: SectorAnalysisData
