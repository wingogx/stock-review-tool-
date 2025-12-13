"""
昨日涨停股今日表现数据采集器

用途：采集昨日涨停股今日的行情表现，用于计算情绪周期核心因子
- 昨日涨停溢价率
- 大面率（跌>5%）
- 高位大面率
- 晋级率

数据来源：
- 昨日涨停股：从 limit_stocks_detail 表获取
- 今日行情：Tushare daily 接口
"""

import os
import tushare as ts
from datetime import datetime
from typing import Optional, List, Dict
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


class YesterdayLimitCollector:
    """昨日涨停股今日表现采集器"""

    def __init__(self):
        self.supabase = get_supabase()
        self._tushare_pro = None

    @property
    def tushare_pro(self):
        """延迟初始化 Tushare Pro API"""
        if self._tushare_pro is None:
            token = os.getenv("TUSHARE_TOKEN")
            if token:
                try:
                    http_url = os.getenv("TUSHARE_HTTP_URL")
                    if http_url:
                        # 使用自定义HTTP URL（高级账号）
                        self._tushare_pro = ts.pro_api()
                        self._tushare_pro._DataApi__token = token
                        self._tushare_pro._DataApi__http_url = http_url
                        logger.info(f"✅ Tushare Pro API 初始化成功（高级账号）")
                    else:
                        # 使用默认API地址
                        self._tushare_pro = ts.pro_api(token)
                        logger.info("✅ Tushare Pro API 初始化成功（标准账号）")
                except Exception as e:
                    logger.warning(f"Tushare Pro 初始化失败: {e}")
        return self._tushare_pro

    def collect(self, trade_date: Optional[str] = None) -> Dict:
        """
        采集昨日涨停股今日表现

        Args:
            trade_date: 今日日期（表现日期），默认最新交易日

        Returns:
            采集结果统计
        """
        if not trade_date:
            trade_date = get_latest_trading_date()

        yesterday = _get_previous_trading_date(trade_date)
        if not yesterday:
            logger.error(f"无法获取 {trade_date} 的前一交易日")
            return {"success": False, "error": "无法获取前一交易日"}

        logger.info(f"开始采集昨日涨停表现: 昨日={yesterday}, 今日={trade_date}")

        # 1. 获取昨日涨停股
        yesterday_limits = self._get_yesterday_limit_stocks(yesterday)
        if not yesterday_limits:
            logger.warning(f"未找到 {yesterday} 的涨停股数据")
            return {"success": False, "error": "未找到昨日涨停股"}

        logger.info(f"昨日涨停股数量: {len(yesterday_limits)}")

        # 2. 获取这些股票今日行情
        stock_codes = [s["stock_code"] for s in yesterday_limits]
        today_quotes = self._get_today_quotes(stock_codes, trade_date)
        logger.info(f"获取到今日行情: {len(today_quotes)} 条")

        # 3. 获取今日涨停/跌停股（用于判断晋级）
        today_limits = self._get_today_limit_stocks(trade_date)

        # 4. 合并数据并计算指标
        records = self._merge_and_calculate(
            yesterday_limits, today_quotes, today_limits, trade_date
        )

        # 5. 写入数据库
        if records:
            self._save_to_db(records, trade_date)

        # 统计结果
        stats = self._calculate_stats(records)
        logger.info(f"采集完成: {stats}")

        return {
            "success": True,
            "trade_date": trade_date,
            "yesterday": yesterday,
            "total_count": len(records),
            "stats": stats
        }

    def _get_yesterday_limit_stocks(self, yesterday: str) -> List[Dict]:
        """从数据库获取昨日涨停股"""
        try:
            result = self.supabase.table("limit_stocks_detail")\
                .select("stock_code, stock_name, continuous_days, is_strong_limit")\
                .eq("trade_date", yesterday)\
                .eq("limit_type", "limit_up")\
                .execute()

            return result.data or []
        except Exception as e:
            logger.error(f"获取昨日涨停股失败: {e}")
            return []

    def _get_today_limit_stocks(self, trade_date: str) -> Dict[str, str]:
        """获取今日涨停/跌停股，返回 {stock_code: limit_type}"""
        try:
            result = self.supabase.table("limit_stocks_detail")\
                .select("stock_code, limit_type")\
                .eq("trade_date", trade_date)\
                .execute()

            return {s["stock_code"]: s["limit_type"] for s in (result.data or [])}
        except Exception as e:
            logger.error(f"获取今日涨停股失败: {e}")
            return {}

    def _get_today_quotes(self, stock_codes: List[str], trade_date: str) -> Dict[str, Dict]:
        """
        获取股票今日行情

        Args:
            stock_codes: 股票代码列表（6位数字）
            trade_date: 交易日期 YYYY-MM-DD

        Returns:
            {stock_code: {open_pct, change_pct, high_pct, low_pct, amount}}
        """
        if not self.tushare_pro or not stock_codes:
            return {}

        result = {}
        trade_date_ts = trade_date.replace("-", "")  # 转为 YYYYMMDD

        # 转换股票代码格式：6位 -> ts格式（000001.SZ）
        ts_codes = []
        code_map = {}  # ts_code -> original_code
        for code in stock_codes:
            if code.startswith("6"):
                ts_code = f"{code}.SH"
            else:
                ts_code = f"{code}.SZ"
            ts_codes.append(ts_code)
            code_map[ts_code] = code

        try:
            # 分批查询（Tushare 限制）
            batch_size = 100
            for i in range(0, len(ts_codes), batch_size):
                batch = ts_codes[i:i + batch_size]
                ts_code_str = ",".join(batch)

                df = self.tushare_pro.daily(
                    ts_code=ts_code_str,
                    trade_date=trade_date_ts,
                    fields="ts_code,open,close,high,low,pre_close,pct_chg,amount"
                )

                if df is not None and not df.empty:
                    for _, row in df.iterrows():
                        ts_code = row["ts_code"]
                        original_code = code_map.get(ts_code)
                        if not original_code:
                            continue

                        pre_close = row["pre_close"]
                        if pre_close and pre_close > 0:
                            open_pct = round((row["open"] - pre_close) / pre_close * 100, 2)
                            high_pct = round((row["high"] - pre_close) / pre_close * 100, 2)
                            low_pct = round((row["low"] - pre_close) / pre_close * 100, 2)
                        else:
                            open_pct = high_pct = low_pct = None

                        result[original_code] = {
                            "open_pct": open_pct,
                            "change_pct": row["pct_chg"],
                            "high_pct": high_pct,
                            "low_pct": low_pct,
                            "amount": row["amount"] * 1000 if row["amount"] else None  # 转为元
                        }

        except Exception as e:
            logger.error(f"获取今日行情失败: {e}")

        return result

    def _merge_and_calculate(
        self,
        yesterday_limits: List[Dict],
        today_quotes: Dict[str, Dict],
        today_limits: Dict[str, str],
        trade_date: str
    ) -> List[Dict]:
        """合并数据并计算指标"""
        records = []

        for stock in yesterday_limits:
            stock_code = stock["stock_code"]
            quote = today_quotes.get(stock_code, {})

            change_pct = quote.get("change_pct")
            limit_type = today_limits.get(stock_code)

            record = {
                "trade_date": trade_date,
                "stock_code": stock_code,
                "stock_name": stock.get("stock_name"),
                "yesterday_continuous_days": stock.get("continuous_days") or 1,
                "yesterday_is_strong_limit": stock.get("is_strong_limit"),
                "today_open_pct": quote.get("open_pct"),
                "today_change_pct": change_pct,
                "today_high_pct": quote.get("high_pct"),
                "today_low_pct": quote.get("low_pct"),
                "today_amount": quote.get("amount"),
                "is_limit_up": limit_type == "limit_up",
                "is_limit_down": limit_type == "limit_down",
                "is_big_loss": change_pct is not None and change_pct <= -5,
                "is_big_high": change_pct is not None and change_pct >= 5 and limit_type != "limit_up"
            }

            records.append(record)

        return records

    def _save_to_db(self, records: List[Dict], trade_date: str):
        """保存到数据库"""
        try:
            # 先删除当日已有数据
            self.supabase.table("yesterday_limit_performance")\
                .delete()\
                .eq("trade_date", trade_date)\
                .execute()

            # 批量插入
            batch_size = 50
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                self.supabase.table("yesterday_limit_performance")\
                    .insert(batch)\
                    .execute()

            logger.info(f"成功写入 {len(records)} 条昨日涨停表现数据")

        except Exception as e:
            logger.error(f"写入数据库失败: {e}")

    def _calculate_stats(self, records: List[Dict]) -> Dict:
        """计算统计数据"""
        if not records:
            return {}

        total = len(records)
        with_quote = [r for r in records if r["today_change_pct"] is not None]

        if not with_quote:
            return {"total": total, "with_quote": 0}

        changes = [r["today_change_pct"] for r in with_quote]
        avg_change = round(sum(changes) / len(changes), 2)

        promotion_count = sum(1 for r in records if r["is_limit_up"])
        big_loss_count = sum(1 for r in records if r["is_big_loss"])

        # 高位（3板+）统计
        high_board = [r for r in records if r["yesterday_continuous_days"] >= 3]
        high_board_big_loss = sum(1 for r in high_board if r["is_big_loss"])

        return {
            "total": total,
            "with_quote": len(with_quote),
            "avg_change_pct": avg_change,
            "promotion_count": promotion_count,
            "promotion_rate": round(promotion_count / total * 100, 1),
            "big_loss_count": big_loss_count,
            "big_loss_rate": round(big_loss_count / total * 100, 1),
            "high_board_count": len(high_board),
            "high_board_big_loss": high_board_big_loss,
            "high_board_big_loss_rate": round(high_board_big_loss / len(high_board) * 100, 1) if high_board else 0
        }


# 便捷函数
def collect_yesterday_limit_performance(trade_date: Optional[str] = None) -> Dict:
    """采集昨日涨停股今日表现"""
    collector = YesterdayLimitCollector()
    return collector.collect(trade_date)


if __name__ == "__main__":
    # 测试
    import sys
    sys.path.insert(0, "/Users/win/Documents/ai 编程/cc/短线复盘/backend")

    from dotenv import load_dotenv
    load_dotenv("/Users/win/Documents/ai 编程/cc/短线复盘/.env")

    result = collect_yesterday_limit_performance("2025-12-11")
    print(result)
