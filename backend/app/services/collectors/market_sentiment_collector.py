"""
市场情绪数据采集服务
使用 AKShare 采集市场情绪相关数据：涨跌比、涨停数、连板分布、炸板率等

数据来源:
- stock_market_activity_legu: 乐咕乐股-市场异动（用于统计涨跌家数）✅ 稳定
- stock_sse_deal_daily: 上交所-每日概览（用于统计上交所成交额）✅ 稳定
- stock_szse_summary: 深交所-市场总貌（用于统计深交所成交额）✅ 稳定
- stock_zt_pool_em: 涨停股池数据（真实涨停数据）
- stock_zt_pool_dtgc_em: 跌停股池数据
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from loguru import logger
import json

from app.utils.supabase_client import get_supabase
from app.utils.trading_date import get_latest_trading_date


class MarketSentimentCollector:
    """市场情绪数据采集器"""

    def __init__(self):
        self.supabase = get_supabase()

    def collect_market_activity_data(self) -> Dict:
        """
        采集市场异动数据（用于统计涨跌家数）
        使用乐咕乐股-市场异动接口（稳定可靠）

        Returns:
            市场异动数据字典
        """
        try:
            logger.info("采集市场异动数据...")
            df = ak.stock_market_activity_legu()

            if df is None or df.empty:
                logger.warning("市场异动数据为空")
                return {}

            # 将数据转换为字典
            data_dict = dict(zip(df['item'], df['value']))

            logger.info(f"成功采集市场异动数据: 上涨{data_dict.get('上涨', 0)}, 下跌{data_dict.get('下跌', 0)}")
            return data_dict

        except Exception as e:
            logger.error(f"采集市场异动数据失败: {str(e)}")
            return {}

    def collect_total_amount(self, date: str) -> float:
        """
        采集两市总成交额（上交所 + 深交所）

        Args:
            date: 日期 YYYYMMDD

        Returns:
            总成交额（元）
        """
        try:
            total_amount = 0.0

            # 1. 获取上交所成交额
            try:
                sse_df = ak.stock_sse_deal_daily(date=date)
                if not sse_df.empty:
                    amount_row = sse_df[sse_df['单日情况'] == '成交金额']
                    if not amount_row.empty:
                        sse_amount_yi = float(amount_row['股票'].iloc[0])
                        sse_amount = sse_amount_yi * 1e8  # 转换为元
                        total_amount += sse_amount
                        logger.debug(f"上交所成交额: {sse_amount_yi:.2f} 亿元")
            except Exception as e:
                logger.warning(f"获取上交所成交额失败: {e}")

            # 2. 获取深交所成交额
            try:
                szse_df = ak.stock_szse_summary(date=date)
                if not szse_df.empty:
                    stock_row = szse_df[szse_df['证券类别'] == '股票']
                    if not stock_row.empty:
                        szse_amount = float(stock_row['成交金额'].iloc[0])  # 单位：元
                        total_amount += szse_amount
                        logger.debug(f"深交所成交额: {szse_amount / 1e8:.2f} 亿元")
            except Exception as e:
                logger.warning(f"获取深交所成交额失败: {e}")

            if total_amount > 0:
                logger.info(f"两市总成交额: {total_amount / 1e8:.2f} 亿元")
            else:
                logger.warning("未能获取两市成交额数据")

            return total_amount

        except Exception as e:
            logger.error(f"采集两市总成交额失败: {str(e)}")
            return 0.0

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
            trade_date: 交易日期 YYYY-MM-DD，默认为最近交易日

        Returns:
            市场情绪数据字典
        """
        if not trade_date:
            trade_date = get_latest_trading_date()  # 使用最近交易日而不是系统当前日期

        date_akshare = trade_date.replace("-", "")

        logger.info(f"开始采集 {trade_date} 市场情绪数据...")

        # 1. 采集市场异动数据（涨跌家数）
        market_activity = self.collect_market_activity_data()

        # 2. 采集两市总成交额
        total_amount = self.collect_total_amount(date_akshare)

        # 3. 采集涨停股池
        limit_up_df = self.collect_limit_up_pool(date_akshare)

        # 4. 采集跌停股池
        limit_down_df = self.collect_limit_down_pool(date_akshare)

        # 5. 从市场异动数据中提取涨跌家数
        up_count = int(market_activity.get('上涨', 0))
        down_count = int(market_activity.get('下跌', 0))
        flat_count = int(market_activity.get('平盘', 0))

        # 计算涨跌比
        up_down_ratio = (up_count / down_count) if down_count > 0 else 0.0

        # 6. 统计涨跌停数量
        limit_up_count = len(limit_up_df)
        limit_down_count = len(limit_down_df)

        # 7. 计算连板分布
        continuous_distribution = self.calculate_continuous_distribution(limit_up_df)

        # 8. 计算炸板率
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

        logger.info(f"市场情绪数据采集完成: 涨{up_count}/跌{down_count}, 涨停{limit_up_count}/跌停{limit_down_count}, 总成交额{total_amount/1e8:.2f}亿, 炸板率{explosion_rate:.2f}%")

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
