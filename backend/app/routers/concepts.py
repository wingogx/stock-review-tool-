"""
概念板块相关 API 路由
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import json

from app.utils.supabase_client import get_supabase
from app.utils.trading_date import get_latest_trading_date
from app.schemas.concepts import (
    HotConceptsResponse,
    HotConceptItem,
    ConceptStocksResponse,
    ConceptStockItem,
    ConceptDetailResponse,
)

router = APIRouter()


@router.get("/hot", response_model=HotConceptsResponse, summary="获取热门概念板块")
async def get_hot_concepts(
    trade_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD"),
    top_n: int = Query(10, ge=1, le=100, description="返回前N个概念"),
    order_by: str = Query("change_pct", description="排序字段: change_pct/concept_strength/rank"),
):
    """
    获取热门概念板块

    支持：
    - top_n: 返回涨幅前N的概念
    - order_by: 按平均涨幅、涨停数或概念强度排序
    """
    try:
        if not trade_date:
            trade_date = get_latest_trading_date()

        supabase = get_supabase()

        # 构建查询
        query = supabase.table("hot_concepts").select("*", count="exact")
        query = query.eq("trade_date", trade_date)

        # 排序（Supabase 格式）
        order_mapping = {
            "change_pct": ("change_pct", {"desc": True, "nullsfirst": True}),
            "concept_strength": ("concept_strength", {"desc": True, "nullsfirst": True}),
            "rank": ("rank", {"desc": False, "nullsfirst": True}),
        }
        order_field, order_opts = order_mapping.get(order_by, ("change_pct", {"desc": True, "nullsfirst": True}))
        query = query.order(order_field, **order_opts)

        # 限制数量
        query = query.limit(top_n)

        # 执行查询
        response = query.execute()

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail=f"未找到 {trade_date} 的热门概念数据"
            )

        concepts = [HotConceptItem(**item) for item in response.data]

        return HotConceptsResponse(
            success=True,
            data=concepts,
            total=len(concepts)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取热门概念失败: {str(e)}")


@router.get("/stocks/{concept_name}", response_model=ConceptStocksResponse, summary="获取概念成分股")
async def get_concept_stocks(
    concept_name: str,
    trade_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD"),
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
):
    """
    获取概念成分股列表

    返回指定概念的成分股，按涨幅排序
    """
    try:
        if not trade_date:
            trade_date = get_latest_trading_date()

        supabase = get_supabase()

        # 查询成分股
        response = supabase.table("concept_stocks").select("*").eq(
            "trade_date", trade_date
        ).eq("concept_name", concept_name).order(
            "change_pct", desc=True, nullsfirst=True
        ).limit(limit).execute()

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail=f"未找到概念 '{concept_name}' 在 {trade_date} 的成分股数据"
            )

        stocks = [ConceptStockItem(**item) for item in response.data]

        return ConceptStocksResponse(
            success=True,
            concept_name=concept_name,
            data=stocks,
            total=len(stocks)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取概念成分股失败: {str(e)}")


@router.get("/detail/{concept_name}", response_model=ConceptDetailResponse, summary="获取概念详情")
async def get_concept_detail(
    concept_name: str,
    trade_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD"),
):
    """
    获取概念详情

    包含：
    - 概念基本信息
    - 龙头股信息
    - 涨幅前10的成分股
    """
    try:
        if not trade_date:
            trade_date = get_latest_trading_date()

        supabase = get_supabase()

        # 查询概念信息
        concept_response = supabase.table("hot_concepts").select("*").eq(
            "trade_date", trade_date
        ).eq("concept_name", concept_name).execute()

        if not concept_response.data or len(concept_response.data) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"未找到概念 '{concept_name}' 在 {trade_date} 的数据"
            )

        concept_info = concept_response.data[0]

        # 查询成分股（涨幅前10）
        stocks_response = supabase.table("concept_stocks").select("*").eq(
            "trade_date", trade_date
        ).eq("concept_name", concept_name).order(
            "change_pct", desc=True, nullsfirst=True
        ).limit(10).execute()

        top_stocks = [ConceptStockItem(**item) for item in stocks_response.data]

        return ConceptDetailResponse(
            success=True,
            concept_name=concept_name,
            trade_date=trade_date,
            change_pct=concept_info['change_pct'],
            concept_strength=concept_info.get('concept_strength'),
            rank=concept_info.get('rank'),
            top_stocks=top_stocks
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取概念详情失败: {str(e)}")


@router.get("/search", response_model=HotConceptsResponse, summary="搜索概念板块")
async def search_concepts(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    trade_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
):
    """
    搜索概念板块

    支持模糊搜索概念名称
    """
    try:
        if not trade_date:
            trade_date = get_latest_trading_date()

        supabase = get_supabase()

        # 模糊搜索
        response = supabase.table("hot_concepts").select("*").eq(
            "trade_date", trade_date
        ).ilike("concept_name", f"%{q}%").order(
            "change_pct", desc=True, nullsfirst=True
        ).limit(limit).execute()

        if not response.data:
            return HotConceptsResponse(
                success=True,
                data=[],
                total=0
            )

        concepts = [HotConceptItem(**item) for item in response.data]

        return HotConceptsResponse(
            success=True,
            data=concepts,
            total=len(concepts)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索概念失败: {str(e)}")
