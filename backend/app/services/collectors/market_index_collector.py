"""
大盘指数数据采集服务
优先使用 Tushare 采集指数数据（更及时），AKShare作为备用
"""

import akshare as ak
import tushare as ts
import pandas as pd
import time
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from loguru import logger

from app.utils.supabase_client import get_supabase


class MarketIndexCollector:
    """大盘指数数据采集器"""

    def __init__(self):
        self.supabase = get_supabase()
        self._tushare_pro = None
        # 指数代码映射
        self.index_mapping = {
            "sh000001": {"code": "SH000001", "name": "上证指数", "ts_code": "000001.SH"},
            "sz399001": {"code": "SZ399001", "name": "深证成指", "ts_code": "399001.SZ"},
            "sz399006": {"code": "SZ399006", "name": "创业板指", "ts_code": "399006.SZ"},
        }

    @property
    def tushare_pro(self):
        """延迟初始化 Tushare Pro API"""
        if self._tushare_pro is None:
            token = os.getenv("TUSHARE_TOKEN")
            if token:
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
                    logger.warning(f"Tushare Pro 初始化失败: {e}")
        return self._tushare_pro

    def collect_index_daily(
        self, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None, max_retries: int = 3
    ) -> pd.DataFrame:
        """
        采集指定指数的日线数据（优先Tushare，备用AKShare）

        Args:
            symbol: 指数代码 (sh000001, sz399001, sz399006)
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            max_retries: 最大重试次数

        Returns:
            DataFrame with columns: trade_date, open_price, high_price, low_price, close_price, volume, amount, change_pct, amplitude
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"开始采集指数 {symbol} 的数据... (尝试 {attempt + 1}/{max_retries})")

                df = pd.DataFrame()

                # 方法1：优先使用Tushare（数据更及时）
                if self.tushare_pro and symbol in self.index_mapping:
                    try:
                        ts_code = self.index_mapping[symbol]["ts_code"]
                        start_ts = start_date.replace("-", "") if start_date else None
                        end_ts = end_date.replace("-", "") if end_date else None

                        logger.debug(f"   尝试从Tushare获取 {ts_code} 数据...")
                        df_ts = self.tushare_pro.index_daily(
                            ts_code=ts_code,
                            start_date=start_ts,
                            end_date=end_ts
                        )

                        if df_ts is not None and not df_ts.empty:
                            # 重命名列
                            df = df_ts.rename(columns={
                                "trade_date": "trade_date_raw",
                                "open": "open_price",
                                "high": "high_price",
                                "low": "low_price",
                                "close": "close_price",
                                "vol": "volume",
                                "amount": "amount",
                                "pct_chg": "change_pct",
                            })

                            # 格式化日期
                            df["trade_date"] = pd.to_datetime(df["trade_date_raw"]).dt.strftime("%Y-%m-%d")
                            df = df.drop("trade_date_raw", axis=1)

                            # 计算振幅
                            df = df.sort_values("trade_date")
                            df["amplitude"] = (
                                (df["high_price"] - df["low_price"]) / df["close_price"].shift(1) * 100
                            )

                            logger.info(f"✅ Tushare 成功采集 {symbol} 数据，共 {len(df)} 条记录")
                    except Exception as e:
                        logger.warning(f"   Tushare获取失败: {e}，尝试备用方案...")

                # 方法2：备用AKShare
                if df.empty:
                    logger.debug(f"   使用AKShare获取 {symbol} 数据...")
                    df_ak = ak.stock_zh_index_daily(symbol=symbol)

                    if df_ak is not None and not df_ak.empty:
                        df = df_ak.rename(columns={
                            "date": "trade_date",
                            "open": "open_price",
                            "high": "high_price",
                            "low": "low_price",
                            "close": "close_price",
                            "volume": "volume",
                        })

                        df["amount"] = None
                        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.strftime("%Y-%m-%d")
                        df["change_pct"] = df["close_price"].pct_change() * 100
                        df["amplitude"] = (
                            (df["high_price"] - df["low_price"]) / df["close_price"].shift(1) * 100
                        )

                        # 过滤日期范围
                        if start_date:
                            df = df[df["trade_date"] >= start_date]
                        if end_date:
                            df = df[df["trade_date"] <= end_date]

                        logger.info(f"✅ AKShare 成功采集 {symbol} 数据，共 {len(df)} 条记录")

                if df.empty:
                    logger.warning(f"指数 {symbol} 没有数据")
                    return pd.DataFrame()

                return df

            except Exception as e:
                logger.warning(f"采集指数 {symbol} 数据失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"采集指数 {symbol} 数据失败，已达最大重试次数")
                    return pd.DataFrame()

        return pd.DataFrame()

    def save_to_database(self, symbol: str, df: pd.DataFrame) -> int:
        """
        保存指数数据到 Supabase

        Args:
            symbol: 指数代码
            df: 数据 DataFrame

        Returns:
            成功保存的记录数
        """
        if df.empty:
            logger.warning(f"没有数据需要保存: {symbol}")
            return 0

        try:
            index_info = self.index_mapping.get(symbol)
            if not index_info:
                logger.error(f"未知的指数代码: {symbol}")
                return 0

            index_code = index_info["code"]
            index_name = index_info["name"]

            # 准备数据
            records = []
            for _, row in df.iterrows():
                record = {
                    "trade_date": row["trade_date"],
                    "index_code": index_code,
                    "index_name": index_name,
                    "open_price": float(row["open_price"]) if pd.notna(row["open_price"]) else None,
                    "high_price": float(row["high_price"]) if pd.notna(row["high_price"]) else None,
                    "low_price": float(row["low_price"]) if pd.notna(row["low_price"]) else None,
                    "close_price": float(row["close_price"]) if pd.notna(row["close_price"]) else None,
                    "volume": int(row["volume"]) if pd.notna(row["volume"]) else None,
                    "amount": float(row["amount"]) if pd.notna(row["amount"]) else None,
                    "change_pct": float(row["change_pct"]) if pd.notna(row["change_pct"]) else None,
                    "amplitude": float(row["amplitude"]) if pd.notna(row["amplitude"]) else None,
                }
                records.append(record)

            # 批量插入/更新数据（使用 upsert）
            logger.info(f"准备保存 {len(records)} 条 {index_name} 数据...")

            response = self.supabase.table("market_index").upsert(
                records, on_conflict="trade_date,index_code"
            ).execute()

            logger.info(f"成功保存 {index_name} 数据: {len(records)} 条")
            return len(records)

        except Exception as e:
            logger.error(f"保存数据到数据库失败: {str(e)}")
            return 0

    def collect_all_indexes(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> Dict[str, int]:
        """
        采集所有指数数据

        Args:
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD

        Returns:
            各指数保存的记录数
        """
        results = {}

        # 如果没有指定日期，默认采集最近 30 天
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        for i, symbol in enumerate(self.index_mapping.keys()):
            try:
                # 在每个请求之间添加延迟，避免频繁请求
                if i > 0:
                    time.sleep(2)

                # 采集数据
                df = self.collect_index_daily(symbol, start_date, end_date)

                # 保存到数据库
                count = self.save_to_database(symbol, df)
                results[symbol] = count

            except Exception as e:
                logger.error(f"处理指数 {symbol} 失败: {str(e)}")
                results[symbol] = 0

        return results

    def get_latest_trade_date(self, index_code: str) -> Optional[str]:
        """
        获取数据库中最新的交易日期

        Args:
            index_code: 指数代码 (SH000001, SZ399001, SZ399006)

        Returns:
            最新交易日期 YYYY-MM-DD，如果没有数据返回 None
        """
        try:
            response = (
                self.supabase.table("market_index")
                .select("trade_date")
                .eq("index_code", index_code)
                .order("trade_date", desc=True)
                .limit(1)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]["trade_date"]
            return None

        except Exception as e:
            logger.error(f"获取最新交易日期失败: {str(e)}")
            return None

    def collect_incremental(self) -> Dict[str, int]:
        """
        增量采集：只采集数据库中没有的数据

        Returns:
            各指数新增的记录数
        """
        results = {}
        end_date = datetime.now().strftime("%Y-%m-%d")

        for symbol, info in self.index_mapping.items():
            try:
                index_code = info["code"]

                # 获取最新日期
                latest_date = self.get_latest_trade_date(index_code)

                if latest_date:
                    # 从最新日期的下一天开始采集
                    start_date = (
                        datetime.strptime(latest_date, "%Y-%m-%d") + timedelta(days=1)
                    ).strftime("%Y-%m-%d")
                    logger.info(f"{info['name']} 最新日期: {latest_date}，从 {start_date} 开始增量采集")
                else:
                    # 如果没有数据，采集最近 30 天
                    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                    logger.info(f"{info['name']} 没有历史数据，从 {start_date} 开始采集")

                # 采集并保存
                df = self.collect_index_daily(symbol, start_date, end_date)
                count = self.save_to_database(symbol, df)
                results[symbol] = count

            except Exception as e:
                logger.error(f"增量采集指数 {symbol} 失败: {str(e)}")
                results[symbol] = 0

        return results


# 便捷函数
def collect_market_indexes(
    start_date: Optional[str] = None, end_date: Optional[str] = None
) -> Dict[str, int]:
    """采集大盘指数数据"""
    collector = MarketIndexCollector()
    return collector.collect_all_indexes(start_date, end_date)


def collect_market_indexes_incremental() -> Dict[str, int]:
    """增量采集大盘指数数据"""
    collector = MarketIndexCollector()
    return collector.collect_incremental()
