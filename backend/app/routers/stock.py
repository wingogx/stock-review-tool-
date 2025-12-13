"""
个股分析相关 API 路由
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from loguru import logger

from app.services.premium_probability_service import PremiumProbabilityService
from app.services.backtest_service import BacktestService
from app.schemas.premium import PremiumScoreResponse
from app.utils.trading_date import get_latest_trading_date

router = APIRouter()


@router.get("/premium-score", response_model=PremiumScoreResponse, summary="获取个股明日溢价概率评分")
async def get_premium_score(
    stock_code: str = Query(..., description="股票代码（6位数字）", regex=r"^\d{6}$"),
    trade_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD，默认为最近交易日")
):
    """
    获取个股明日溢价概率评分

    评分维度（v2.0）：
    - 技术面（-2 ~ +2）：封板时间、开板次数、换手率
    - 资金面（-2 ~ +2）：封单比、主力净流入
    - 题材地位（-2 ~ +2）：热门概念、梯队状态
    - 位置风险（-2 ~ +2）：连板天数
    - 市场环境（-1 ~ +1）：情绪阶段 × 0.5

    总分范围：-9 ~ +9

    溢价等级：
    - ≥6: 极高（深红）
    - 4~6: 高（橙色）
    - 2~4: 偏高（黄色）
    - 0~2: 中性（灰色）
    - -2~0: 偏低（蓝色）
    - <-2: 低（绿色）

    参数：
    - stock_code: 股票代码（6位数字）
    - trade_date: 交易日期，不传则使用最近交易日

    返回：
    - 总分和等级
    - 各维度得分及详情
    - 风险提示

    注意：手动评测的数据会自动保存到回测表
    """
    try:
        # 默认使用最近交易日
        if not trade_date:
            trade_date = get_latest_trading_date()

        # 计算溢价评分
        service = PremiumProbabilityService()
        result = await service.calculate_premium_score(stock_code, trade_date)

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"未找到 {stock_code} 在 {trade_date} 的涨停数据"
            )

        # 异步保存到回测表（不阻塞返回，失败也不影响评分结果）
        try:
            backtest_service = BacktestService()
            await backtest_service.save_backtest_record(
                stock_code=stock_code,
                trade_date=trade_date,
                next_trade_date=None  # 不传次日日期，函数内部会自动计算
            )
            logger.info(f"✅ 手动评测结果已保存到回测表: {stock_code} {trade_date}")
        except Exception as e:
            # 保存失败不影响评分结果返回
            logger.warning(f"保存回测记录失败（不影响评分）: {e}")

        return PremiumScoreResponse(
            success=True,
            data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"计算溢价评分失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"计算溢价评分失败: {str(e)}"
        )
