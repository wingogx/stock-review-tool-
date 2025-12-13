"""
回测相关 API 路由
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from loguru import logger

from app.services.backtest_service import BacktestService
from app.utils.supabase_client import get_supabase

router = APIRouter()


@router.post("/save/{trade_date}", summary="保存指定日期的回测数据")
async def save_backtest_data(
    trade_date: str,
    next_trade_date: Optional[str] = Query(None, description="次日交易日期"),
    limit: int = Query(50, description="最多处理股票数量")
):
    """
    批量保存某天所有涨停股票的回测数据

    Args:
        trade_date: 交易日期 YYYY-MM-DD
        next_trade_date: 次日交易日期（可选，不传则自动+1天）
        limit: 最多处理多少只股票

    Returns:
        保存统计信息
    """
    try:
        service = BacktestService()
        result = await service.batch_save_backtest(
            trade_date=trade_date,
            next_trade_date=next_trade_date,
            limit=limit
        )

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        logger.error(f"保存回测数据失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results", summary="查询回测结果")
async def get_backtest_results(
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    min_score: Optional[float] = Query(None, description="最低分数"),
    max_score: Optional[float] = Query(None, description="最高分数"),
    page: int = Query(1, description="页码（从1开始）", ge=1),
    page_size: int = Query(20, description="每页条数", ge=1, le=100)
):
    """
    查询回测结果（支持分页）

    Args:
        start_date: 开始日期 YYYY-MM-DD
        end_date: 结束日期 YYYY-MM-DD
        min_score: 最低分数
        max_score: 最高分数
        page: 页码（从1开始）
        page_size: 每页条数

    Returns:
        回测记录列表（按创建时间倒序）
    """
    try:
        service = BacktestService()

        # 查询结果和总数
        results, total = service.query_backtest_results(
            start_date=start_date,
            end_date=end_date,
            min_score=min_score,
            max_score=max_score,
            page=page,
            page_size=page_size
        )

        return {
            "success": True,
            "data": results,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size  # 向上取整
        }

    except Exception as e:
        logger.error(f"查询回测结果失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", summary="获取回测统计数据")
async def get_backtest_statistics(
    trade_date: Optional[str] = Query(None, description="指定日期，不传则统计所有")
):
    """
    获取回测统计数据

    按评分等级分组统计：
    - 平均次日涨幅
    - 涨停率
    - 盈利率
    - 预测准确率

    Args:
        trade_date: 指定日期 YYYY-MM-DD（可选）

    Returns:
        统计信息
    """
    try:
        service = BacktestService()
        stats = service.get_backtest_statistics(trade_date=trade_date)

        return {
            "success": True,
            "data": stats
        }

    except Exception as e:
        logger.error(f"获取统计数据失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/records", summary="删除回测记录")
async def delete_backtest_records(
    record_ids: list[int] = Query(..., description="要删除的记录ID列表")
):
    """
    批量删除回测记录

    Args:
        record_ids: 记录ID列表

    Returns:
        删除结果
    """
    try:
        service = BacktestService()
        deleted_count = service.delete_backtest_records(record_ids)

        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"成功删除 {deleted_count} 条记录"
        }

    except Exception as e:
        logger.error(f"删除回测记录失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock-detail/{stock_code}", summary="获取股票涨停时的详细数据")
async def get_stock_limit_detail(
    stock_code: str,
    trade_date: str = Query(..., description="交易日期 YYYY-MM-DD")
):
    """
    获取某只股票在某个交易日涨停时的详细数据

    用于在回测记录中点击股票名称时，查看该股票涨停时的具体情况

    Args:
        stock_code: 股票代码（6位数字）
        trade_date: 交易日期 YYYY-MM-DD

    Returns:
        股票涨停详细数据（包含首页连板展示的所有字段）
    """
    try:
        supabase = get_supabase()

        # 从limit_stocks_detail表查询该股票涨停时的详细数据
        response = supabase.table("limit_stocks_detail")\
            .select("*")\
            .eq("stock_code", stock_code)\
            .eq("trade_date", trade_date)\
            .eq("limit_type", "limit_up")\
            .execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"未找到股票 {stock_code} 在 {trade_date} 的涨停数据"
            )

        stock_data = response.data[0]

        return {
            "success": True,
            "data": stock_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取股票详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
