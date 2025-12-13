"""
明日溢价概率评分服务

用途：
- 龙头股深度分析
- 自选股溢价分析
- 涨停股筛选评分

版本: v2.0
基于5维度评分模型：技术面、资金面、题材地位、位置风险、市场环境
"""

from loguru import logger
from typing import Optional, Dict, List
from datetime import datetime, time as dt_time

from app.utils.supabase_client import get_supabase
from app.schemas.premium import (
    PremiumScoreResult,
    TechnicalScoreDetail,
    CapitalScoreDetail,
    ThemeScoreDetail,
    PositionScoreDetail,
    MarketScoreDetail
)


class PremiumProbabilityService:
    """明日溢价概率评分服务"""

    def __init__(self):
        self.supabase = get_supabase()

        # 可配置的阈值参数（v2.0初始值，后续可根据回测调整）
        self.config = {
            # 技术面阈值
            "first_limit_early": 0,          # 一字板/集合竞价封板阈值（分钟数）
            "first_limit_good": 30,          # 10:00前封板阈值
            "first_limit_medium": 210,       # 13:00前封板阈值
            "first_limit_late": 270,         # 14:00前封板阈值
            "turnover_low": 5,               # 低换手阈值
            "turnover_medium_low": 10,       # 中低换手阈值
            "turnover_medium_high": 15,      # 中高换手阈值
            "turnover_high": 20,             # 高换手阈值
            "turnover_very_high": 25,        # 极高换手阈值

            # 资金面阈值（封单比 = 封单金额/成交额，小数形式）
            "sealed_ratio_strong": 0.10,     # 强封单比阈值（10%）
            "sealed_ratio_medium": 0.03,     # 中等封单比阈值（3%）
            "sealed_ratio_weak": 0.005,      # 弱封单比阈值（0.5%）
            "inflow_pct_heavy_out": -10,     # 明显砸盘阈值
            "inflow_pct_light_in": 5,        # 小幅流入阈值
            "inflow_pct_medium_in": 10,      # 中等流入阈值

            # 题材地位（无需阈值，从数据库查询判断）

            # 位置风险阈值
            "position_very_high": 7,         # 极高位（7板以上）
            "position_high": 5,              # 高位（5-6板）
            "position_medium": 3,            # 中位（3-4板）

            # 市场环境映射
            "emotion_stage_map": {
                "冰点期": -2,
                "回暖期": -1,
                "退潮期": -2,
                "加速期": +1,
                "高潮期": +2
            }
        }

    async def calculate_premium_score(
        self,
        stock_code: str,
        trade_date: str,
        cached_market_data: Optional[Dict] = None
    ) -> Optional[PremiumScoreResult]:
        """
        计算个股明日溢价概率评分

        Args:
            stock_code: 股票代码（6位数字）
            trade_date: 交易日期 YYYY-MM-DD
            cached_market_data: 缓存的市场环境数据（可选，用于批量计算时复用）

        Returns:
            PremiumScoreResult 或 None（股票不存在或非涨停股）
        """
        logger.info(f"计算 {stock_code} {trade_date} 明日溢价概率...")

        # 1. 获取股票基础数据
        stock_data = self._get_stock_data(stock_code, trade_date)
        if not stock_data:
            logger.warning(f"股票 {stock_code} {trade_date} 数据不存在")
            return None

        # 2. 获取市场环境（优先使用缓存）
        if cached_market_data:
            market_data = cached_market_data
            logger.debug(f"使用缓存的市场环境数据")
        else:
            market_data = await self._get_market_environment(trade_date)

        # 3. 获取题材地位信息
        theme_data = self._get_theme_position(stock_code, trade_date, stock_data)

        # 4. 计算各维度评分
        technical_detail = self._calculate_technical_score(stock_data)
        capital_detail = self._calculate_capital_score(stock_data)
        theme_detail = self._calculate_theme_score(theme_data)
        position_detail = self._calculate_position_score(stock_data)
        market_detail = self._calculate_market_score(market_data)

        # 5. 计算总分（原始分数：-9 ~ +9）
        total_score_raw = (
            technical_detail.final_score +
            capital_detail.final_score +
            theme_detail.final_score +
            position_detail.final_score +
            market_detail.final_score  # 已经 × 0.5
        )

        # 6. 转换为10分制
        total_score = self._convert_to_10_scale(total_score_raw, -9, 9)
        technical_score = self._convert_to_10_scale(technical_detail.final_score, -2, 2)
        capital_score = self._convert_to_10_scale(capital_detail.final_score, -2, 2)
        theme_score = self._convert_to_10_scale(theme_detail.final_score, -2, 2)
        position_score = self._convert_to_10_scale(position_detail.final_score, -2, 2)
        market_score = self._convert_to_10_scale(market_detail.final_score, -1, 1)

        # 7. 龙头加分：当天最高板且连板数≥5板，+1分（龙头多条命）
        is_leader_bonus = False
        if stock_data.get("continuous_days", 1) >= 5:
            max_continuous_days = self._get_max_continuous_days(trade_date)
            if max_continuous_days and stock_data.get("continuous_days") == max_continuous_days:
                total_score = min(10.0, total_score + 1.0)  # 加1分，最高不超过10分
                is_leader_bonus = True
                logger.info(f"🔥 {stock_code} 是当天最高板({max_continuous_days}板)且≥5板，触发龙头加分 +1分")

        # 8. 映射溢价等级
        premium_level, level_color = self._map_premium_level(total_score)

        # 9. 构建返回结果
        result = PremiumScoreResult(
            stock_code=stock_code,
            stock_name=stock_data.get("stock_name", ""),
            trade_date=trade_date,
            total_score=round(total_score, 2),
            premium_level=premium_level,
            premium_level_color=level_color,
            technical_score=round(technical_score, 2),
            capital_score=round(capital_score, 2),
            theme_score=round(theme_score, 2),
            position_score=round(position_score, 2),
            market_score=round(market_score, 2),
            technical_detail=technical_detail,
            capital_detail=capital_detail,
            theme_detail=theme_detail,
            position_detail=position_detail,
            market_detail=market_detail
        )

        logger.info(f"✅ {stock_code} 溢价评分: {total_score:.2f}/10 ({premium_level})")
        return result

    def _get_stock_data(self, stock_code: str, trade_date: str) -> Optional[Dict]:
        """获取股票基础数据"""
        try:
            response = self.supabase.table("limit_stocks_detail")\
                .select("*")\
                .eq("stock_code", stock_code)\
                .eq("trade_date", trade_date)\
                .eq("limit_type", "limit_up")\
                .execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"获取股票数据失败: {e}")
            return None

    async def _get_market_environment(self, trade_date: str) -> Dict:
        """获取市场环境（情绪阶段）"""
        try:
            # 从 sentiment_service 获取涨停情绪阶段
            from app.services.sentiment_service import SentimentService
            sentiment_service = SentimentService()
            sentiment_data = await sentiment_service.get_analysis(trade_date)

            if sentiment_data and "data" in sentiment_data:
                data = sentiment_data["data"]
                dashboard = data.get("emotion_dashboard", {})
                return {
                    "emotion_stage": dashboard.get("emotion_stage", "中性"),
                    "emotion_stage_color": dashboard.get("emotion_stage_color", "gray")
                }

        except Exception as e:
            logger.warning(f"获取市场环境失败: {e}")

        # 默认值
        return {
            "emotion_stage": "中性",
            "emotion_stage_color": "gray"
        }

    def _get_theme_position(self, stock_code: str, trade_date: str, stock_data: Dict) -> Dict:
        """获取题材地位信息"""
        result = {
            "main_concept": None,
            "is_in_top10": False,
            "is_main_line": False,
            "ladder_status": "alone"
        }

        try:
            # 1. 获取股票所属概念
            concept_response = self.supabase.table("ths_concept_members")\
                .select("concept_name")\
                .eq("stock_code", stock_code)\
                .execute()

            if not concept_response.data:
                return result

            stock_concepts = [item["concept_name"] for item in concept_response.data]

            # 2. 获取当日热门概念TOP10
            top10_response = self.supabase.table("hot_concepts")\
                .select("concept_name, limit_up_count")\
                .eq("trade_date", trade_date)\
                .eq("is_anomaly", False)\
                .lte("rank", 10)\
                .execute()

            if not top10_response.data:
                return result

            top10_concepts = {item["concept_name"]: item.get("limit_up_count", 0)
                            for item in top10_response.data}

            # 3. 找到股票在TOP10中的概念
            matched_concepts = [c for c in stock_concepts if c in top10_concepts]

            if not matched_concepts:
                return result

            # 取涨停数最多的概念作为主概念
            main_concept = max(matched_concepts, key=lambda c: top10_concepts[c])
            result["main_concept"] = main_concept
            result["is_in_top10"] = True

            # 判断是否主线（TOP10 且 涨停数>=8）
            limit_up_count = top10_concepts[main_concept]
            result["is_main_line"] = (limit_up_count >= 8)

            # 4. 获取该概念的梯队状态
            # 查询该概念的所有涨停股
            concept_stocks_response = self.supabase.table("limit_stocks_detail")\
                .select("continuous_days")\
                .eq("trade_date", trade_date)\
                .eq("limit_type", "limit_up")\
                .execute()

            if concept_stocks_response.data:
                # 找出属于该概念的股票
                concept_member_codes = self.supabase.table("ths_concept_members")\
                    .select("stock_code")\
                    .eq("concept_name", main_concept)\
                    .execute()

                concept_codes = {item["stock_code"] for item in concept_member_codes.data}

                # 统计该概念的连板分布
                continuous_days_list = [
                    stock["continuous_days"]
                    for stock in concept_stocks_response.data
                    if stock["continuous_days"] and stock["continuous_days"] >= 1
                ]

                unique_levels = len(set(continuous_days_list))

                # 判断梯队状态
                if unique_levels >= 3:
                    result["ladder_status"] = "complete"
                elif unique_levels >= 2:
                    result["ladder_status"] = "normal"
                else:
                    result["ladder_status"] = "alone"

        except Exception as e:
            logger.warning(f"获取题材地位信息失败: {e}")

        return result

    def _calculate_technical_score(self, stock_data: Dict) -> TechnicalScoreDetail:
        """计算技术面评分"""
        # 获取字段
        first_limit_time_str = stock_data.get("first_limit_time")
        opening_times = stock_data.get("opening_times") or 0
        turnover_rate = stock_data.get("turnover_rate") or 0
        is_strong_limit = stock_data.get("is_strong_limit", False)

        # 1. 计算封板时间得分
        time_score = 0.0
        if first_limit_time_str:
            # 转换时间为分钟数（从09:30开始）
            try:
                limit_time = datetime.strptime(first_limit_time_str, "%H:%M:%S").time()
                market_open = dt_time(9, 30, 0)

                # 计算分钟数差
                limit_minutes = (limit_time.hour * 60 + limit_time.minute) - \
                               (market_open.hour * 60 + market_open.minute)

                if limit_minutes <= self.config["first_limit_early"]:  # 集合竞价/一字板
                    time_score = 2.0
                elif limit_minutes <= self.config["first_limit_good"]:  # 10:00前
                    time_score = 1.5
                elif limit_minutes <= self.config["first_limit_medium"]:  # 13:00前
                    time_score = 1.0
                elif limit_minutes <= self.config["first_limit_late"]:  # 14:00前
                    time_score = 0.0
                else:  # 尾盘封板
                    time_score = -1.0

            except Exception as e:
                logger.debug(f"解析封板时间失败: {e}")
                time_score = 0.0

        # 开板次数惩罚
        if opening_times == 0:
            pass  # 不调整
        elif opening_times == 1:
            time_score -= 0.5
        else:  # >=2次
            time_score -= 1.0

        # 2. 计算换手率得分
        turnover_score = 0.0
        if turnover_rate < self.config["turnover_low"]:  # <5%
            turnover_score = -1.0
        elif turnover_rate < self.config["turnover_medium_low"]:  # 5-10%
            turnover_score = 0.0
        elif turnover_rate < self.config["turnover_medium_high"]:  # 10-15%
            turnover_score = 1.0
        elif turnover_rate < self.config["turnover_high"]:  # 15-20%
            turnover_score = 2.0
        elif turnover_rate < self.config["turnover_very_high"]:  # 20-25%
            turnover_score = 1.0
        else:  # >=25%
            turnover_score = 1.0

        # 3. 综合得分
        final_score = (time_score + turnover_score) / 2
        final_score = max(-2, min(2, final_score))  # 截断到 [-2, +2]

        # 4. 一字板特判
        is_one_word = is_strong_limit and opening_times == 0
        if is_one_word and final_score < 1:
            final_score = 1.0

        return TechnicalScoreDetail(
            first_limit_time=first_limit_time_str,
            opening_times=opening_times,
            turnover_rate=turnover_rate,
            is_one_word=is_one_word,
            time_score=round(time_score, 2),
            turnover_score=round(turnover_score, 2),
            final_score=round(final_score, 2)
        )

    def _calculate_capital_score(self, stock_data: Dict) -> CapitalScoreDetail:
        """计算资金面评分"""
        # 获取字段
        sealed_amount = stock_data.get("sealed_amount")  # 单位：元
        amount = stock_data.get("amount")  # 单位：元
        main_net_inflow = stock_data.get("main_net_inflow")  # 单位：元
        main_net_inflow_pct = stock_data.get("main_net_inflow_pct")  # 百分比

        # 转换为万元
        sealed_amount_wan = sealed_amount / 10000 if sealed_amount else None
        amount_wan = amount / 10000 if amount else None
        main_net_inflow_wan = main_net_inflow / 10000 if main_net_inflow else None

        # 1. 计算封单比（封单/成交）
        sealed_ratio = None
        sealed_score = 0.0

        if sealed_amount and amount and amount > 0:
            sealed_ratio = sealed_amount / amount

            if sealed_ratio >= self.config["sealed_ratio_strong"]:  # >=10
                sealed_score = 2.0
            elif sealed_ratio >= self.config["sealed_ratio_medium"]:  # 3-10
                sealed_score = 1.0
            elif sealed_ratio >= self.config["sealed_ratio_weak"]:  # 0.5-3
                sealed_score = 0.0
            else:  # <0.5
                sealed_score = -2.0

        # 2. 计算主力净流入得分
        inflow_score = 0.0

        if main_net_inflow_pct is not None:
            if main_net_inflow_pct <= self.config["inflow_pct_heavy_out"]:  # <=-10%
                inflow_score = -2.0
            elif main_net_inflow_pct < 0:  # -10% ~ 0
                inflow_score = -1.0
            elif main_net_inflow_pct <= self.config["inflow_pct_light_in"]:  # 0-5%
                inflow_score = 0.0
            elif main_net_inflow_pct <= self.config["inflow_pct_medium_in"]:  # 5-10%
                inflow_score = 1.0
            else:  # >10%
                inflow_score = 2.0

        # 3. 综合得分
        final_score = (sealed_score + inflow_score) / 2
        final_score = max(-2, min(2, final_score))

        return CapitalScoreDetail(
            sealed_amount=sealed_amount_wan,
            amount=amount_wan,
            sealed_ratio=round(sealed_ratio, 2) if sealed_ratio else None,
            main_net_inflow=main_net_inflow_wan,
            main_net_inflow_pct=main_net_inflow_pct,
            sealed_score=round(sealed_score, 2),
            inflow_score=round(inflow_score, 2),
            final_score=round(final_score, 2)
        )

    def _calculate_theme_score(self, theme_data: Dict) -> ThemeScoreDetail:
        """计算题材地位评分"""
        is_in_top10 = theme_data.get("is_in_top10", False)
        is_main_line = theme_data.get("is_main_line", False)
        ladder_status = theme_data.get("ladder_status", "alone")
        main_concept = theme_data.get("main_concept")

        # 1. 题材热度得分
        theme_hot_score = 0.0
        if is_in_top10:
            if is_main_line:
                theme_hot_score = 2.0
            else:
                theme_hot_score = 1.0
        else:
            theme_hot_score = 0.0  # 不在前十，给0（不是-1）

        # 2. 梯队状态得分
        ladder_score = 0.0
        if ladder_status == "complete":
            ladder_score = 2.0
        elif ladder_status == "normal":
            ladder_score = 0.0
        else:  # alone
            ladder_score = -2.0

        # 3. 综合得分
        final_score = (theme_hot_score + ladder_score) / 2
        final_score = max(-2, min(2, final_score))

        return ThemeScoreDetail(
            main_concept=main_concept,
            is_in_top10=is_in_top10,
            is_main_line=is_main_line,
            ladder_status=ladder_status,
            theme_hot_score=round(theme_hot_score, 2),
            ladder_score=round(ladder_score, 2),
            final_score=round(final_score, 2)
        )

    def _calculate_position_score(self, stock_data: Dict) -> PositionScoreDetail:
        """计算位置风险评分"""
        continuous_days = stock_data.get("continuous_days") or 1

        # 连板天数越高，风险越大，得分越低
        if continuous_days >= self.config["position_very_high"]:  # >=7板
            final_score = -2.0
            risk_level = "极高"
        elif continuous_days >= self.config["position_high"]:  # 5-6板
            final_score = -1.0
            risk_level = "高"
        elif continuous_days >= self.config["position_medium"]:  # 3-4板
            final_score = 0.0
            risk_level = "中"
        elif continuous_days == 2:  # 2板
            final_score = 1.0
            risk_level = "低"
        else:  # 首板
            final_score = 2.0
            risk_level = "极低"

        return PositionScoreDetail(
            continuous_days=continuous_days,
            position_risk_level=risk_level,
            final_score=round(final_score, 2)
        )

    def _calculate_market_score(self, market_data: Dict) -> MarketScoreDetail:
        """计算市场环境评分"""
        emotion_stage = market_data.get("emotion_stage", "中性")
        emotion_stage_color = market_data.get("emotion_stage_color", "gray")

        # 从配置中获取情绪阶段对应的得分
        stage_map = self.config["emotion_stage_map"]
        raw_score = stage_map.get(emotion_stage, 0)

        # 乘以0.5权重
        final_score = raw_score * 0.5

        return MarketScoreDetail(
            emotion_stage=emotion_stage,
            emotion_stage_color=emotion_stage_color,
            final_score=round(final_score, 2)
        )

    def _convert_to_10_scale(self, score: float, min_val: float = -9, max_val: float = 9) -> float:
        """
        将分数转换为10分制

        Args:
            score: 原始分数
            min_val: 原始分数最小值（默认-9）
            max_val: 原始分数最大值（默认+9）

        Returns:
            0-10分制的分数
        """
        # 转换公式：(score - min_val) / (max_val - min_val) * 10
        return (score - min_val) / (max_val - min_val) * 10

    def _get_max_continuous_days(self, trade_date: str) -> Optional[int]:
        """
        获取当天所有涨停股的最高连板数

        Args:
            trade_date: 交易日期 YYYY-MM-DD

        Returns:
            最高连板数，查询失败返回None
        """
        try:
            response = self.supabase.table("limit_stocks_detail")\
                .select("continuous_days")\
                .eq("trade_date", trade_date)\
                .eq("limit_type", "limit_up")\
                .order("continuous_days", desc=True)\
                .limit(1)\
                .execute()

            if response.data and len(response.data) > 0:
                max_days = response.data[0].get("continuous_days")
                logger.debug(f"当天({trade_date})最高连板数: {max_days}板")
                return max_days
            return None
        except Exception as e:
            logger.error(f"查询最高连板数失败: {e}")
            return None

    def _map_premium_level(self, total_score: float) -> tuple[str, str]:
        """
        映射溢价等级（10分制）

        Returns:
            (等级名称, 颜色)
        """
        if total_score >= 8:
            return "极高", "red"
        elif total_score >= 7:
            return "高", "orange"
        elif total_score >= 6:
            return "偏高", "yellow"
        elif total_score >= 5:
            return "中性", "gray"
        elif total_score >= 4:
            return "偏低", "blue"
        else:
            return "低", "purple"
