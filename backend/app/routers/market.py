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

    评分维度（5项，每项 -1/0/+1，总分范围 -5 ~ +5）：
    1. 上涨占比: >50% +1, 30%-50% 0, <30% -1
    2. 成交额变化: >+10% +1, ±10% 0, <-10% -1
    3. 涨停数（绝对数量）: >=100只 +1, 50-99只 0, <50只 -1
    4. 跌停数（绝对数量）: <=5只 +1, 6-15只 0, >15只 -1
    5. 炸板率: <20% +1, 20%-30% 0, >30% -1

    情绪等级映射：
    +4~+5: 极度亢奋 (深红)
    +2~+3: 情绪偏热 (橙色)
    +1: 情绪偏暖 (黄色)
    0: 情绪中性 (灰色)
    -1: 情绪偏冷 (黄色)
    -2~-3: 情绪偏弱 (蓝色)
    -4~-5: 极度冰点 (绿色)
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

    # 3. 涨停数得分（基于绝对数量，参考市场通用标准）
    # 标准来源：主板涨停<50只为弱势，>100只为强势
    limit_up = data.get('limit_up_count', 0)
    if limit_up >= 100:
        scores['limit_up_score'] = 1      # 强势：做多热情高涨
    elif limit_up >= 50:
        scores['limit_up_score'] = 0      # 中性：正常水平
    else:
        scores['limit_up_score'] = -1     # 弱势：市场情绪不佳

    # 4. 跌停数得分（基于绝对数量，参考市场通用标准）
    # 标准来源：跌停<=5只为情绪高涨，>15只为恐慌
    limit_down = data.get('limit_down_count', 0)
    if limit_down <= 5:
        scores['limit_down_score'] = 1    # 情绪好：恐慌低
    elif limit_down <= 15:
        scores['limit_down_score'] = 0    # 中性：正常水平
    else:
        scores['limit_down_score'] = -1   # 情绪差：恐慌蔓延

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

        # 查询前一交易日数据用于计算成交额环比
        prev_response = supabase.table("market_index").select("index_code,amount").lt(
            "trade_date", trade_date
        ).order("trade_date", desc=True).limit(3).execute()

        # 构建前一日成交额映射
        prev_amount_map = {}
        if prev_response.data:
            for item in prev_response.data:
                if item['index_code'] not in prev_amount_map:
                    prev_amount_map[item['index_code']] = item['amount']

        # 转换数据并计算成交额环比
        indexes = []
        for item in response.data:
            # 计算成交额环比变化率
            index_code = item['index_code']
            current_amount = item.get('amount')
            prev_amount = prev_amount_map.get(index_code)

            if current_amount and prev_amount and prev_amount > 0:
                amount_change_pct = round((current_amount - prev_amount) / prev_amount * 100, 2)
                item['amount_change_pct'] = amount_change_pct
            else:
                item['amount_change_pct'] = None

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
            prev_response = supabase.table("market_sentiment").select("total_amount,up_count,down_count,limit_up_count,limit_down_count,explosion_rate,continuous_limit_distribution").lt(
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

                # 添加前1日涨跌家数
                data['prev_up_count'] = prev_data.get('up_count')
                data['prev_down_count'] = prev_data.get('down_count')

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
                data['prev_up_count'] = None
                data['prev_down_count'] = None
                data['prev_limit_up_count'] = None
                data['prev_limit_down_count'] = None
                data['prev_explosion_rate'] = None
                data['prev_continuous_limit_distribution'] = None
                data['prev2_continuous_limit_distribution'] = None
        except Exception as e:
            # 如果无法获取前一日数据，设置为None
            data['total_amount_change'] = None
            data['total_amount_change_pct'] = None
            data['prev_up_count'] = None
            data['prev_down_count'] = None
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


@router.get("/index/history", summary="获取指数历史K线数据")
async def get_index_history(
    index_code: str = Query("SH000001", description="指数代码"),
    days: int = Query(20, ge=5, le=60, description="查询天数")
):
    """
    获取指数历史K线数据（含走势分析）

    参数:
    - index_code: 指数代码 (SH000001=上证, SZ399001=深证, SZ399006=创业板)
    - days: 查询天数 (5-60天)

    返回:
    - data: K线数据数组（按日期升序，含走势分析字段）
    - trend_analysis: 最新一日的走势分析
      - trend: 震荡/上涨/下跌
      - ma5_position: 当前价格与MA5关系
      - ma10_position: 当前价格与MA10关系
      - ma20_position: 当前价格与MA20关系
      - change_5d: 5日涨跌幅
    """
    try:
        supabase = get_supabase()

        # 查询最近N天数据（已包含走势分析字段）
        response = supabase.table("market_index")\
            .select("*")\
            .eq("index_code", index_code)\
            .order("trade_date", desc=True)\
            .limit(days)\
            .execute()

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail=f"未找到指数 {index_code} 的数据"
            )

        # 按日期升序排列（K线图需要从旧到新）
        data = sorted(response.data, key=lambda x: x['trade_date'])

        # 从最新一条记录获取走势分析（已在采集时计算好）
        latest = data[-1]

        # 生成走势描述
        trend = latest.get("trend")
        change_5d = latest.get("change_5d") or 0
        ma5_pos = latest.get("ma5_position")

        if trend == "上涨":
            description = f"多头排列，价格站上均线，近5日涨{change_5d:.2f}%"
        elif trend == "下跌":
            description = f"空头排列，价格跌破均线，近5日跌{abs(change_5d):.2f}%"
        else:
            if abs(change_5d) < 2:
                description = f"横盘整理，近5日涨跌幅{change_5d:.2f}%，波动较小"
            elif ma5_pos == "above":
                description = f"短期偏强，价格站上MA5，区间震荡"
            elif ma5_pos == "below":
                description = f"短期偏弱，价格跌破MA5，区间震荡"
            else:
                description = f"区间震荡，等待方向选择"

        trend_analysis = {
            "trend": trend,
            "ma5_position": ma5_pos,
            "ma10_position": latest.get("ma10_position"),
            "ma20_position": latest.get("ma20_position"),
            "change_5d": change_5d,
            "current_price": latest.get("close_price"),
            "description": description,
        }

        return {
            "success": True,
            "data": data,
            "total": len(data),
            "trend_analysis": trend_analysis
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取指数历史数据失败: {str(e)}")


def analyze_trend(kline_data: list) -> dict:
    """
    分析指数走势（震荡/上涨/下跌）

    算法逻辑:
    1. 计算MA5, MA10, MA20（根据可用数据调整）
    2. 判断当前价格与均线位置关系
    3. 计算近期涨跌幅
    4. 综合判断走势

    走势判断:
    - 上涨: 价格 > MA5 > MA10 且近5日涨幅 > 2%
    - 下跌: 价格 < MA5 < MA10 且近5日跌幅 > 2%
    - 震荡: 其他情况
    """
    if len(kline_data) < 7:
        return {
            "trend": "数据不足",
            "description": f"历史数据仅{len(kline_data)}天，至少需要7天数据"
        }

    # 获取最新数据
    latest = kline_data[-1]
    close_price = latest['close_price']

    # 从数据库获取MA5, MA10, MA20（使用Tushare提供的均线数据）
    ma5 = latest.get('ma5')
    ma10 = latest.get('ma10')
    ma20 = latest.get('ma20')

    # 计算近5日涨跌幅
    if len(kline_data) >= 6:
        price_5days_ago = kline_data[-6]['close_price']
        change_5d = ((close_price - price_5days_ago) / price_5days_ago) * 100
    else:
        change_5d = 0

    # 判断价格与均线位置关系（支持above/below/equal三种状态）
    def compare_price_ma(price, ma_value):
        """比较价格与均线,返回 above/below/equal"""
        if ma_value is None:
            return "unknown"
        if price > ma_value:
            return "above"
        elif price < ma_value:
            return "below"
        else:
            return "equal"

    ma5_position = compare_price_ma(close_price, ma5)
    ma10_position = compare_price_ma(close_price, ma10)
    ma20_position = compare_price_ma(close_price, ma20)

    # 判断均线排列（需要所有均线都存在）
    ma_aligned_up = (ma5 and ma10 and ma20 and ma5 > ma10 > ma20)  # 多头排列
    ma_aligned_down = (ma5 and ma10 and ma20 and ma5 < ma10 < ma20)  # 空头排列

    # 综合判断走势（根据可用数据调整判断条件）
    if ma20:  # 有20天数据，使用完整判断
        if close_price > ma5 and ma_aligned_up and change_5d > 2:
            trend = "上涨"
            description = f"多头排列，价格站上MA5，近5日涨{change_5d:.2f}%"
        elif close_price < ma5 and ma_aligned_down and change_5d < -2:
            trend = "下跌"
            description = f"空头排列，价格跌破MA5，近5日跌{abs(change_5d):.2f}%"
        else:
            trend = "震荡"
            if abs(change_5d) < 2:
                description = f"横盘整理，近5日涨跌幅{change_5d:.2f}%，波动较小"
            elif close_price > ma5 and close_price < ma10:
                description = f"短期偏强，价格在MA5和MA10之间震荡"
            elif close_price < ma5 and close_price > ma10:
                description = f"短期偏弱，价格在MA5和MA10之间震荡"
            else:
                description = f"区间震荡，均线未形成明确排列"
    else:  # 数据不足20天，使用简化判断（仅MA5和MA10）
        if ma10 and close_price > ma5 > ma10 and change_5d > 2:
            trend = "上涨"
            description = f"价格站上MA5和MA10，近5日涨{change_5d:.2f}%（数据有限，仅供参考）"
        elif ma10 and close_price < ma5 < ma10 and change_5d < -2:
            trend = "下跌"
            description = f"价格跌破MA5和MA10，近5日跌{abs(change_5d):.2f}%（数据有限，仅供参考）"
        else:
            trend = "震荡"
            if abs(change_5d) < 2:
                description = f"横盘整理，近5日涨跌幅{change_5d:.2f}%（数据有限，仅供参考）"
            else:
                description = f"区间震荡，近5日涨跌幅{change_5d:.2f}%（数据有限，仅供参考）"

    return {
        "trend": trend,
        "ma5": round(ma5, 2) if ma5 else None,
        "ma10": round(ma10, 2) if ma10 else None,
        "ma20": round(ma20, 2) if ma20 else None,
        "current_price": round(close_price, 2),
        "change_5d": round(change_5d, 2),
        "ma5_position": ma5_position,
        "ma10_position": ma10_position,
        "ma20_position": ma20_position,
        "description": description
    }


@router.get("/sentiment/history", summary="获取历史市场情绪数据")
async def get_sentiment_history(
    days: int = Query(60, ge=5, le=120, description="查询天数")
):
    """
    获取历史市场情绪数据（用于成交额趋势图等）

    参数:
    - days: 查询天数 (5-120天)

    返回:
    - data: 历史数据数组（按日期升序）
    """
    try:
        supabase = get_supabase()

        # 查询最近N天数据
        response = supabase.table("market_sentiment")\
            .select("trade_date,total_amount,up_count,down_count,limit_up_count,limit_down_count")\
            .order("trade_date", desc=True)\
            .limit(days)\
            .execute()

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="未找到市场情绪历史数据"
            )

        # 按日期升序排列
        data = sorted(response.data, key=lambda x: x['trade_date'])

        return {
            "success": True,
            "data": data,
            "total": len(data)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取市场情绪历史数据失败: {str(e)}")
