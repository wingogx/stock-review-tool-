"""
情绪分析API路由
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from loguru import logger

from app.schemas.sentiment import SentimentAnalysisResponse
from app.services.sentiment_service import SentimentService

router = APIRouter(prefix="/api/sentiment", tags=["情绪分析"])


@router.get("/analysis", response_model=SentimentAnalysisResponse, summary="获取情绪分析数据")
async def get_sentiment_analysis(
    trade_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD，默认最新交易日"),
):
    """
    获取情绪分析完整数据

    包含四大模块：
    - **情绪周期仪表盘**: 空间板高度、晋级率、炸板率、情绪阶段判断
    - **昨日涨停表现**: 昨日涨停数、大面数量、大面率、大面个股列表
    - **概念梯队分析**: 4板+概念的梯队分布、梯队完整度（空间板>=4板时展示）
    - **龙头股深度分析**: 4板+龙头的技术面、资金面、梯队情况、综合评估
    """
    try:
        service = SentimentService()
        result = await service.get_analysis(trade_date)
        logger.info(f"情绪分析数据获取成功: {result['trade_date']}")
        return result

    except Exception as e:
        logger.error(f"获取情绪分析数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取情绪分析数据失败: {str(e)}")
