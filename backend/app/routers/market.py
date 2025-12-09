"""
市场数据相关 API 路由
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime
import json

from app.utils.supabase_client import get_supabase
from app.utils.trading_date import get_latest_trading_date
from app.schemas.market import (
    MarketIndexResponse,
    MarketIndexItem,
    MarketSentimentResponse,
    MarketSentimentItem,
    MarketStatsResponse,
    MarketStatsItem,
)

router = APIRouter()


@router.get("/index", response_model=MarketIndexResponse, response_model_by_alias=False, summary="获取大盘指数数据")
async def get_market_index(
    trade_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD，默认为最近交易日")
):
    """
    获取大盘指数数据（上证、深证、创业板）

    - **trade_date**: 交易日期，格式 YYYY-MM-DD，不传则返回最近交易日数据
    """
    try:
        # 使用最近交易日
        if not trade_date:
            trade_date = get_latest_trading_date()

        supabase = get_supabase()

        # 查询指数数据
        response = supabase.table("market_index").select("*").eq(
            "trade_date", trade_date
        ).order("index_code").execute()

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail=f"未找到 {trade_date} 的大盘指数数据"
            )

        # 转换数据
        indexes = [MarketIndexItem.model_validate(item) for item in response.data]

        return MarketIndexResponse(
            success=True,
            data=indexes,
            trade_date=trade_date
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取大盘指数失败: {str(e)}")


@router.get("/sentiment", response_model=MarketSentimentResponse, summary="获取市场情绪数据")
async def get_market_sentiment(
    trade_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD，默认为最近交易日")
):
    """
    获取市场情绪数据

    包含：
    - 涨跌家数、涨跌比
    - 涨停数、跌停数
    - 连板分布
    - 炸板率
    - 两市成交额（含环比）
    """
    try:
        if not trade_date:
            trade_date = get_latest_trading_date()

        supabase = get_supabase()

        # 查询市场情绪数据
        response = supabase.table("market_sentiment").select("*").eq(
            "trade_date", trade_date
        ).execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"未找到 {trade_date} 的市场情绪数据"
            )

        data = response.data[0]

        # 解析 JSON 字段
        if isinstance(data.get('continuous_limit_distribution'), str):
            data['continuous_limit_distribution'] = json.loads(data['continuous_limit_distribution'])

        # 查询前两个交易日的数据以计算环比和对比
        try:
            prev_response = supabase.table("market_sentiment").select("total_amount,limit_up_count,limit_down_count,continuous_limit_distribution").lt(
                "trade_date", trade_date
            ).order("trade_date", desc=True).limit(2).execute()

            if prev_response.data and len(prev_response.data) > 0:
                # 前1个交易日数据
                prev_data = prev_response.data[0]
                prev_total_amount = prev_data['total_amount']
                current_total_amount = data['total_amount']

                # 计算环比变化
                total_amount_change = current_total_amount - prev_total_amount
                total_amount_change_pct = (total_amount_change / prev_total_amount * 100) if prev_total_amount > 0 else 0

                data['total_amount_change'] = round(total_amount_change, 2)
                data['total_amount_change_pct'] = round(total_amount_change_pct, 2)

                # 添加前1日涨停跌停数据
                data['prev_limit_up_count'] = prev_data.get('limit_up_count')
                data['prev_limit_down_count'] = prev_data.get('limit_down_count')

                # 添加前1日连板分布
                prev_distribution = prev_data.get('continuous_limit_distribution')
                if isinstance(prev_distribution, str):
                    data['prev_continuous_limit_distribution'] = json.loads(prev_distribution)
                else:
                    data['prev_continuous_limit_distribution'] = prev_distribution

                # 前2个交易日数据（如果存在）
                if len(prev_response.data) > 1:
                    prev2_data = prev_response.data[1]
                    prev2_distribution = prev2_data.get('continuous_limit_distribution')
                    if isinstance(prev2_distribution, str):
                        data['prev2_continuous_limit_distribution'] = json.loads(prev2_distribution)
                    else:
                        data['prev2_continuous_limit_distribution'] = prev2_distribution
                else:
                    data['prev2_continuous_limit_distribution'] = None
            else:
                # 如果无法获取前一日数据，设置为None
                data['total_amount_change'] = None
                data['total_amount_change_pct'] = None
                data['prev_limit_up_count'] = None
                data['prev_limit_down_count'] = None
                data['prev_continuous_limit_distribution'] = None
                data['prev2_continuous_limit_distribution'] = None
        except Exception as e:
            # 如果无法获取前一日数据，设置为None
            data['total_amount_change'] = None
            data['total_amount_change_pct'] = None
            data['prev_limit_up_count'] = None
            data['prev_limit_down_count'] = None
            data['prev_continuous_limit_distribution'] = None
            data['prev2_continuous_limit_distribution'] = None

        sentiment = MarketSentimentItem(**data)

        return MarketSentimentResponse(
            success=True,
            data=sentiment
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取市场情绪失败: {str(e)}")


@router.get("/stats", response_model=MarketStatsResponse, summary="获取市场统计数据")
async def get_market_stats(
    trade_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD，默认为最近交易日")
):
    """
    获取市场统计数据

    包含：
    - 两市总成交额
    - 涨跌家数和涨跌比
    - 涨停数和跌停数
    - 市场状态评估（强势/震荡/弱势）
    """
    try:
        if not trade_date:
            trade_date = get_latest_trading_date()

        supabase = get_supabase()

        # 查询市场情绪数据
        response = supabase.table("market_sentiment").select("*").eq(
            "trade_date", trade_date
        ).execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"未找到 {trade_date} 的市场数据"
            )

        data = response.data[0]

        # 计算市场状态
        up_down_ratio = data['up_down_ratio']
        limit_up_count = data['limit_up_count']

        if up_down_ratio >= 1.5 and limit_up_count >= 50:
            market_status = "强势"
        elif up_down_ratio >= 0.8 and limit_up_count >= 20:
            market_status = "震荡"
        else:
            market_status = "弱势"

        stats = MarketStatsItem(
            trade_date=data['trade_date'],
            total_amount_yi=round(data['total_amount'] / 1e8, 2),
            up_count=data['up_count'],
            down_count=data['down_count'],
            limit_up_count=data['limit_up_count'],
            limit_down_count=data['limit_down_count'],
            up_down_ratio=data['up_down_ratio'],
            market_status=market_status
        )

        return MarketStatsResponse(
            success=True,
            data=stats
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取市场统计失败: {str(e)}")
