"""
回测服务：保存和查询溢价评分回测数据
"""
from loguru import logger
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import tushare as ts
import os

from app.utils.supabase_client import get_supabase
from app.services.premium_probability_service import PremiumProbabilityService


class BacktestService:
    """回测数据服务"""

    def __init__(self):
        self.supabase = get_supabase()
        self.premium_service = PremiumProbabilityService()

        # 初始化Tushare API（用于获取日线行情）
        token = os.getenv('TUSHARE_TOKEN')
        if token:
            self.ts_api = ts.pro_api(token)
        else:
            self.ts_api = None
            logger.warning("TUSHARE_TOKEN未配置，次日数据查询可能不完整")

    async def save_backtest_record(
        self,
        stock_code: str,
        trade_date: str,
        next_trade_date: Optional[str] = None,
        cached_market_data: Optional[Dict] = None
    ) -> bool:
        """
        保存单个股票的回测记录

        Args:
            stock_code: 股票代码
            trade_date: 评测日期（涨停日）YYYY-MM-DD
            next_trade_date: 次日交易日期，不传则自动计算

        Returns:
            bool: 是否保存成功
        """
        try:
            # 1. 计算溢价评分（使用缓存的市场数据）
            score_result = await self.premium_service.calculate_premium_score(
                stock_code, trade_date, cached_market_data
            )

            if not score_result:
                logger.warning(f"股票 {stock_code} {trade_date} 评分失败")
                return False

            # 2. 获取次日交易数据
            if not next_trade_date:
                # 自动计算下一个交易日（简单处理，假设+1天）
                from datetime import datetime, timedelta
                trade_dt = datetime.strptime(trade_date, "%Y-%m-%d")
                next_dt = trade_dt + timedelta(days=1)
                next_trade_date = next_dt.strftime("%Y-%m-%d")

            next_day_data = self._get_next_day_data(stock_code, next_trade_date)

            # 3. 构建回测记录
            record = {
                "stock_code": stock_code,
                "stock_name": score_result.stock_name,
                "trade_date": trade_date,
                "continuous_days": score_result.position_detail.continuous_days,
                "total_score": score_result.total_score,
                "premium_level": score_result.premium_level,
                "technical_score": score_result.technical_score,
                "capital_score": score_result.capital_score,
                "theme_score": score_result.theme_score,
                "position_score": score_result.position_score,
                "market_score": score_result.market_score,
            }

            # 添加次日数据
            if next_day_data:
                record.update({
                    "next_trade_date": next_trade_date,
                    "next_day_change_pct": next_day_data.get("change_pct"),
                    "next_day_close_price": next_day_data.get("close_price"),
                    "is_next_day_limit_up": next_day_data.get("limit_type") == "limit_up",
                    "is_next_day_limit_down": next_day_data.get("limit_type") == "limit_down",
                    "next_day_turnover_rate": next_day_data.get("turnover_rate"),
                })

                # 判断预测准确性
                prediction_result = self._evaluate_prediction(
                    score_result.total_score,
                    next_day_data.get("change_pct")
                )
                record["prediction_result"] = prediction_result
                record["is_profitable"] = next_day_data.get("change_pct", 0) > 0

            # 4. 保存到数据库（upsert）
            response = self.supabase.table("premium_score_backtest")\
                .upsert(record, on_conflict="stock_code,trade_date")\
                .execute()

            logger.info(f"✅ 保存回测记录: {stock_code} {trade_date} 评分{score_result.total_score:.2f}")
            return True

        except Exception as e:
            logger.error(f"保存回测记录失败: {e}", exc_info=True)
            return False

    async def batch_save_backtest(
        self,
        trade_date: str,
        next_trade_date: Optional[str] = None,
        limit: int = 50
    ) -> Dict:
        """
        批量保存某天所有涨停股票的回测记录

        Args:
            trade_date: 评测日期 YYYY-MM-DD
            next_trade_date: 次日交易日期
            limit: 最多处理多少只股票

        Returns:
            统计信息
        """
        logger.info(f"开始批量保存 {trade_date} 的回测数据...")

        # ⚡ 性能优化：提前计算市场环境数据（所有股票共享）
        logger.info(f"📊 预计算市场环境数据...")
        from app.services.sentiment_service import SentimentService
        sentiment_service = SentimentService()
        market_data = await sentiment_service.get_analysis(trade_date)
        logger.info(f"✅ 市场环境数据已缓存")

        # 获取当天所有涨停股票
        response = self.supabase.table("limit_stocks_detail")\
            .select("stock_code, stock_name")\
            .eq("trade_date", trade_date)\
            .eq("limit_type", "limit_up")\
            .limit(limit)\
            .execute()

        stocks = response.data
        logger.info(f"找到 {len(stocks)} 只涨停股票")

        success_count = 0
        fail_count = 0

        for stock in stocks:
            success = await self.save_backtest_record(
                stock["stock_code"],
                trade_date,
                next_trade_date,
                cached_market_data=market_data  # 复用市场数据
            )

            if success:
                success_count += 1
            else:
                fail_count += 1

        logger.info(f"批量保存完成: 成功 {success_count}, 失败 {fail_count}")

        return {
            "total": len(stocks),
            "success": success_count,
            "fail": fail_count,
            "trade_date": trade_date
        }

    def _get_next_day_data(self, stock_code: str, next_trade_date: str) -> Optional[Dict]:
        """
        获取次日交易数据

        优先从limit_stocks_detail表查询（如果次日涨停/跌停）
        如果查不到，则调用Tushare API获取日线行情数据
        """
        try:
            # 方法1: 先从涨停表查询（如果次日涨停/跌停，这里能查到更详细的数据）
            response = self.supabase.table("limit_stocks_detail")\
                .select("change_pct, close_price, turnover_rate, limit_type")\
                .eq("stock_code", stock_code)\
                .eq("trade_date", next_trade_date)\
                .execute()

            if response.data and len(response.data) > 0:
                logger.debug(f"从涨停表获取 {stock_code} {next_trade_date} 数据")
                return response.data[0]

            # 方法2: 涨停表查不到，调用Tushare API获取日线行情
            if not self.ts_api:
                logger.warning(f"{stock_code} {next_trade_date} 涨停表无数据，且Tushare未配置")
                return None

            logger.debug(f"涨停表无数据，调用Tushare获取 {stock_code} {next_trade_date} 日线数据")

            # 转换日期格式：YYYY-MM-DD -> YYYYMMDD
            ts_date = next_trade_date.replace('-', '')

            # 转换股票代码格式：XXXXXX -> XXXXXX.SH/SZ
            if stock_code.startswith(('6', '900')):
                ts_code = f"{stock_code}.SH"
            elif stock_code.startswith(('0', '2', '3')):
                ts_code = f"{stock_code}.SZ"
            elif stock_code.startswith(('8', '4')):
                ts_code = f"{stock_code}.BJ"  # 北交所
            else:
                ts_code = f"{stock_code}.SH"  # 默认上交所

            # 调用Tushare API
            df = self.ts_api.daily(
                ts_code=ts_code,
                start_date=ts_date,
                end_date=ts_date
            )

            if df is None or df.empty:
                logger.warning(f"Tushare未返回 {stock_code} {next_trade_date} 数据（可能停牌）")
                return None

            # 解析数据
            row = df.iloc[0]
            change_pct = row['pct_chg']  # 涨跌幅%
            close_price = row['close']
            turnover_rate = row['turnover_rate'] if 'turnover_rate' in df.columns else None

            # 判断涨跌停（简单判断：>=9.9%为涨停，<=-9.9%为跌停）
            limit_type = None
            if change_pct >= 9.9:
                limit_type = "limit_up"
            elif change_pct <= -9.9:
                limit_type = "limit_down"

            return {
                "change_pct": change_pct,
                "close_price": close_price,
                "turnover_rate": turnover_rate,
                "limit_type": limit_type
            }

        except Exception as e:
            logger.error(f"获取次日数据失败: {e}", exc_info=True)
            return None

    def _evaluate_prediction(self, score: float, next_pct: Optional[float]) -> str:
        """
        评估预测准确性

        规则：
        - 高分股票（≥7分）：次日应该上涨 → 上涨为正确
        - 低分股票（<5分）：次日应该下跌或平淡 → 下跌为正确
        - 中等股票（5-7分）：中性
        """
        if next_pct is None:
            return "unknown"

        if score >= 7:
            # 高分股票预期上涨
            return "correct" if next_pct > 0 else "wrong"
        elif score < 5:
            # 低分股票预期下跌
            return "correct" if next_pct <= 0 else "wrong"
        else:
            # 中等分数中性
            return "neutral"

    def query_backtest_results(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Dict], int]:
        """
        查询回测结果（支持分页）

        Args:
            start_date: 开始日期
            end_date: 结束日期
            min_score: 最低分数
            max_score: 最高分数
            page: 页码（从1开始）
            page_size: 每页条数

        Returns:
            (回测记录列表, 总记录数)
        """
        try:
            # 构建查询
            query = self.supabase.table("premium_score_backtest")\
                .select("*", count="exact")

            if start_date:
                query = query.gte("trade_date", start_date)
            if end_date:
                query = query.lte("trade_date", end_date)
            if min_score is not None:
                query = query.gte("total_score", min_score)
            if max_score is not None:
                query = query.lte("total_score", max_score)

            # 按创建时间倒序排列（最新的在前）
            query = query.order("created_at", desc=True)

            # 计算offset
            offset = (page - 1) * page_size

            # 执行分页查询
            response = query.range(offset, offset + page_size - 1).execute()

            total = response.count if hasattr(response, 'count') else len(response.data)

            return response.data, total

        except Exception as e:
            logger.error(f"查询回测结果失败: {e}")
            return [], 0

    def get_backtest_statistics(self, trade_date: Optional[str] = None) -> Dict:
        """
        获取回测统计数据

        Args:
            trade_date: 指定日期，不传则统计所有

        Returns:
            统计信息
        """
        try:
            query = self.supabase.table("premium_score_backtest").select("*")

            if trade_date:
                query = query.eq("trade_date", trade_date)

            response = query.execute()
            records = response.data

            if not records:
                return {"total": 0}

            # 统计各等级表现
            stats = {
                "total": len(records),
                "by_level": {},
                "by_score_range": {},
                "overall": {
                    "avg_next_day_pct": 0,
                    "limit_up_count": 0,
                    "limit_up_rate": 0,
                    "profitable_count": 0,
                    "profitable_rate": 0,
                    "correct_predictions": 0,
                    "prediction_accuracy": 0
                }
            }

            # 按等级分组
            level_groups = {}
            for record in records:
                level = record["premium_level"]
                if level not in level_groups:
                    level_groups[level] = []
                level_groups[level].append(record)

            # 计算各等级统计
            for level, group in level_groups.items():
                valid_group = [r for r in group if r.get("next_day_change_pct") is not None]

                if len(valid_group) == 0:
                    continue

                avg_pct = sum(r["next_day_change_pct"] for r in valid_group) / len(valid_group)
                limit_up_count = sum(1 for r in valid_group if r.get("is_next_day_limit_up"))
                profitable_count = sum(1 for r in valid_group if r.get("is_profitable"))
                correct_count = sum(1 for r in valid_group if r.get("prediction_result") == "correct")

                stats["by_level"][level] = {
                    "count": len(valid_group),
                    "avg_next_day_pct": round(avg_pct, 2),
                    "limit_up_count": limit_up_count,
                    "limit_up_rate": round(limit_up_count / len(valid_group) * 100, 2),
                    "profitable_count": profitable_count,
                    "profitable_rate": round(profitable_count / len(valid_group) * 100, 2),
                    "prediction_accuracy": round(correct_count / len(valid_group) * 100, 2) if len(valid_group) > 0 else 0
                }

            # 总体统计
            valid_records = [r for r in records if r.get("next_day_change_pct") is not None]
            if valid_records:
                stats["overall"]["avg_next_day_pct"] = round(
                    sum(r["next_day_change_pct"] for r in valid_records) / len(valid_records), 2
                )
                stats["overall"]["limit_up_count"] = sum(1 for r in valid_records if r.get("is_next_day_limit_up"))
                stats["overall"]["limit_up_rate"] = round(
                    stats["overall"]["limit_up_count"] / len(valid_records) * 100, 2
                )
                stats["overall"]["profitable_count"] = sum(1 for r in valid_records if r.get("is_profitable"))
                stats["overall"]["profitable_rate"] = round(
                    stats["overall"]["profitable_count"] / len(valid_records) * 100, 2
                )

                correct_count = sum(1 for r in valid_records if r.get("prediction_result") == "correct")
                stats["overall"]["correct_predictions"] = correct_count
                stats["overall"]["prediction_accuracy"] = round(
                    correct_count / len(valid_records) * 100, 2
                )

            return stats

        except Exception as e:
            logger.error(f"获取统计数据失败: {e}")
            return {"total": 0, "error": str(e)}

    def delete_backtest_records(self, record_ids: List[int]) -> int:
        """
        批量删除回测记录

        Args:
            record_ids: 记录ID列表

        Returns:
            删除的记录数
        """
        try:
            if not record_ids:
                return 0

            # Supabase 批量删除
            response = self.supabase.table("premium_score_backtest")\
                .delete()\
                .in_("id", record_ids)\
                .execute()

            deleted_count = len(response.data) if response.data else 0
            logger.info(f"成功删除 {deleted_count} 条回测记录")

            return deleted_count

        except Exception as e:
            logger.error(f"删除回测记录失败: {e}")
            raise
