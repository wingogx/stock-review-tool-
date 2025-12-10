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
    SentimentScoreDetail,
)


def calculate_sentiment_score(data: dict) -> SentimentScoreDetail:
    """
    计算市场情绪评分

    评分维度：
    1. 上涨占比: >50% +1, 30%-50% 0, <30% -1
    2. 成交额变化: >+10% +1, ±10% 0, <-10% -1
    3. 涨停数变化: 增加 +1, 小幅减少 0, 大幅减少(>30%) -1
    4. 跌停数变化: 减少 +1, 小幅增加 0, 大幅增加(>50%) -1
    5. 炸板率: <20% +1, 20%-30% 0, >30% -1
    """
    scores = {}

    # 1. 上涨占比得分
    up_count = data.get('up_count', 0)
    down_count = data.get('down_count', 0)
    total = up_count + down_count
    up_ratio = (up_count / total * 100) if total > 0 else 0

    if up_ratio > 50:
        scores['up_ratio_score'] = 1
    elif up_ratio < 30:
        scores['up_ratio_score'] = -1
    else:
        scores['up_ratio_score'] = 0

    # 2. 成交额变化得分
    amount_change_pct = data.get('total_amount_change_pct')
    if amount_change_pct is not None:
        if amount_change_pct > 10:
            scores['amount_change_score'] = 1
        elif amount_change_pct < -10:
            scores['amount_change_score'] = -1
        else:
            scores['amount_change_score'] = 0
    else:
        scores['amount_change_score'] = 0

    # 3. 涨停数变化得分
    limit_up = data.get('limit_up_count', 0)
    prev_limit_up = data.get('prev_limit_up_count')
    if prev_limit_up is not None and prev_limit_up > 0:
        if limit_up > prev_limit_up:
            scores['limit_up_change_score'] = 1
        elif limit_up < prev_limit_up * 0.7:  # 降幅超过30%
            scores['limit_up_change_score'] = -1
        else:
            scores['limit_up_change_score'] = 0
    else:
        scores['limit_up_change_score'] = 0

    # 4. 跌停数变化得分
    limit_down = data.get('limit_down_count', 0)
    prev_limit_down = data.get('prev_limit_down_count')
    if prev_limit_down is not None:
        if prev_limit_down == 0:
            # 昨日跌停为0的特殊处理
            if limit_down <= 3:
                scores['limit_down_change_score'] = 0
            else:
                scores['limit_down_change_score'] = -1
        else:
            if limit_down < prev_limit_down:
                scores['limit_down_change_score'] = 1
            elif limit_down > prev_limit_down * 1.5:  # 增幅超过50%
                scores['limit_down_change_score'] = -1
            else:
                scores['limit_down_change_score'] = 0
    else:
        scores['limit_down_change_score'] = 0

    # 5. 炸板率得分
    explosion_rate = data.get('explosion_rate', 0)
    if explosion_rate < 20:
        scores['explosion_rate_score'] = 1
    elif explosion_rate > 30:
        scores['explosion_rate_score'] = -1
    else:
        scores['explosion_rate_score'] = 0

    # 计算总分
    total_score = sum(scores.values())
    scores['total_score'] = total_score

    # 确定情绪等级和颜色
    if total_score >= 4:
        scores['sentiment_level'] = '极度亢奋'
        scores['sentiment_color'] = 'deep_red'
    elif total_score >= 2:
        scores['sentiment_level'] = '情绪偏热'
        scores['sentiment_color'] = 'orange'
    elif total_score == 1:
        scores['sentiment_level'] = '情绪偏暖'
        scores['sentiment_color'] = 'yellow'
    elif total_score == 0:
        scores['sentiment_level'] = '情绪中性'
        scores['sentiment_color'] = 'gray'
    elif total_score == -1:
        scores['sentiment_level'] = '情绪偏冷'
        scores['sentiment_color'] = 'yellow'
    elif total_score >= -3:
        scores['sentiment_level'] = '情绪偏弱'
        scores['sentiment_color'] = 'blue'
    else:
        scores['sentiment_level'] = '极度冰点'
        scores['sentiment_color'] = 'green'

    return SentimentScoreDetail(**scores)

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

        # 查询前一交易日数据用于计算成交量环比
        prev_response = supabase.table("market_index").select("index_code,volume").lt(
            "trade_date", trade_date
        ).order("trade_date", desc=True).limit(3).execute()

        # 构建前一日成交量映射
        prev_volume_map = {}
        if prev_response.data:
            for item in prev_response.data:
                if item['index_code'] not in prev_volume_map:
                    prev_volume_map[item['index_code']] = item['volume']

        # 转换数据并计算成交量环比
        indexes = []
        for item in response.data:
            # 计算成交量环比变化率
            index_code = item['index_code']
            current_volume = item.get('volume')
            prev_volume = prev_volume_map.get(index_code)

            if current_volume and prev_volume and prev_volume > 0:
                volume_change_pct = round((current_volume - prev_volume) / prev_volume * 100, 2)
                item['volume_change_pct'] = volume_change_pct
            else:
                item['volume_change_pct'] = None

            indexes.append(MarketIndexItem.model_validate(item))

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
            prev_response = supabase.table("market_sentiment").select("total_amount,limit_up_count,limit_down_count,explosion_rate,continuous_limit_distribution").lt(
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
                data['prev_explosion_rate'] = prev_data.get('explosion_rate')

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
                data['prev_explosion_rate'] = None
                data['prev_continuous_limit_distribution'] = None
                data['prev2_continuous_limit_distribution'] = None
        except Exception as e:
            # 如果无法获取前一日数据，设置为None
            data['total_amount_change'] = None
            data['total_amount_change_pct'] = None
            data['prev_limit_up_count'] = None
            data['prev_limit_down_count'] = None
            data['prev_explosion_rate'] = None
            data['prev_continuous_limit_distribution'] = None
            data['prev2_continuous_limit_distribution'] = None

        # 计算情绪评分
        sentiment_score = calculate_sentiment_score(data)
        data['sentiment_score'] = sentiment_score

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
