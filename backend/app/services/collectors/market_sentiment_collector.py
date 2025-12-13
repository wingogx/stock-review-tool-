"""
市场情绪数据采集服务
使用 Tushare Pro 采集市场情绪相关数据：涨跌比、涨停数、连板分布、炸板率等

数据来源:
- daily: 每日行情（统计涨跌家数、总成交额）✅ Tushare
- limit_list_d: 涨跌停列表（涨停、跌停、炸板、连板统计）✅ Tushare
"""

import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from loguru import logger
import json
import os

from app.utils.supabase_client import get_supabase
from app.utils.trading_date import get_latest_trading_date


class MarketSentimentCollector:
    """市场情绪数据采集器（基于Tushare）"""

    def __init__(self):
        self.supabase = get_supabase()
        self._tushare_pro = None

    @property
    def tushare_pro(self):
        """延迟初始化 Tushare Pro API"""
        if self._tushare_pro is None:
            token = os.getenv("TUSHARE_TOKEN")
            if not token:
                raise ValueError("TUSHARE_TOKEN 未配置")

            try:
                http_url = os.getenv("TUSHARE_HTTP_URL")
                if http_url:
                    self._tushare_pro = ts.pro_api()
                    self._tushare_pro._DataApi__token = token
                    self._tushare_pro._DataApi__http_url = http_url
                    logger.debug(f"✅ Tushare Pro API 初始化成功（高级账号）")
                else:
                    self._tushare_pro = ts.pro_api(token)
                    logger.debug("✅ Tushare Pro API 初始化成功（标准账号）")
            except Exception as e:
                logger.error(f"Tushare Pro 初始化失败: {e}")
                raise
        return self._tushare_pro

    def collect_market_stats(self, trade_date: str) -> Dict:
        """
        采集市场统计数据（涨跌家数、总成交额）
        使用 Tushare daily 接口

        Args:
            trade_date: 交易日期 YYYYMMDD

        Returns:
            市场统计数据字典 {up_count, down_count, flat_count, total_amount}
        """
        try:
            logger.info(f"采集市场统计数据 {trade_date}...")

            df = self.tushare_pro.daily(trade_date=trade_date)

            if df is None or df.empty:
                logger.warning(f"市场统计数据为空: {trade_date}")
                return {}

            # 统计涨跌家数
            up_count = len(df[df['pct_chg'] > 0])
            down_count = len(df[df['pct_chg'] < 0])
            flat_count = len(df[df['pct_chg'] == 0])

            # 计算总成交额（Tushare的amount单位是千元）
            total_amount = float(df['amount'].sum()) * 1000  # 千元 -> 元

            logger.info(f"✅ 市场统计: 上涨{up_count}, 下跌{down_count}, 平盘{flat_count}, 成交额{total_amount/1e8:.2f}亿")

            return {
                'up_count': up_count,
                'down_count': down_count,
                'flat_count': flat_count,
                'total_amount': total_amount,
            }

        except Exception as e:
            logger.error(f"采集市场统计数据失败: {str(e)}")
            return {}

    def collect_limit_data(self, trade_date: str) -> Dict:
        """
        采集涨跌停数据（涨停、跌停、炸板、连板分布）
        使用 Tushare limit_list_d 接口

        Args:
            trade_date: 交易日期 YYYYMMDD

        Returns:
            涨跌停数据字典
        """
        try:
            logger.info(f"采集涨跌停数据 {trade_date}...")

            df = self.tushare_pro.limit_list_d(trade_date=trade_date)

            if df is None or df.empty:
                logger.warning(f"涨跌停数据为空: {trade_date}")
                return {
                    'limit_up_count': 0,
                    'limit_down_count': 0,
                    'exploded_count': 0,
                    'continuous_limit_distribution': {},
                }

            # 统计涨停、跌停、炸板
            # limit字段: U=涨停, D=跌停, Z=炸板
            limit_up_count = len(df[df['limit'] == 'U'])
            limit_down_count = len(df[df['limit'] == 'D'])
            exploded_count = len(df[df['limit'] == 'Z'])

            # 计算连板分布（只统计涨停股票）
            limit_up_df = df[df['limit'] == 'U']
            continuous_distribution = self._calculate_continuous_distribution(limit_up_df)

            logger.info(f"✅ 涨跌停统计: 涨停{limit_up_count}, 跌停{limit_down_count}, 炸板{exploded_count}")
            logger.info(f"   连板分布: {continuous_distribution}")

            return {
                'limit_up_count': limit_up_count,
                'limit_down_count': limit_down_count,
                'exploded_count': exploded_count,
                'continuous_limit_distribution': continuous_distribution,
            }

        except Exception as e:
            logger.error(f"采集涨跌停数据失败: {str(e)}")
            return {
                'limit_up_count': 0,
                'limit_down_count': 0,
                'exploded_count': 0,
                'continuous_limit_distribution': {},
            }

    def _calculate_continuous_distribution(self, limit_up_df: pd.DataFrame) -> Dict[str, int]:
        """
        计算连板分布（基于Tushare的limit_times字段）

        Args:
            limit_up_df: 涨停股票数据

        Returns:
            连板分布字典 {"1": count, "2": count, ...}
        """
        if limit_up_df.empty:
            return {"1": 0}

        distribution = {}

        # 使用limit_times字段（连板天数）
        if 'limit_times' in limit_up_df.columns:
            for times in limit_up_df['limit_times']:
                if pd.notna(times):
                    days = int(times)
                    key = str(days)
                    distribution[key] = distribution.get(key, 0) + 1
                else:
                    # 如果没有连板天数，默认为首板
                    distribution["1"] = distribution.get("1", 0) + 1
        else:
            # 如果没有limit_times字段，全部算作首板
            distribution["1"] = len(limit_up_df)

        return distribution

    def collect_market_sentiment(self, trade_date: Optional[str] = None) -> Dict:
        """
        采集完整的市场情绪数据

        Args:
            trade_date: 交易日期 YYYY-MM-DD，默认为最近交易日

        Returns:
            市场情绪数据字典
        """
        if not trade_date:
            trade_date = get_latest_trading_date()

        date_ts = trade_date.replace("-", "")

        logger.info(f"开始采集 {trade_date} 市场情绪数据（Tushare）...")

        # 1. 采集市场统计数据（涨跌家数、总成交额）
        market_stats = self.collect_market_stats(date_ts)

        # 2. 采集涨跌停数据（涨停、跌停、炸板、连板分布）
        limit_data = self.collect_limit_data(date_ts)

        # 3. 计算涨跌比
        up_count = market_stats.get('up_count', 0)
        down_count = market_stats.get('down_count', 0)
        up_down_ratio = (up_count / down_count) if down_count > 0 else 0.0

        # 4. 计算炸板率（通用口径：炸板数 / 触及涨停总数）
        limit_up_count = limit_data.get('limit_up_count', 0)
        exploded_count = limit_data.get('exploded_count', 0)
        total_touched = limit_up_count + exploded_count
        explosion_rate = (exploded_count / total_touched * 100) if total_touched > 0 else 0.0

        # 5. 计算市场状态（基于上涨股票占比）
        total_stocks = up_count + down_count
        up_pct = (up_count / total_stocks * 100) if total_stocks > 0 else 0

        if up_pct >= 60:
            market_status = "强势"
        elif up_pct < 40:
            market_status = "弱势"
        else:
            market_status = "震荡"

        sentiment_data = {
            "trade_date": trade_date,
            "total_amount": market_stats.get('total_amount', 0),
            "up_count": up_count,
            "down_count": down_count,
            "flat_count": market_stats.get('flat_count', 0),
            "up_down_ratio": round(up_down_ratio, 4),
            "limit_up_count": limit_up_count,
            "limit_down_count": limit_data.get('limit_down_count', 0),
            "continuous_limit_distribution": limit_data.get('continuous_limit_distribution', {}),
            "exploded_count": exploded_count,
            "explosion_rate": round(explosion_rate, 4),
            "market_status": market_status,
        }

        logger.info(
            f"市场情绪数据采集完成: 涨{up_count}/跌{down_count}, "
            f"涨停{limit_up_count}/跌停{limit_data.get('limit_down_count', 0)}, "
            f"总成交额{market_stats.get('total_amount', 0)/1e8:.2f}亿, "
            f"炸板率{explosion_rate:.2f}%"
        )

        return sentiment_data

    def save_to_database(self, sentiment_data: Dict) -> bool:
        """
        保存市场情绪数据到 Supabase

        Args:
            sentiment_data: 市场情绪数据

        Returns:
            是否保存成功
        """
        try:
            # 转换连板分布为 JSON
            record = {
                "trade_date": sentiment_data["trade_date"],
                "total_amount": float(sentiment_data["total_amount"]),
                "up_count": int(sentiment_data["up_count"]),
                "down_count": int(sentiment_data["down_count"]),
                "flat_count": int(sentiment_data.get("flat_count", 0)),
                "up_down_ratio": float(sentiment_data["up_down_ratio"]),
                "limit_up_count": int(sentiment_data["limit_up_count"]),
                "limit_down_count": int(sentiment_data["limit_down_count"]),
                "continuous_limit_distribution": json.dumps(sentiment_data["continuous_limit_distribution"]),
                "exploded_count": int(sentiment_data.get("exploded_count", 0)),
                "explosion_rate": float(sentiment_data["explosion_rate"]),
                "market_status": sentiment_data["market_status"],
            }

            logger.info(f"保存市场情绪数据: {sentiment_data['trade_date']}")

            # 使用 upsert 避免重复
            response = self.supabase.table("market_sentiment").upsert(
                record, on_conflict="trade_date"
            ).execute()

            logger.info(f"✅ 成功保存市场情绪数据")
            return True

        except Exception as e:
            logger.error(f"保存市场情绪数据失败: {str(e)}")
            return False

    def collect_and_save(self, trade_date: Optional[str] = None) -> bool:
        """
        采集并保存市场情绪数据

        Args:
            trade_date: 交易日期 YYYY-MM-DD

        Returns:
            是否成功
        """
        sentiment_data = self.collect_market_sentiment(trade_date)
        return self.save_to_database(sentiment_data)


# 便捷函数
def collect_market_sentiment(trade_date: Optional[str] = None) -> Dict:
    """采集市场情绪数据"""
    collector = MarketSentimentCollector()
    return collector.collect_market_sentiment(trade_date)


def collect_and_save_market_sentiment(trade_date: Optional[str] = None) -> bool:
    """采集并保存市场情绪数据"""
    collector = MarketSentimentCollector()
    return collector.collect_and_save(trade_date)
