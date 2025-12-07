"""
市场情绪数据采集服务
使用 AKShare 采集市场情绪相关数据：涨跌比、涨停数、连板分布、炸板率等

数据来源:
- stock_zh_a_spot_em: A股实时行情数据（用于统计涨跌家数）
- stock_zt_pool_em: 涨停股池数据（真实涨停数据）
- stock_zt_pool_dtgc_em: 跌停股池数据
- stock_zt_pool_previous_em: 昨日涨停股池（用于计算连板）
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from loguru import logger
import json

from app.utils.supabase_client import get_supabase


class MarketSentimentCollector:
    """市场情绪数据采集器"""

    def __init__(self):
        self.supabase = get_supabase()

    def collect_stock_spot_data(self) -> pd.DataFrame:
        """
        采集 A 股实时行情数据（用于统计涨跌家数）

        Returns:
            DataFrame with all A-share stocks realtime data
        """
        try:
            logger.info("采集 A 股实时行情数据...")
            df = ak.stock_zh_a_spot_em()

            if df is None or df.empty:
                logger.warning("A 股实时行情数据为空")
                return pd.DataFrame()

            logger.info(f"成功采集 A 股实时行情，共 {len(df)} 只股票")
            return df

        except Exception as e:
            logger.error(f"采集 A 股实时行情失败: {str(e)}")
            return pd.DataFrame()

    def collect_limit_up_pool(self, date: Optional[str] = None) -> pd.DataFrame:
        """
        采集涨停股池数据（真实数据）

        Args:
            date: 日期 YYYYMMDD，默认为今天

        Returns:
            DataFrame with limit-up stocks
        """
        try:
            logger.info("采集涨停股池数据...")

            # 使用东方财富涨停股池接口（实时数据）
            df = ak.stock_zt_pool_em(date=date or datetime.now().strftime("%Y%m%d"))

            if df is None or df.empty:
                logger.warning("涨停股池数据为空")
                return pd.DataFrame()

            logger.info(f"成功采集涨停股池，共 {len(df)} 只涨停股")
            return df

        except Exception as e:
            logger.error(f"采集涨停股池失败: {str(e)}")
            return pd.DataFrame()

    def collect_limit_down_pool(self, date: Optional[str] = None) -> pd.DataFrame:
        """
        采集跌停股池数据（真实数据）

        Args:
            date: 日期 YYYYMMDD，默认为今天

        Returns:
            DataFrame with limit-down stocks
        """
        try:
            logger.info("采集跌停股池数据...")

            # 使用东方财富跌停股池接口
            df = ak.stock_zt_pool_dtgc_em(date=date or datetime.now().strftime("%Y%m%d"))

            if df is None or df.empty:
                logger.warning("跌停股池数据为空")
                return pd.DataFrame()

            logger.info(f"成功采集跌停股池，共 {len(df)} 只跌停股")
            return df

        except Exception as e:
            logger.error(f"采集跌停股池失败: {str(e)}")
            return pd.DataFrame()

    def collect_continuous_limit_up(self, date: Optional[str] = None) -> pd.DataFrame:
        """
        采集连板股数据（真实数据）

        Args:
            date: 日期 YYYYMMDD

        Returns:
            DataFrame with continuous limit-up stocks
        """
        try:
            logger.info("采集连板股数据...")

            # 使用昨日涨停股池（包含连板天数信息）
            df = ak.stock_zt_pool_previous_em(date=date or datetime.now().strftime("%Y%m%d"))

            if df is None or df.empty:
                logger.warning("连板股数据为空")
                return pd.DataFrame()

            logger.info(f"成功采集连板股数据，共 {len(df)} 只")
            return df

        except Exception as e:
            logger.error(f"采集连板股数据失败: {str(e)}")
            return pd.DataFrame()

    def calculate_continuous_distribution(self, limit_up_df: pd.DataFrame) -> Dict[str, int]:
        """
        计算连板分布（基于真实数据）

        Args:
            limit_up_df: 涨停股池数据（包含连板天数）

        Returns:
            连板分布字典 {"1": count, "2": count, "3": count, "4+": count}
        """
        try:
            if limit_up_df.empty:
                return {"1": 0, "2": 0, "3": 0, "4+": 0}

            # 检查是否有连板天数字段
            continuous_col = None
            for col in ['连板数', '几板', '连板天数', '涨停统计']:
                if col in limit_up_df.columns:
                    continuous_col = col
                    break

            if not continuous_col:
                # 如果没有连板字段，默认都是首板
                return {"1": len(limit_up_df), "2": 0, "3": 0, "4+": 0}

            # 统计连板分布
            distribution = {"1": 0, "2": 0, "3": 0, "4+": 0}

            for value in limit_up_df[continuous_col]:
                try:
                    # 处理可能的字符串格式
                    if isinstance(value, str):
                        # 提取数字
                        import re
                        match = re.search(r'\d+', value)
                        if match:
                            days = int(match.group())
                        else:
                            days = 1
                    else:
                        days = int(value)

                    if days == 1:
                        distribution["1"] += 1
                    elif days == 2:
                        distribution["2"] += 1
                    elif days == 3:
                        distribution["3"] += 1
                    else:
                        distribution["4+"] += 1

                except:
                    distribution["1"] += 1

            logger.info(f"连板分布: {distribution}")
            return distribution

        except Exception as e:
            logger.error(f"计算连板分布失败: {str(e)}")
            return {"1": 0, "2": 0, "3": 0, "4+": 0}

    def calculate_explosion_rate(self, limit_up_df: pd.DataFrame) -> tuple:
        """
        计算炸板率（基于真实数据）

        Args:
            limit_up_df: 涨停股池数据（包含开板次数）

        Returns:
            (炸板数, 炸板率)
        """
        try:
            if limit_up_df.empty:
                return 0, 0.0

            # 查找开板次数字段
            open_times_col = None
            for col in ['打开次数', '开板次数', '炸板次数']:
                if col in limit_up_df.columns:
                    open_times_col = col
                    break

            if not open_times_col:
                # 如果没有开板次数字段，返回0
                logger.warning("涨停数据中没有找到开板次数字段，炸板率设为0")
                return 0, 0.0

            # 统计炸板股（开板次数 > 0）
            exploded_count = (limit_up_df[open_times_col] > 0).sum()
            total_count = len(limit_up_df)

            explosion_rate = (exploded_count / total_count * 100) if total_count > 0 else 0.0

            logger.info(f"炸板统计: {exploded_count}/{total_count} = {explosion_rate:.2f}%")
            return exploded_count, explosion_rate

        except Exception as e:
            logger.error(f"计算炸板率失败: {str(e)}")
            return 0, 0.0

    def collect_market_sentiment(self, trade_date: Optional[str] = None) -> Dict:
        """
        采集完整的市场情绪数据

        Args:
            trade_date: 交易日期 YYYY-MM-DD，默认为今天

        Returns:
            市场情绪数据字典
        """
        if not trade_date:
            trade_date = datetime.now().strftime("%Y-%m-%d")

        date_akshare = trade_date.replace("-", "")

        logger.info(f"开始采集 {trade_date} 市场情绪数据...")

        # 1. 采集实时行情（统计涨跌家数）
        spot_df = self.collect_stock_spot_data()

        # 2. 采集涨停股池
        limit_up_df = self.collect_limit_up_pool(date_akshare)

        # 3. 采集跌停股池
        limit_down_df = self.collect_limit_down_pool(date_akshare)

        # 4. 统计涨跌家数
        up_count = 0
        down_count = 0
        flat_count = 0
        total_amount = 0.0

        if not spot_df.empty and '涨跌幅' in spot_df.columns:
            up_count = (spot_df['涨跌幅'] > 0).sum()
            down_count = (spot_df['涨跌幅'] < 0).sum()
            flat_count = (spot_df['涨跌幅'] == 0).sum()

            # 统计总成交额
            if '成交额' in spot_df.columns:
                total_amount = spot_df['成交额'].sum()

        # 计算涨跌比
        up_down_ratio = (up_count / down_count) if down_count > 0 else 0.0

        # 5. 统计涨跌停数量
        limit_up_count = len(limit_up_df)
        limit_down_count = len(limit_down_df)

        # 6. 计算连板分布
        continuous_distribution = self.calculate_continuous_distribution(limit_up_df)

        # 7. 计算炸板率
        exploded_count, explosion_rate = self.calculate_explosion_rate(limit_up_df)

        sentiment_data = {
            "trade_date": trade_date,
            "total_amount": total_amount,
            "up_count": up_count,
            "down_count": down_count,
            "flat_count": flat_count,
            "up_down_ratio": round(up_down_ratio, 4),
            "limit_up_count": limit_up_count,
            "limit_down_count": limit_down_count,
            "continuous_limit_distribution": continuous_distribution,
            "exploded_count": exploded_count,
            "explosion_rate": round(explosion_rate, 4),
        }

        logger.info(f"市场情绪数据采集完成: 涨{up_count}/跌{down_count}, 涨停{limit_up_count}/跌停{limit_down_count}, 炸板率{explosion_rate:.2f}%")

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
            }

            logger.info(f"保存市场情绪数据: {sentiment_data['trade_date']}")

            # 使用 upsert 避免重复
            response = self.supabase.table("market_sentiment").upsert(
                record, on_conflict="trade_date"
            ).execute()

            logger.info(f"成功保存市场情绪数据")
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
