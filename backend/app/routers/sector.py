"""
板块分析API路由
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from loguru import logger

from app.schemas.sector import (
    SectorAnalysisResponse,
    SectorAnalysisData,
    TrendSectorItem,
    EmotionSectorItem,
    MainSectorItem,
    AnomalySectorItem,
)
from app.utils.supabase_client import get_supabase
from app.utils.trading_date import get_latest_trading_date

router = APIRouter(prefix="/api/sector", tags=["板块分析"])

# 情绪板块涨停数阈值（>=8即满足条件）
EMOTION_LIMIT_UP_THRESHOLD = 8


def get_consecutive_main_days(supabase, concept_name: str, current_date: str) -> tuple:
    """
    计算板块连续主线天数和上榜首日

    主线条件：在TOP10热门板块 且 涨停数>10
    利用数据库只有交易日有数据的特点判断连续性

    Args:
        supabase: Supabase客户端
        concept_name: 板块名称
        current_date: 当前日期

    Returns:
        (连续主线天数, 上榜首日日期)
    """
    try:
        # 查询该板块历史数据（最近30天，按日期倒序）
        response = supabase.table("hot_concepts").select(
            "trade_date, rank, limit_up_count, is_anomaly"
        ).eq("concept_name", concept_name).lt(
            "trade_date", current_date
        ).order("trade_date", desc=True).limit(30).execute()

        if not response.data:
            return 1, current_date  # 无历史记录，今天第1天，首日就是今天

        consecutive_days = 1  # 今天算1天
        first_main_date = current_date  # 上榜首日，初始为今天
        prev_date = current_date

        for record in response.data:
            record_date = record['trade_date']

            # 检查是否是连续的交易日（利用数据库只有交易日有数据的特点）
            # 查询这两个日期之间是否有其他交易日的数据
            between_response = supabase.table("hot_concepts").select(
                "trade_date"
            ).gt("trade_date", record_date).lt(
                "trade_date", prev_date
            ).limit(1).execute()

            if between_response.data:
                # 中间有其他交易日，不连续，停止计数
                break

            # 检查该日期是否满足主线条件：在TOP10 且 涨停数>=8
            is_in_top10 = (record.get('rank') or 999) <= 10 and not record.get('is_anomaly', False)
            limit_up_count = record.get('limit_up_count') or 0

            if is_in_top10 and limit_up_count >= EMOTION_LIMIT_UP_THRESHOLD:
                consecutive_days += 1
                first_main_date = record_date  # 更新上榜首日
                prev_date = record_date
            else:
                # 不满足主线条件，停止计数
                break

        return consecutive_days, first_main_date

    except Exception as e:
        logger.debug(f"计算连续主线天数失败: {concept_name}, {e}")
        return 1, current_date


@router.get("/analysis", response_model=SectorAnalysisResponse, summary="获取板块分析数据")
async def get_sector_analysis(
    trade_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD，默认最新交易日"),
):
    """
    获取板块分析四大模块数据

    - **趋势板块**: 首页热门板块TOP10（按5日涨幅排序）
    - **情绪板块**: 首页热门板块中涨停数>=8的板块
    - **主线板块**: 趋势板块与情绪板块的交集
    - **异动板块**: 非首页前十中涨停数/涨幅最高的板块
    """
    try:
        # 获取交易日期
        if not trade_date:
            trade_date = get_latest_trading_date()

        logger.info(f"获取 {trade_date} 的板块分析数据")

        supabase = get_supabase()

        # 1. 获取首页热门板块（rank 1-10，非异动）
        hot_response = supabase.table("hot_concepts").select("*").eq(
            "trade_date", trade_date
        ).eq("is_anomaly", False).lte("rank", 10).order("rank").execute()

        hot_concepts = hot_response.data or []
        logger.info(f"获取到 {len(hot_concepts)} 个热门板块")

        # 2. 获取异动板块
        anomaly_response = supabase.table("hot_concepts").select("*").eq(
            "trade_date", trade_date
        ).eq("is_anomaly", True).execute()

        anomaly_concepts = anomaly_response.data or []
        logger.info(f"获取到 {len(anomaly_concepts)} 个异动板块")

        # 3. 计算趋势板块（热门板块TOP10，按5日涨幅排序展示）
        trend_sorted = sorted(
            hot_concepts,
            key=lambda x: x.get('change_pct') or 0,
            reverse=True
        )

        trend_sectors = [
            TrendSectorItem(
                concept_name=c['concept_name'],
                day_change_pct=c.get('day_change_pct'),
                change_pct=c.get('change_pct'),
                leader_stock_name=c.get('leader_stock_name'),
                leader_stock_code=c.get('leader_stock_code'),
                leader_continuous_days=c.get('leader_continuous_days'),
            )
            for c in trend_sorted
        ]

        # 4. 计算情绪板块（涨停数>=8）
        emotion_filtered = [
            c for c in hot_concepts
            if (c.get('limit_up_count') or 0) >= EMOTION_LIMIT_UP_THRESHOLD
        ]
        emotion_sorted = sorted(
            emotion_filtered,
            key=lambda x: x.get('limit_up_count') or 0,
            reverse=True
        )

        emotion_sectors = [
            EmotionSectorItem(
                concept_name=c['concept_name'],
                day_change_pct=c.get('day_change_pct'),
                limit_up_count=c.get('limit_up_count'),
                leader_stock_name=c.get('leader_stock_name'),
                leader_stock_code=c.get('leader_stock_code'),
                leader_continuous_days=c.get('leader_continuous_days'),
            )
            for c in emotion_sorted
        ]

        # 5. 计算主线板块（趋势∩情绪）
        trend_names = {s.concept_name for s in trend_sectors}
        emotion_names = {s.concept_name for s in emotion_sectors}
        main_names = trend_names & emotion_names

        # 保持趋势板块的顺序，并计算连续主线天数和上榜首日
        main_sectors = []
        for c in trend_sorted:
            if c['concept_name'] in main_names:
                consecutive_days, first_main_date = get_consecutive_main_days(
                    supabase, c['concept_name'], trade_date
                )
                main_sectors.append(MainSectorItem(
                    concept_name=c['concept_name'],
                    consecutive_main_days=consecutive_days,
                    first_main_date=first_main_date,
                    day_change_pct=c.get('day_change_pct'),
                    change_pct=c.get('change_pct'),
                    limit_up_count=c.get('limit_up_count'),
                    leader_stock_name=c.get('leader_stock_name'),
                    leader_stock_code=c.get('leader_stock_code'),
                    leader_continuous_days=c.get('leader_continuous_days'),
                ))

        # 按连续主线天数降序排序
        main_sectors.sort(key=lambda x: x.consecutive_main_days, reverse=True)

        # 6. 处理异动板块（按类型和顺序排序）
        # 涨停异动在上，涨幅异动在下
        limit_up_anomalies = sorted(
            [c for c in anomaly_concepts if c.get('anomaly_type') == 'limit_up'],
            key=lambda x: x.get('limit_up_count') or 0,
            reverse=True
        )
        change_pct_anomalies = sorted(
            [c for c in anomaly_concepts if c.get('anomaly_type') == 'change_pct'],
            key=lambda x: x.get('day_change_pct') or 0,
            reverse=True
        )

        anomaly_sectors = [
            AnomalySectorItem(
                concept_name=c['concept_name'],
                day_change_pct=c.get('day_change_pct'),
                limit_up_count=c.get('limit_up_count'),
                leader_stock_name=c.get('leader_stock_name'),
                leader_stock_code=c.get('leader_stock_code'),
                leader_continuous_days=c.get('leader_continuous_days'),
                anomaly_type=c.get('anomaly_type', 'unknown'),
            )
            for c in limit_up_anomalies + change_pct_anomalies
        ]

        logger.info(
            f"板块分析完成: 趋势{len(trend_sectors)}个, "
            f"情绪{len(emotion_sectors)}个, "
            f"主线{len(main_sectors)}个, "
            f"异动{len(anomaly_sectors)}个"
        )

        return SectorAnalysisResponse(
            success=True,
            trade_date=trade_date,
            data=SectorAnalysisData(
                trend_sectors=trend_sectors,
                emotion_sectors=emotion_sectors,
                main_sectors=main_sectors,
                anomaly_sectors=anomaly_sectors,
            )
        )

    except Exception as e:
        logger.error(f"获取板块分析数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取板块分析数据失败: {str(e)}")
