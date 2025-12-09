"""
涨停池相关 API 路由
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import json

from app.utils.supabase_client import get_supabase
from app.utils.trading_date import get_latest_trading_date
from app.schemas.limit_stocks import (
    LimitStocksResponse,
    LimitStockItem,
    LimitStatsResponse,
    LimitStatsItem,
)

router = APIRouter()


@router.get("/stocks", response_model=LimitStocksResponse, summary="获取涨停/跌停股票列表")
async def get_limit_stocks(
    trade_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD"),
    limit_type: str = Query("limit_up", description="类型: limit_up(涨停) / limit_down(跌停)"),
    min_continuous_days: Optional[int] = Query(None, description="最小连板天数"),
    continuous_days: Optional[int] = Query(None, description="精确连板天数"),
    filter_st: bool = Query(False, description="是否过滤ST股票"),
    order_by: str = Query("continuous_days", description="排序字段: continuous_days/change_pct/amount"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
):
    """
    获取涨停/跌停股票列表

    支持的筛选条件：
    - limit_type: 涨停或跌停
    - min_continuous_days: 最小连板天数（仅涨停有效）
    - filter_st: 是否过滤ST股票
    - order_by: 排序字段

    支持分页
    """
    try:
        if not trade_date:
            trade_date = get_latest_trading_date()

        supabase = get_supabase()

        # 构建查询
        query = supabase.table("limit_stocks_detail").select("*", count="exact")
        query = query.eq("trade_date", trade_date).eq("limit_type", limit_type)

        # 筛选连板天数（精确匹配优先）
        if continuous_days is not None and limit_type == "limit_up":
            query = query.eq("continuous_days", continuous_days)
        elif min_continuous_days is not None and limit_type == "limit_up":
            query = query.gte("continuous_days", min_continuous_days)

        # 过滤 ST
        if filter_st:
            query = query.not_.like("stock_name", "%ST%")

        # 排序（Supabase 格式）
        order_mapping = {
            "continuous_days": ("continuous_days", {"desc": True, "nullsfirst": True}),
            "change_pct": ("change_pct", {"desc": True, "nullsfirst": True}),
            "amount": ("amount", {"desc": True, "nullsfirst": True}),
        }
        order_field, order_opts = order_mapping.get(order_by, ("continuous_days", {"desc": True, "nullsfirst": True}))
        query = query.order(order_field, **order_opts)

        # 分页
        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1)

        # 执行查询
        response = query.execute()

        # 处理数据
        stocks = []
        for item in response.data:
            # 解析 concepts 字段
            if isinstance(item.get('concepts'), str):
                try:
                    item['concepts'] = json.loads(item['concepts'])
                except:
                    item['concepts'] = []
            elif item.get('concepts') is None:
                item['concepts'] = []

            stocks.append(LimitStockItem(**item))

        total = response.count if response.count is not None else len(stocks)

        return LimitStocksResponse(
            success=True,
            data=stocks,
            total=total,
            page=page,
            page_size=page_size
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取涨停股票失败: {str(e)}")


@router.get("/stats", response_model=LimitStatsResponse, summary="获取涨停统计数据")
async def get_limit_stats(
    trade_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD")
):
    """
    获取涨停统计数据

    包含：
    - 涨停数量
    - 跌停数量
    - 连板分布
    - 一字板数量
    - 炸板数量和炸板率
    """
    try:
        if not trade_date:
            trade_date = get_latest_trading_date()

        supabase = get_supabase()

        # 查询市场情绪数据（包含涨停统计）
        response = supabase.table("market_sentiment").select("*").eq(
            "trade_date", trade_date
        ).execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"未找到 {trade_date} 的涨停统计数据"
            )

        data = response.data[0]

        # 解析连板分布
        continuous_dist = data.get('continuous_limit_distribution')
        if isinstance(continuous_dist, str):
            continuous_dist = json.loads(continuous_dist)

        # 查询一字板数量
        strong_limit_response = supabase.table("limit_stocks_detail").select(
            "*", count="exact"
        ).eq("trade_date", trade_date).eq("limit_type", "limit_up").eq(
            "is_strong_limit", True
        ).execute()

        strong_limit_count = strong_limit_response.count if strong_limit_response.count is not None else 0

        stats = LimitStatsItem(
            trade_date=trade_date,
            limit_up_count=data['limit_up_count'],
            limit_down_count=data['limit_down_count'],
            continuous_distribution=continuous_dist,
            strong_limit_count=strong_limit_count,
            exploded_count=data.get('exploded_count', 0),
            explosion_rate=data['explosion_rate']
        )

        return LimitStatsResponse(
            success=True,
            data=stats
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取涨停统计失败: {str(e)}")


@router.get("/stock/{stock_code}", response_model=LimitStockItem, summary="获取个股涨停详情")
async def get_stock_limit_detail(
    stock_code: str,
    trade_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD")
):
    """
    获取个股涨停详情

    返回指定日期该股票的涨停/跌停详细信息
    """
    try:
        if not trade_date:
            trade_date = get_latest_trading_date()

        supabase = get_supabase()

        # 查询个股数据
        response = supabase.table("limit_stocks_detail").select("*").eq(
            "trade_date", trade_date
        ).eq("stock_code", stock_code).execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"未找到股票 {stock_code} 在 {trade_date} 的涨跌停数据"
            )

        data = response.data[0]

        # 解析 concepts
        if isinstance(data.get('concepts'), str):
            try:
                data['concepts'] = json.loads(data['concepts'])
            except:
                data['concepts'] = []

        return LimitStockItem(**data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取个股详情失败: {str(e)}")
