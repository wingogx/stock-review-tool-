"""
情绪分析服务
提供情绪周期仪表盘、昨日涨停表现、概念梯队分析、龙头股深度分析等功能
"""

from typing import Optional, List, Dict, Any
from loguru import logger

from app.utils.supabase_client import get_supabase
from app.utils.trading_date import get_latest_trading_date


def _get_previous_trading_date(trade_date: str) -> Optional[str]:
    """获取前一个交易日"""
    try:
        # 尝试多种导入路径
        try:
            from trading_calendar_2025 import get_calendar
        except ImportError:
            from backend.trading_calendar_2025 import get_calendar

        calendar = get_calendar()
        return calendar.get_previous_trading_day(trade_date)
    except Exception as e:
        logger.warning(f"获取前一交易日失败: {e}")
        return None


class SentimentService:
    """情绪分析服务"""

    def __init__(self):
        self.supabase = get_supabase()

    async def get_analysis(self, trade_date: Optional[str] = None) -> dict:
        """
        获取情绪分析完整数据

        Args:
            trade_date: 交易日期，默认最新交易日

        Returns:
            情绪分析数据
        """
        if not trade_date:
            trade_date = get_latest_trading_date()

        yesterday = _get_previous_trading_date(trade_date)
        logger.info(f"开始情绪分析: trade_date={trade_date}, yesterday={yesterday}")

        # 获取各模块数据
        emotion_dashboard = await self._get_emotion_dashboard(trade_date, yesterday)
        yesterday_performance = await self._get_yesterday_performance(trade_date, yesterday)
        concept_ladder = await self._get_concept_ladder(trade_date)
        leader_analysis = await self._get_leader_analysis(trade_date)

        return {
            "success": True,
            "trade_date": trade_date,
            "data": {
                "emotion_dashboard": emotion_dashboard,
                "yesterday_performance": yesterday_performance,
                "concept_ladder": concept_ladder,
                "leader_analysis": leader_analysis
            }
        }

    async def _get_emotion_dashboard(self, trade_date: str, yesterday: Optional[str]) -> dict:
        """
        获取情绪周期仪表盘数据

        包含：空间板高度、涨停数、炸板率、晋级率、情绪阶段
        """
        # 1. 获取今日市场情绪
        today_sentiment = self.supabase.table("market_sentiment")\
            .select("*").eq("trade_date", trade_date).execute()

        if not today_sentiment.data:
            logger.warning(f"未找到 {trade_date} 的市场情绪数据")
            return self._empty_emotion_dashboard()

        today_data = today_sentiment.data[0]

        # 2. 获取昨日市场情绪
        yesterday_data = None
        if yesterday:
            yesterday_sentiment = self.supabase.table("market_sentiment")\
                .select("*").eq("trade_date", yesterday).execute()
            if yesterday_sentiment.data:
                yesterday_data = yesterday_sentiment.data[0]

        # 3. 计算空间板高度
        today_distribution = today_data.get("continuous_limit_distribution") or {}
        if isinstance(today_distribution, str):
            import json
            today_distribution = json.loads(today_distribution)

        space_height = max([int(k) for k in today_distribution.keys()]) if today_distribution else 0

        # 3.1 计算昨日空间板高度（用于计算变化）
        yesterday_space_height = 0
        if yesterday_data:
            yesterday_distribution_raw = yesterday_data.get("continuous_limit_distribution") or {}
            if isinstance(yesterday_distribution_raw, str):
                import json
                yesterday_distribution_raw = json.loads(yesterday_distribution_raw)
            if yesterday_distribution_raw:
                yesterday_space_height = max([int(k) for k in yesterday_distribution_raw.keys()])

        # 4. 计算晋级率
        yesterday_distribution = {}
        if yesterday_data:
            yesterday_distribution = yesterday_data.get("continuous_limit_distribution") or {}
            if isinstance(yesterday_distribution, str):
                import json
                yesterday_distribution = json.loads(yesterday_distribution)

        promotion_details = self._calculate_promotion_rate(today_distribution, yesterday_distribution)

        # 5. 计算整体晋级率
        overall_promotion_rate = None
        if promotion_details:
            total_yesterday = sum(p["yesterday_count"] for p in promotion_details)
            total_today = sum(p["today_count"] for p in promotion_details)
            if total_yesterday > 0:
                overall_promotion_rate = round(total_today / total_yesterday * 100, 1)

        # 5.5 获取昨日涨停溢价统计（新增）
        premium_stats = self._get_yesterday_limit_premium_stats(trade_date)

        # 5.6 获取最近阶段（用于退潮判断）
        recent_stages = self._get_recent_stages(trade_date, days=3)

        # 5.7 获取昨日情绪阶段（用于惯性区间判断）
        previous_stage = self._get_previous_emotion_stage(yesterday, yesterday_data)

        # 6. 判断情绪阶段（v2.3 多因子梯度打分 + 惯性区间）
        explosion_rate = today_data.get("explosion_rate") or 0
        limit_up_count = today_data.get("limit_up_count") or 0
        limit_down_count = today_data.get("limit_down_count") or 0
        emotion_stage, stage_color, stage_details = self._determine_emotion_stage(
            space_height=space_height,
            explosion_rate=explosion_rate,
            promotion_details=promotion_details,
            limit_up_count=limit_up_count,
            limit_down_count=limit_down_count,
            premium_stats=premium_stats,
            recent_stages=recent_stages,
            previous_stage=previous_stage
        )

        # 7. 计算涨停数变化
        limit_up_count = today_data.get("limit_up_count") or 0
        limit_up_change = None
        if yesterday_data:
            yesterday_limit_up = yesterday_data.get("limit_up_count") or 0
            limit_up_change = limit_up_count - yesterday_limit_up

        # 7.1 计算空间板高度变化
        space_height_change = None
        if yesterday_data and yesterday_space_height > 0:
            space_height_change = space_height - yesterday_space_height

        # 7.2 计算炸板率变化
        explosion_rate_change = None
        if yesterday_data:
            yesterday_explosion_rate = yesterday_data.get("explosion_rate") or 0
            explosion_rate_change = round(explosion_rate - yesterday_explosion_rate, 1)

        return {
            "space_height": space_height,
            "space_height_change": space_height_change,
            "limit_up_count": limit_up_count,
            "limit_up_change": limit_up_change,
            "explosion_rate": explosion_rate,
            "explosion_rate_change": explosion_rate_change,
            "overall_promotion_rate": overall_promotion_rate,
            "promotion_details": promotion_details,
            "emotion_stage": emotion_stage,
            "emotion_stage_color": stage_color,
            # 新增：昨日涨停溢价统计
            "premium_stats": {
                "avg_premium": premium_stats.get("avg_premium"),           # 整体溢价率
                "avg_open_premium": premium_stats.get("avg_open_premium"), # 开盘溢价率
                "first_board_premium": premium_stats.get("first_board_premium"),  # 首板溢价
                "high_board_premium": premium_stats.get("high_board_premium"),    # 高位板溢价
                "big_loss_rate": premium_stats.get("big_loss_rate"),              # 大面率
                "high_board_big_loss_rate": premium_stats.get("high_board_big_loss_rate")  # 高位大面率
            } if premium_stats else None,
            # v2.3 新增：情绪阶段判断详情（含惯性区间）
            "stage_details": {
                "factor_scores": stage_details.get("factor_scores"),      # 各因子得分
                "total_score": stage_details.get("total_score"),          # 总分
                "had_recent_peak": stage_details.get("had_recent_peak"),  # 最近是否有高峰
                "is_deteriorating": stage_details.get("is_deteriorating"), # 是否恶化中
                "stage_raw": stage_details.get("stage_raw"),              # 原始阶段（不带惯性）
                "used_inertia": stage_details.get("used_inertia"),        # 是否使用了惯性
                "previous_stage": stage_details.get("previous_stage")     # 昨日阶段
            } if stage_details else None
        }

    async def _get_yesterday_performance(self, trade_date: str, yesterday: Optional[str]) -> dict:
        """
        获取昨日涨停今日表现

        包含：昨日涨停数、今日平均涨幅、大面数量、大面率、大面个股列表
        优先从 yesterday_limit_performance 表获取完整数据
        """
        if not yesterday:
            return self._empty_yesterday_performance()

        # 优先从 yesterday_limit_performance 表获取数据
        perf_result = self.supabase.table("yesterday_limit_performance")\
            .select("*")\
            .eq("trade_date", trade_date)\
            .execute()

        if perf_result.data:
            # 使用完整数据
            records = perf_result.data
            yesterday_limit_up_count = len(records)

            # 有涨跌幅数据的记录
            with_change = [r for r in records if r.get("today_change_pct") is not None]
            today_avg_change = round(sum(r["today_change_pct"] for r in with_change) / len(with_change), 2) if with_change else None

            # 统计上涨/下跌
            up_count = sum(1 for r in records if r.get("today_change_pct") is not None and r["today_change_pct"] > 0)
            down_count = sum(1 for r in records if r.get("today_change_pct") is not None and r["today_change_pct"] < 0)

            # 大面股列表（跌幅>5%）
            big_loss_records = [r for r in records if r.get("is_big_loss")]
            big_loss_count = len(big_loss_records)
            big_loss_rate = round(big_loss_count / yesterday_limit_up_count * 100, 1) if yesterday_limit_up_count > 0 else 0

            # 排序：按跌幅从大到小
            big_loss_records.sort(key=lambda x: x.get("today_change_pct") or 0)

            # 从 limit_stocks_detail 获取昨日炸板次数
            big_loss_codes = [r["stock_code"] for r in big_loss_records[:10]]
            opening_times_map = {}
            if big_loss_codes and yesterday:
                detail_result = self.supabase.table("limit_stocks_detail")\
                    .select("stock_code, opening_times")\
                    .eq("trade_date", yesterday)\
                    .in_("stock_code", big_loss_codes)\
                    .execute()
                if detail_result.data:
                    for item in detail_result.data:
                        opening_times_map[item["stock_code"]] = item.get("opening_times")

            big_loss_stocks = [
                {
                    "stock_code": r["stock_code"],
                    "stock_name": r.get("stock_name"),
                    "today_change_pct": r.get("today_change_pct"),
                    "yesterday_continuous_days": r.get("yesterday_continuous_days") or 1,
                    "yesterday_opening_times": opening_times_map.get(r["stock_code"]),
                    "concepts": []
                }
                for r in big_loss_records[:10]
            ]

            return {
                "yesterday_limit_up_count": yesterday_limit_up_count,
                "today_avg_change": today_avg_change,
                "up_count": up_count,
                "down_count": down_count,
                "big_loss_count": big_loss_count,
                "big_loss_rate": big_loss_rate,
                "big_loss_stocks": big_loss_stocks
            }

        # 回退方案：从 limit_stocks_detail 表获取（数据不完整）
        yesterday_stocks = self.supabase.table("limit_stocks_detail")\
            .select("stock_code, stock_name, continuous_days, concepts")\
            .eq("trade_date", yesterday)\
            .eq("limit_type", "limit_up")\
            .execute()

        if not yesterday_stocks.data:
            return self._empty_yesterday_performance()

        yesterday_limit_up_count = len(yesterday_stocks.data)

        today_stocks = self.supabase.table("limit_stocks_detail")\
            .select("stock_code, stock_name, change_pct, limit_type")\
            .eq("trade_date", trade_date)\
            .execute()

        today_map = {s["stock_code"]: s for s in today_stocks.data}

        up_count = 0
        down_count = 0
        big_loss_stocks = []

        for stock in yesterday_stocks.data:
            stock_code = stock["stock_code"]
            today_stock = today_map.get(stock_code)

            if today_stock:
                change_pct = today_stock.get("change_pct") or 0
                limit_type = today_stock.get("limit_type")

                if limit_type == "limit_up":
                    up_count += 1
                elif limit_type == "limit_down":
                    down_count += 1
                    big_loss_stocks.append({
                        "stock_code": stock_code,
                        "stock_name": stock["stock_name"],
                        "today_change_pct": change_pct,
                        "yesterday_continuous_days": stock.get("continuous_days") or 1,
                        "concepts": self._parse_concepts(stock.get("concepts"))[:1]
                    })
            else:
                down_count += 1

        big_loss_count = len(big_loss_stocks)
        big_loss_rate = round(big_loss_count / yesterday_limit_up_count * 100, 1) if yesterday_limit_up_count > 0 else 0
        big_loss_stocks.sort(key=lambda x: x["today_change_pct"])

        return {
            "yesterday_limit_up_count": yesterday_limit_up_count,
            "today_avg_change": None,
            "up_count": up_count,
            "down_count": down_count,
            "big_loss_count": big_loss_count,
            "big_loss_rate": big_loss_rate,
            "big_loss_stocks": big_loss_stocks[:10]
        }

    async def _get_concept_ladder(self, trade_date: str) -> dict:
        """
        获取概念梯队分析（使用 ths_concept_members 对照表）

        只显示4板及以上股票所属的概念，且这些概念必须在首页热门概念前十名单中
        """
        # 1. 获取4板及以上的涨停股
        high_board_stocks = self.supabase.table("limit_stocks_detail")\
            .select("stock_code, stock_name, continuous_days")\
            .eq("trade_date", trade_date)\
            .eq("limit_type", "limit_up")\
            .gte("continuous_days", 4)\
            .execute()

        if not high_board_stocks.data:
            return {"available": False, "concepts": []}

        # 2. 获取当日热门概念前十名单（含涨停数，用于判断是否主线）
        top10_concepts = self.supabase.table("hot_concepts")\
            .select("concept_name, limit_up_count")\
            .eq("trade_date", trade_date)\
            .eq("is_anomaly", False)\
            .lte("rank", 10)\
            .execute()

        if not top10_concepts.data:
            logger.warning(f"未查询到当日热门概念前十")
            return {"available": False, "concepts": []}

        # 构建前十概念名称集合（用于快速查找）
        top10_names = {item["concept_name"] for item in top10_concepts.data}
        # 构建主线板块集合（TOP10 且 涨停数>=8）
        main_line_names = {item["concept_name"] for item in top10_concepts.data if (item.get("limit_up_count") or 0) >= 8}
        logger.info(f"当日热门概念前十: {top10_names}, 其中主线板块: {main_line_names}")

        # 3. 提取4板+股票代码（转换为6位格式）
        high_board_codes = []
        for stock in high_board_stocks.data:
            code_6 = stock["stock_code"].split('.')[0] if '.' in stock["stock_code"] else stock["stock_code"]
            high_board_codes.append(code_6)

        # 4. 从 ths_concept_members 表查询4板+股票的概念归属
        concept_members = self.supabase.table("ths_concept_members")\
            .select("stock_code, concept_name")\
            .in_("stock_code", high_board_codes)\
            .execute()

        if not concept_members.data:
            logger.warning(f"未从 ths_concept_members 表查询到4板+股票的概念数据")
            return {"available": False, "concepts": []}

        # 5. 筛选出在前十名单中的概念
        # 构建 概念 -> 4板+股票列表 的映射（只保留前十概念）
        concept_high_board_map: Dict[str, List[str]] = {}
        for item in concept_members.data:
            concept = item["concept_name"]
            # 只保留在前十名单中的概念
            if concept not in top10_names:
                continue

            if concept not in concept_high_board_map:
                concept_high_board_map[concept] = []
            concept_high_board_map[concept].append(item["stock_code"])

        if not concept_high_board_map:
            logger.info(f"概念梯队分析: 没有4板+股票属于前十热门概念")
            return {"available": False, "concepts": []}

        logger.info(f"概念梯队分析: 找到 {len(concept_high_board_map)} 个前十概念包含4板+股票")

        # 6. 对每个前十概念，获取其完整梯队（查询该概念的所有涨停股）
        # 首先获取今日所有涨停股
        all_limit_stocks = self.supabase.table("limit_stocks_detail")\
            .select("stock_code, stock_name, continuous_days")\
            .eq("trade_date", trade_date)\
            .eq("limit_type", "limit_up")\
            .gte("continuous_days", 1)\
            .execute()

        if not all_limit_stocks.data:
            return {"available": False, "concepts": []}

        # 构建股票代码映射（6位代码 -> 股票信息）
        limit_stock_map = {}
        for stock in all_limit_stocks.data:
            code_6 = stock["stock_code"].split('.')[0] if '.' in stock["stock_code"] else stock["stock_code"]
            limit_stock_map[code_6] = stock

        # 7. 对每个前十概念，查询其成分股并构建梯队
        result_concepts = []
        for concept in concept_high_board_map.keys():
            # 从 ths_concept_members 查询该概念的所有成分股
            members_result = self.supabase.table("ths_concept_members")\
                .select("stock_code")\
                .eq("concept_name", concept)\
                .execute()

            if not members_result.data:
                continue

            # 提取成分股代码
            member_codes = [item["stock_code"] for item in members_result.data]

            # 找出该概念在今日涨停的成分股
            concept_limit_stocks = []
            for code in member_codes:
                if code in limit_stock_map:
                    concept_limit_stocks.append(limit_stock_map[code])

            if not concept_limit_stocks:
                continue

            max_continuous = max([s["continuous_days"] for s in concept_limit_stocks])

            # 构建梯队分布
            ladder_dict: Dict[int, List[str]] = {}
            for stock in concept_limit_stocks:
                days = stock["continuous_days"]
                if days not in ladder_dict:
                    ladder_dict[days] = []
                ladder_dict[days].append(stock["stock_name"])

            # 筛选：梯队层级必须>=3（如1板+2板+4板）
            if len(ladder_dict) < 3:
                continue

            ladder_list = [
                {"days": days, "count": len(names), "stocks": names}
                for days, names in sorted(ladder_dict.items(), reverse=True)
            ]

            # 判断梯队状态
            total_count = len(concept_limit_stocks)
            if total_count == 1:
                status = "alone"    # 独苗
            elif total_count >= 3 and len(ladder_dict) >= 2:
                status = "complete"  # 梯队完整
            else:
                status = "normal"

            result_concepts.append({
                "concept_name": concept,
                "max_continuous_days": max_continuous,
                "total_limit_up_count": total_count,
                "concept_change_pct": None,  # 需要额外查询概念涨幅
                "ladder_status": status,
                "is_main_line": concept in main_line_names,  # 标注是否主线板块
                "ladder": ladder_list
            })

        logger.info(f"概念梯队分析: 筛选出 {len(result_concepts)} 个符合条件的前十概念梯队")

        # 按最高连板数排序
        result_concepts.sort(key=lambda x: (-x["max_continuous_days"], -x["total_limit_up_count"]))

        return {"available": True, "concepts": result_concepts}

    async def _get_leader_analysis(self, trade_date: str) -> List[dict]:
        """
        获取龙头股深度分析（使用 ths_concept_members 表）

        分析4板+龙头股的技术面、资金面、梯队情况，并给出综合评估
        """
        # 1. 获取4板+龙头股
        leaders = self.supabase.table("limit_stocks_detail")\
            .select("*")\
            .eq("trade_date", trade_date)\
            .eq("limit_type", "limit_up")\
            .gte("continuous_days", 4)\
            .order("continuous_days", desc=True)\
            .execute()

        if not leaders.data:
            return []

        max_days = leaders.data[0]["continuous_days"]

        # 2. 批量查询所有龙头股的概念
        leader_codes = []
        for stock in leaders.data:
            code_6 = stock["stock_code"].split('.')[0] if '.' in stock["stock_code"] else stock["stock_code"]
            leader_codes.append(code_6)

        # 从 ths_concept_members 表批量查询概念
        concepts_result = self.supabase.table("ths_concept_members")\
            .select("stock_code, concept_name")\
            .in_("stock_code", leader_codes)\
            .execute()

        # 构建 股票 -> 概念列表 的映射
        stock_concepts_map: Dict[str, List[str]] = {}
        if concepts_result.data:
            for item in concepts_result.data:
                code = item["stock_code"]
                concept = item["concept_name"]
                if code not in stock_concepts_map:
                    stock_concepts_map[code] = []
                stock_concepts_map[code].append(concept)

        # 3. 逐个分析龙头股
        result = []
        for stock in leaders.data:
            # 获取该股票的概念列表
            code_6 = stock["stock_code"].split('.')[0] if '.' in stock["stock_code"] else stock["stock_code"]
            concepts = stock_concepts_map.get(code_6, [])

            # 技术面分析
            technical = self._analyze_technical(stock)

            # 资金面分析
            capital = self._analyze_capital(stock)

            # 梯队分析
            ladder = await self._get_stock_ladder(trade_date, stock)

            # 综合评估
            evaluation = self._evaluate_leader(stock, technical, capital, ladder)

            result.append({
                "stock_code": stock["stock_code"],
                "stock_name": stock["stock_name"],
                "continuous_days": stock["continuous_days"],
                "is_top": stock["continuous_days"] == max_days,
                "concepts": concepts,  # 使用新表的概念数据
                "industry": stock.get("industry") or "",
                "technical": technical,
                "capital": capital,
                "ladder": ladder,
                "evaluation": evaluation
            })

        return result

    def _analyze_technical(self, stock: dict) -> dict:
        """分析技术面"""
        first_time = stock.get("first_limit_time") or ""
        opening_times = stock.get("opening_times") or 0
        turnover_rate = stock.get("turnover_rate") or 0

        # 首封时间评级
        if first_time and first_time < "10:00:00":
            first_time_level = "strong"
        elif first_time and first_time < "13:30:00":
            first_time_level = "normal"
        else:
            first_time_level = "weak"

        # 开板次数评级
        if opening_times == 0:
            opening_level = "strong"
        elif opening_times <= 1:
            opening_level = "normal"
        else:
            opening_level = "weak"

        # 换手率评级
        if turnover_rate and turnover_rate < 20:
            turnover_level = "strong"
        elif turnover_rate and turnover_rate < 35:
            turnover_level = "normal"
        else:
            turnover_level = "weak"

        return {
            "first_limit_time": first_time,
            "first_limit_time_level": first_time_level,
            "last_limit_time": stock.get("last_limit_time") or "",
            "opening_times": opening_times,
            "opening_times_level": opening_level,
            "turnover_rate": turnover_rate,
            "turnover_rate_level": turnover_level,
            "amount": stock.get("amount") or 0
        }

    def _analyze_capital(self, stock: dict) -> dict:
        """分析资金面"""
        main_inflow = stock.get("main_net_inflow") or 0
        main_inflow_pct = stock.get("main_net_inflow_pct") or 0
        sealed_amount = stock.get("sealed_amount") or 0
        amount = stock.get("amount") or 1

        # 主力净流入评级
        if main_inflow > 0 and main_inflow_pct > 10:
            inflow_level = "strong"
        elif main_inflow > 0:
            inflow_level = "normal"
        else:
            inflow_level = "weak"

        # 封单比评级
        sealed_ratio = (sealed_amount / amount * 100) if amount > 0 else 0
        if sealed_ratio > 50:
            sealed_level = "strong"
        elif sealed_ratio > 20:
            sealed_level = "normal"
        else:
            sealed_level = "weak"

        return {
            "main_net_inflow": main_inflow,
            "main_net_inflow_level": inflow_level,
            "main_net_inflow_pct": main_inflow_pct,
            "sealed_amount": sealed_amount,
            "sealed_ratio": round(sealed_ratio, 1),
            "sealed_ratio_level": sealed_level
        }

    async def _get_stock_ladder(self, trade_date: str, stock: dict) -> dict:
        """获取股票所属概念的梯队情况（使用 ths_concept_members 表）"""
        # 1. 从 ths_concept_members 表查询该股票的所有概念
        stock_code = stock["stock_code"].split('.')[0] if '.' in stock["stock_code"] else stock["stock_code"]

        concept_result = self.supabase.table("ths_concept_members")\
            .select("concept_name")\
            .eq("stock_code", stock_code)\
            .execute()

        if not concept_result.data:
            return {
                "concept_name": None,
                "status": "alone",
                "follower_count": 0,
                "ladder_detail": []
            }

        # 取第一个概念作为主概念
        main_concept = concept_result.data[0]["concept_name"]

        # 2. 查询当日所有涨停股
        all_stocks = self.supabase.table("limit_stocks_detail")\
            .select("stock_code, stock_name, continuous_days")\
            .eq("trade_date", trade_date)\
            .eq("limit_type", "limit_up")\
            .execute()

        if not all_stocks.data:
            return {
                "concept_name": main_concept,
                "status": "alone",
                "follower_count": 0,
                "ladder_detail": []
            }

        # 3. 提取其他涨停股代码（排除自己）
        other_stock_codes = []
        other_stock_map = {}
        for s in all_stocks.data:
            if s["stock_code"] == stock["stock_code"]:
                continue
            code_6 = s["stock_code"].split('.')[0] if '.' in s["stock_code"] else s["stock_code"]
            other_stock_codes.append(code_6)
            other_stock_map[code_6] = s

        if not other_stock_codes:
            return {
                "concept_name": main_concept,
                "status": "alone",
                "follower_count": 0,
                "ladder_detail": []
            }

        # 4. 查询同概念的其他涨停股
        same_concept_members = self.supabase.table("ths_concept_members")\
            .select("stock_code")\
            .eq("concept_name", main_concept)\
            .in_("stock_code", other_stock_codes)\
            .execute()

        if not same_concept_members.data:
            return {
                "concept_name": main_concept,
                "status": "alone",
                "follower_count": 0,
                "ladder_detail": []
            }

        # 5. 构建同概念股票列表
        same_concept_stocks = []
        for item in same_concept_members.data:
            code = item["stock_code"]
            stock_info = other_stock_map.get(code)
            if stock_info:
                same_concept_stocks.append(stock_info)

        if not same_concept_stocks:
            return {
                "concept_name": main_concept,
                "status": "alone",
                "follower_count": 0,
                "ladder_detail": []
            }

        # 6. 构建梯队
        ladder_dict: Dict[int, List[str]] = {}
        for s in same_concept_stocks:
            days = s["continuous_days"]
            if days not in ladder_dict:
                ladder_dict[days] = []
            ladder_dict[days].append(s["stock_name"])

        ladder_detail = [
            {"days": days, "count": len(names), "stocks": names[:3]}
            for days, names in sorted(ladder_dict.items(), reverse=True)
        ]

        # 7. 判断梯队状态
        if len(same_concept_stocks) >= 3:
            status = "complete"
        elif len(same_concept_stocks) >= 1:
            status = "normal"
        else:
            status = "alone"

        return {
            "concept_name": main_concept,
            "status": status,
            "follower_count": len(same_concept_stocks),
            "ladder_detail": ladder_detail
        }

    def _evaluate_leader(self, stock: dict, technical: dict, capital: dict, ladder: dict) -> dict:
        """综合评估龙头"""
        positive = []
        negative = []

        # 技术面评估
        if technical["first_limit_time_level"] == "strong":
            positive.append("早盘封板，强势")
        elif technical["first_limit_time_level"] == "weak":
            negative.append("尾盘封板，弱势")

        if technical["opening_times_level"] == "strong":
            positive.append("未开板，封单稳固")
        elif technical["opening_times_level"] == "weak":
            negative.append(f"开板{technical['opening_times']}次，烂板")

        if technical["turnover_rate_level"] == "weak":
            tr = technical.get("turnover_rate") or 0
            negative.append(f"换手率{tr:.1f}%，获利盘多")

        # 资金面评估
        if capital["main_net_inflow_level"] == "strong":
            inflow = capital.get("main_net_inflow") or 0
            positive.append(f"主力净流入{inflow/100000000:.1f}亿")
        elif capital["main_net_inflow_level"] == "weak":
            negative.append("主力资金流出")

        if capital["sealed_ratio_level"] == "strong":
            ratio = capital.get("sealed_ratio") or 0
            positive.append(f"封单强，封单比{ratio:.0f}%")
        elif capital["sealed_ratio_level"] == "weak":
            negative.append("封单弱，易炸板")

        # 梯队评估
        if ladder["status"] == "complete":
            positive.append("板块梯队完整，有跟风")
        elif ladder["status"] == "alone":
            negative.append("独苗，无跟风")

        # 高位风险
        continuous_days = stock.get("continuous_days") or 0
        if continuous_days >= 5:
            negative.append(f"{continuous_days}连板高位，溢价空间有限")

        # 综合判断
        if len(positive) > len(negative):
            conclusion = "opportunity"
            conclusion_text = "机会 > 风险"
        elif len(positive) < len(negative):
            conclusion = "risk"
            conclusion_text = "风险 > 机会"
        else:
            conclusion = "neutral"
            conclusion_text = "机会与风险并存"

        return {
            "positive_factors": positive,
            "negative_factors": negative,
            "conclusion": conclusion,
            "conclusion_text": conclusion_text
        }

    def _calculate_promotion_rate(self, today: dict, yesterday: dict) -> List[dict]:
        """计算分层晋级率"""
        result = []
        for n in range(1, 10):
            yesterday_count = yesterday.get(str(n), 0)
            today_count = today.get(str(n + 1), 0)

            if yesterday_count > 0:
                rate = round(today_count / yesterday_count * 100, 1)
                result.append({
                    "from_days": n,
                    "to_days": n + 1,
                    "yesterday_count": yesterday_count,
                    "today_count": today_count,
                    "rate": rate
                })

        return result

    def _get_recent_stages(self, trade_date: str, days: int = 3) -> List[str]:
        """
        获取最近N天的情绪阶段（用于判断退潮前置条件）
        简化实现：检查最近N天是否有高空间板（>=5）
        """
        try:
            # 获取最近N天的市场情绪数据
            result = self.supabase.table("market_sentiment")\
                .select("trade_date, continuous_limit_distribution")\
                .lt("trade_date", trade_date)\
                .order("trade_date", desc=True)\
                .limit(days)\
                .execute()

            if not result.data:
                return []

            stages = []
            for item in result.data:
                distribution = item.get("continuous_limit_distribution") or {}
                if isinstance(distribution, str):
                    import json
                    distribution = json.loads(distribution)

                if distribution:
                    max_height = max([int(k) for k in distribution.keys()])
                    # 简化判断：空间>=5视为曾有加速/高潮
                    if max_height >= 7:
                        stages.append("高潮期")
                    elif max_height >= 5:
                        stages.append("加速期")
                    else:
                        stages.append("其他")
                else:
                    stages.append("其他")

            return stages

        except Exception as e:
            logger.warning(f"获取最近阶段失败: {e}")
            return []

    def _get_yesterday_limit_premium_stats(self, trade_date: str) -> Dict:
        """
        获取昨日涨停股今日表现统计
        从 yesterday_limit_performance 表获取
        """
        try:
            result = self.supabase.table("yesterday_limit_performance")\
                .select("*")\
                .eq("trade_date", trade_date)\
                .execute()

            if not result.data:
                return {}

            records = result.data
            total = len(records)

            # 有涨跌幅数据的记录
            with_change = [r for r in records if r.get("today_change_pct") is not None]
            if not with_change:
                return {"total": total, "with_data": 0}

            # 计算整体溢价率
            changes = [r["today_change_pct"] for r in with_change]
            avg_premium = round(sum(changes) / len(changes), 2)

            # 计算开盘溢价
            with_open = [r for r in records if r.get("today_open_pct") is not None]
            avg_open_premium = round(sum(r["today_open_pct"] for r in with_open) / len(with_open), 2) if with_open else None

            # 分层统计
            first_board = [r for r in records if r.get("yesterday_continuous_days") == 1]
            second_board = [r for r in records if r.get("yesterday_continuous_days") == 2]
            high_board = [r for r in records if (r.get("yesterday_continuous_days") or 0) >= 3]

            def calc_avg(lst):
                valid = [r["today_change_pct"] for r in lst if r.get("today_change_pct") is not None]
                return round(sum(valid) / len(valid), 2) if valid else None

            # 晋级数（今日涨停）
            promotion_count = sum(1 for r in records if r.get("is_limit_up"))
            promotion_rate = round(promotion_count / total * 100, 1) if total > 0 else 0

            # 大面数（跌>5%）
            big_loss_count = sum(1 for r in records if r.get("is_big_loss"))
            big_loss_rate = round(big_loss_count / total * 100, 1) if total > 0 else 0

            # 高位大面（3板+跌>5%）
            high_board_big_loss = sum(1 for r in high_board if r.get("is_big_loss"))
            high_board_big_loss_rate = round(high_board_big_loss / len(high_board) * 100, 1) if high_board else 0

            return {
                "total": total,
                "with_data": len(with_change),
                "avg_premium": avg_premium,           # 整体溢价率
                "avg_open_premium": avg_open_premium, # 开盘溢价率
                "first_board_count": len(first_board),
                "first_board_premium": calc_avg(first_board),
                "second_board_count": len(second_board),
                "second_board_premium": calc_avg(second_board),
                "high_board_count": len(high_board),
                "high_board_premium": calc_avg(high_board),
                "promotion_count": promotion_count,
                "promotion_rate": promotion_rate,
                "big_loss_count": big_loss_count,
                "big_loss_rate": big_loss_rate,
                "high_board_big_loss": high_board_big_loss,
                "high_board_big_loss_rate": high_board_big_loss_rate
            }

        except Exception as e:
            logger.error(f"获取昨日涨停表现统计失败: {e}")
            return {}

    def _get_previous_emotion_stage(self, yesterday: Optional[str], yesterday_data: Optional[dict]) -> Optional[str]:
        """
        获取昨日情绪阶段（用于惯性区间判断）

        计算昨日的原始阶段（不带惯性），避免递归问题
        """
        if not yesterday or not yesterday_data:
            return None

        try:
            # 获取昨日的前一天
            prev_yesterday = _get_previous_trading_date(yesterday)

            # 获取昨日空间板高度
            yesterday_distribution = yesterday_data.get("continuous_limit_distribution") or {}
            if isinstance(yesterday_distribution, str):
                import json
                yesterday_distribution = json.loads(yesterday_distribution)
            yesterday_space_height = max([int(k) for k in yesterday_distribution.keys()]) if yesterday_distribution else 0

            # 获取昨日涨停数和跌停数
            yesterday_limit_up = yesterday_data.get("limit_up_count") or 0
            yesterday_limit_down = yesterday_data.get("limit_down_count") or 0
            yesterday_explosion_rate = yesterday_data.get("explosion_rate") or 0

            # 获取昨日的溢价统计（前天涨停股在昨天的表现）
            yesterday_premium_stats = self._get_yesterday_limit_premium_stats(yesterday)

            # 获取昨日的晋级率（需要前天的连板分布）
            prev_yesterday_data = None
            if prev_yesterday:
                prev_result = self.supabase.table("market_sentiment")\
                    .select("continuous_limit_distribution").eq("trade_date", prev_yesterday).execute()
                if prev_result.data:
                    prev_yesterday_data = prev_result.data[0]

            prev_distribution = {}
            if prev_yesterday_data:
                prev_distribution = prev_yesterday_data.get("continuous_limit_distribution") or {}
                if isinstance(prev_distribution, str):
                    import json
                    prev_distribution = json.loads(prev_distribution)

            yesterday_promotion_details = self._calculate_promotion_rate(yesterday_distribution, prev_distribution)

            # 计算昨日原始阶段（不带惯性，previous_stage=None）
            stage, _, _ = self._determine_emotion_stage(
                space_height=yesterday_space_height,
                explosion_rate=yesterday_explosion_rate,
                promotion_details=yesterday_promotion_details,
                limit_up_count=yesterday_limit_up,
                limit_down_count=yesterday_limit_down,
                premium_stats=yesterday_premium_stats,
                recent_stages=[],  # 不需要退潮判断
                previous_stage=None  # 不递归，直接用原始阶段
            )

            logger.debug(f"昨日({yesterday})原始阶段: {stage}")
            return stage

        except Exception as e:
            logger.warning(f"获取昨日情绪阶段失败: {e}")
            return None

    def _score_factor(self, value: float, thresholds: List[tuple]) -> int:
        """
        因子梯度打分
        thresholds: [(阈值, 分数), ...] 从小到大排列
        """
        if value is None:
            return 0
        for threshold, score in thresholds:
            if value <= threshold:
                return score
        return thresholds[-1][1]  # 超过最大阈值返回最后一个分数

    def _determine_emotion_stage(
        self,
        space_height: int,
        explosion_rate: float,
        promotion_details: List[dict],
        limit_up_count: int = 0,
        limit_down_count: int = 0,
        premium_stats: Dict = None,
        recent_stages: List[str] = None,
        previous_stage: str = None
    ) -> tuple:
        """
        v2.0 多因子梯度打分 + 总分映射阶段

        设计思路：
        1. 每个因子独立打分（-2 到 +2）
        2. 加权求和得到总分
        3. 用总分区间映射到情绪阶段
        4. 退潮期需要前置条件（最近有加速/高潮）
        5. 边界模糊时考虑阶段惯性

        因子打分表：
        | 因子 | -2 | -1 | 0 | +1 | +2 |
        |------|----|----|---|----|----|
        | 空间板 | ≤2 | 3-4 | - | 5-6 | ≥7 |
        | 涨停数 | <20 | 20-40 | 40-60 | 60-80 | ≥80 |
        | 炸板率 | >50 | 40-50 | 25-40 | 15-25 | <15 |
        | 溢价率 | <-3 | -3~-1 | -1~+1 | +1~+3 | >+3 |
        | 大面率 | >40 | 30-40 | 20-30 | 10-20 | <10 |
        | 高位大面 | >50 | 30-50 | 15-30 | <15 | - |
        | 晋级率 | <20 | 20-40 | 40-50 | 50-60 | >60 |

        总分映射：
        S ≤ -5     → 冰点期
        -5 < S ≤ 0 → 回暖期
        0 < S ≤ 5  → 加速期
        S > 5      → 高潮期
        退潮期：前置条件 + 恶化信号
        """
        premium_stats = premium_stats or {}
        recent_stages = recent_stages or []

        # === 1. 提取各因子原始值 ===
        avg_premium = premium_stats.get("avg_premium")
        big_loss_rate = premium_stats.get("big_loss_rate", 0)
        high_board_big_loss_rate = premium_stats.get("high_board_big_loss_rate", 0)

        avg_promotion_rate = 0
        if promotion_details:
            avg_promotion_rate = sum(p["rate"] for p in promotion_details) / len(promotion_details)

        # === 2. 各因子梯度打分 ===
        factor_scores = {}

        # 空间板高度：≤2=-2, 3-4=-1, 5-6=+1, ≥7=+2
        if space_height <= 2:
            factor_scores["空间板高度"] = -2
        elif space_height <= 4:
            factor_scores["空间板高度"] = -1
        elif space_height <= 6:
            factor_scores["空间板高度"] = 1
        else:
            factor_scores["空间板高度"] = 2

        # 涨停数：<10=-2, 10-29=-1, 30-69=0, 70-89=+1, ≥90=+2
        if limit_up_count < 10:
            factor_scores["涨停数"] = -2
        elif limit_up_count < 30:
            factor_scores["涨停数"] = -1
        elif limit_up_count < 70:
            factor_scores["涨停数"] = 0
        elif limit_up_count < 90:
            factor_scores["涨停数"] = 1
        else:
            factor_scores["涨停数"] = 2

        # 跌停数（反向）：≥50=-2, 30-49=-1, 10-29=0, 1-9=+1, =0=+1
        # v2.2: 跌停数=0也只给+1，避免高估无跌停的情况
        if limit_down_count >= 50:
            factor_scores["跌停数"] = -2
        elif limit_down_count >= 30:
            factor_scores["跌停数"] = -1
        elif limit_down_count >= 10:
            factor_scores["跌停数"] = 0
        else:
            # 0-9都是+1，不再区分0和1-9
            factor_scores["跌停数"] = 1

        # 炸板率（反向）：>50=-2, 35-50=-1, 25-35=0, 15-25=+1, <15=+2
        if explosion_rate > 50:
            factor_scores["炸板率"] = -2
        elif explosion_rate > 35:
            factor_scores["炸板率"] = -1
        elif explosion_rate > 25:
            factor_scores["炸板率"] = 0
        elif explosion_rate > 15:
            factor_scores["炸板率"] = 1
        else:
            factor_scores["炸板率"] = 2

        # 溢价率：<-3=-2, -3~-1=-1, -1~+1=0, +1~+3=+1, >+3=+2
        if avg_premium is None:
            factor_scores["溢价率"] = 0
        elif avg_premium < -3:
            factor_scores["溢价率"] = -2
        elif avg_premium < -1:
            factor_scores["溢价率"] = -1
        elif avg_premium < 1:
            factor_scores["溢价率"] = 0
        elif avg_premium < 3:
            factor_scores["溢价率"] = 1
        else:
            factor_scores["溢价率"] = 2

        # 大面率（反向）：>40=-2, 30-40=-1, 20-30=0, 10-20=+1, <10=+2
        if big_loss_rate > 40:
            factor_scores["大面率"] = -2
        elif big_loss_rate > 30:
            factor_scores["大面率"] = -1
        elif big_loss_rate > 20:
            factor_scores["大面率"] = 0
        elif big_loss_rate > 10:
            factor_scores["大面率"] = 1
        else:
            factor_scores["大面率"] = 2

        # 高位大面率（反向）：>50=-2, 30-50=-1, 15-30=0, <15=+1
        if high_board_big_loss_rate > 50:
            factor_scores["高位大面率"] = -2
        elif high_board_big_loss_rate > 30:
            factor_scores["高位大面率"] = -1
        elif high_board_big_loss_rate > 15:
            factor_scores["高位大面率"] = 0
        else:
            factor_scores["高位大面率"] = 1

        # 晋级率：<15%=-2, 15-25%=-1, 25-50%=0, 50-60%=+1, >60%=+2
        # v2.2: 细化低区间，更好区分冰点期
        if avg_promotion_rate < 15:
            factor_scores["晋级率"] = -2
        elif avg_promotion_rate < 25:
            factor_scores["晋级率"] = -1
        elif avg_promotion_rate < 50:
            factor_scores["晋级率"] = 0
        elif avg_promotion_rate < 60:
            factor_scores["晋级率"] = 1
        else:
            factor_scores["晋级率"] = 2

        # === 3. 计算总分（可加权，暂时等权） ===
        total_score = sum(factor_scores.values())

        # === 4. 退潮期特殊判断 ===
        # 前置条件：最近3天内有加速或高潮
        had_recent_peak = any(s in ["加速期", "高潮期"] for s in recent_stages)
        # 恶化信号：大面率>25% 且 溢价<0 且 空间板还没跌到冰点
        # v2.2: 空间板条件从>=3改为>=4，更严谨地判断退潮
        is_deteriorating = (
            big_loss_rate > 25 and
            (avg_premium is not None and avg_premium < 0) and
            space_height >= 4  # 还没跌到冰点水平
        )

        # === 5. 总分映射阶段（原始阶段） ===
        # 8因子，总分范围-16~+16，按比例调整阈值
        if had_recent_peak and is_deteriorating and total_score < 0:
            # 满足退潮条件
            stage_raw = "退潮期"
        elif total_score <= -6:
            stage_raw = "冰点期"
        elif total_score <= 0:
            stage_raw = "回暖期"
        elif total_score <= 6:
            stage_raw = "加速期"
        else:
            stage_raw = "高潮期"

        # === 6. 惯性区间机制 (v2.3) ===
        # 边界±1范围内沿用昨日阶段，减少边界抖动
        # 只检查相邻阶段之间的边界，而不是所有边界
        stage = stage_raw  # 默认使用原始阶段
        used_inertia = False

        if previous_stage and previous_stage != stage_raw:
            # 阶段发生变化，找出相邻阶段的边界
            stage_order = ["冰点期", "回暖期", "加速期", "高潮期"]
            # 退潮期特殊处理：视为在高潮期和回暖期之间
            if previous_stage == "退潮期":
                previous_stage_for_check = "回暖期"
            else:
                previous_stage_for_check = previous_stage

            if stage_raw == "退潮期":
                stage_raw_for_check = "回暖期"
            else:
                stage_raw_for_check = stage_raw

            # 找出两个阶段之间的边界
            boundary_map = {
                ("冰点期", "回暖期"): -6,
                ("回暖期", "冰点期"): -6,
                ("回暖期", "加速期"): 0,
                ("加速期", "回暖期"): 0,
                ("加速期", "高潮期"): 6,
                ("高潮期", "加速期"): 6,
            }

            relevant_boundary = boundary_map.get((previous_stage_for_check, stage_raw_for_check))

            if relevant_boundary is not None:
                # 检查是否在相关边界的±1范围内
                if abs(total_score - relevant_boundary) <= 1:
                    stage = previous_stage
                    used_inertia = True
                    logger.info(f"惯性区间生效: 总分={total_score}, 边界={relevant_boundary}, 原始阶段={stage_raw}, 沿用昨日={previous_stage}")

        # 颜色映射
        color_map = {
            "冰点期": "blue",
            "回暖期": "yellow",
            "加速期": "orange",
            "高潮期": "red",
            "退潮期": "green"
        }

        logger.info(f"情绪阶段判断 v2.3: 因子得分={factor_scores}, 总分={total_score}, "
                    f"原始阶段={stage_raw}, 昨日阶段={previous_stage}, 惯性生效={used_inertia}, "
                    f"最终阶段={stage}")

        return (stage, color_map[stage], {
            "factor_scores": factor_scores,
            "total_score": total_score,
            "had_recent_peak": had_recent_peak,
            "is_deteriorating": is_deteriorating,
            "stage_raw": stage_raw,
            "used_inertia": used_inertia,
            "previous_stage": previous_stage
        })

    def _parse_concepts(self, concepts: Any) -> List[str]:
        """解析概念字段"""
        if not concepts:
            return []
        if isinstance(concepts, list):
            return concepts
        if isinstance(concepts, str):
            try:
                import json
                return json.loads(concepts)
            except:
                return [concepts]
        return []

    def _empty_emotion_dashboard(self) -> dict:
        """空的情绪仪表盘"""
        return {
            "space_height": 0,
            "limit_up_count": 0,
            "limit_up_change": None,
            "explosion_rate": 0,
            "overall_promotion_rate": None,
            "promotion_details": [],
            "emotion_stage": "冰点期",
            "emotion_stage_color": "blue"
        }

    def _empty_yesterday_performance(self) -> dict:
        """空的昨日涨停表现"""
        return {
            "yesterday_limit_up_count": 0,
            "today_avg_change": None,
            "up_count": 0,
            "down_count": 0,
            "big_loss_count": 0,
            "big_loss_rate": 0,
            "big_loss_stocks": []
        }
