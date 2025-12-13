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
        采集指定指数的日线数据（使用pro_bar接口，包含MA均线数据）

        Args:
            symbol: 指数代码 (sh000001, sz399001, sz399006)
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            max_retries: 最大重试次数

        Returns:
            DataFrame with columns: trade_date, open_price, high_price, low_price, close_price, volume, amount, change_pct, amplitude, ma5, ma10, ma20
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"开始采集指数 {symbol} 的数据... (尝试 {attempt + 1}/{max_retries})")

                df = pd.DataFrame()

                # 方法1：优先使用Tushare pro_bar（支持均线数据）
                if self.tushare_pro and symbol in self.index_mapping:
                    try:
                        ts_code = self.index_mapping[symbol]["ts_code"]
                        start_ts = start_date.replace("-", "") if start_date else None
                        end_ts = end_date.replace("-", "") if end_date else None

                        logger.debug(f"   尝试从Tushare pro_bar获取 {ts_code} 数据（含均线）...")

                        # 使用pro_bar接口，支持ma参数获取均线
                        df_ts = ts.pro_bar(
                            ts_code=ts_code,
                            api=self.tushare_pro,
                            start_date=start_ts,
                            end_date=end_ts,
                            asset='I',  # I=指数
                            ma=[5, 10, 20]  # 获取5/10/20日均线
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

                            # 排序（pro_bar返回的是倒序）
                            df = df.sort_values("trade_date")

                            # 计算振幅
                            df["amplitude"] = (
                                (df["high_price"] - df["low_price"]) / df["close_price"].shift(1) * 100
                            )

                            logger.info(f"✅ Tushare pro_bar 成功采集 {symbol} 数据（含均线），共 {len(df)} 条记录")
                    except Exception as e:
                        logger.warning(f"   Tushare pro_bar获取失败: {e}，尝试备用方案...")

                # 方法2：备用 - 使用index_daily（不含均线，需要自己计算）
                if df.empty and self.tushare_pro and symbol in self.index_mapping:
                    try:
                        ts_code = self.index_mapping[symbol]["ts_code"]
                        start_ts = start_date.replace("-", "") if start_date else None
                        end_ts = end_date.replace("-", "") if end_date else None

                        logger.debug(f"   尝试从Tushare index_daily获取 {ts_code} 数据...")
                        df_ts = self.tushare_pro.index_daily(
                            ts_code=ts_code,
                            start_date=start_ts,
                            end_date=end_ts
                        )

                        if df_ts is not None and not df_ts.empty:
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

                            df["trade_date"] = pd.to_datetime(df["trade_date_raw"]).dt.strftime("%Y-%m-%d")
                            df = df.drop("trade_date_raw", axis=1)
                            df = df.sort_values("trade_date")

                            # 计算振幅
                            df["amplitude"] = (
                                (df["high_price"] - df["low_price"]) / df["close_price"].shift(1) * 100
                            )

                            # 自行计算均线
                            df["ma5"] = df["close_price"].rolling(window=5).mean()
                            df["ma10"] = df["close_price"].rolling(window=10).mean()
                            df["ma20"] = df["close_price"].rolling(window=20).mean()

                            logger.info(f"✅ Tushare index_daily 成功采集 {symbol} 数据，共 {len(df)} 条记录")
                    except Exception as e:
                        logger.warning(f"   Tushare index_daily获取失败: {e}，尝试AKShare...")

                # 方法3：备用AKShare（需要自己计算均线）
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

                        # 自行计算均线
                        df["ma5"] = df["close_price"].rolling(window=5).mean()
                        df["ma10"] = df["close_price"].rolling(window=10).mean()
                        df["ma20"] = df["close_price"].rolling(window=20).mean()

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

    def _calculate_trend_analysis(self, df: pd.DataFrame, index: int) -> dict:
        """
        计算单条记录的走势分析

        Args:
            df: 完整的数据DataFrame
            index: 当前记录的索引位置

        Returns:
            包含走势分析字段的字典
        """
        row = df.iloc[index]

        # 获取基本数据
        close_price = row["close_price"]
        ma5 = row.get("ma5")
        ma10 = row.get("ma10")
        ma20 = row.get("ma20")

        # 初始化返回值
        result = {
            "trend": None,
            "ma5_position": None,
            "ma10_position": None,
            "ma20_position": None,
            "change_5d": None,
        }

        # 判断价格与均线位置关系
        def compare_price_ma(price, ma_value):
            """比较价格与均线,返回 above/below/equal"""
            if ma_value is None or pd.isna(ma_value):
                return None
            if price > ma_value:
                return "above"
            elif price < ma_value:
                return "below"
            else:
                return "equal"

        result["ma5_position"] = compare_price_ma(close_price, ma5)
        result["ma10_position"] = compare_price_ma(close_price, ma10)
        result["ma20_position"] = compare_price_ma(close_price, ma20)

        # 计算5日涨跌幅
        if index >= 5:
            price_5days_ago = df.iloc[index - 5]["close_price"]
            if pd.notna(price_5days_ago) and price_5days_ago != 0:
                result["change_5d"] = round(((close_price - price_5days_ago) / price_5days_ago) * 100, 2)

        # 判断走势
        if ma5 is not None and ma10 is not None and not pd.isna(ma5) and not pd.isna(ma10):
            change_5d = result["change_5d"] or 0

            # 上涨判断: 价格 > MA5 > MA10 且 5日涨幅 > 2%
            if close_price > ma5 and ma5 > ma10 and change_5d > 2:
                result["trend"] = "上涨"
            # 下跌判断: 价格 < MA5 < MA10 且 5日跌幅 > 2%
            elif close_price < ma5 and ma5 < ma10 and change_5d < -2:
                result["trend"] = "下跌"
            # 其他情况为震荡
            else:
                result["trend"] = "震荡"

        return result

    def save_to_database(self, symbol: str, df: pd.DataFrame) -> int:
        """
        保存指数数据到 Supabase（含走势分析）

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
            for idx, row in df.iterrows():
                # 计算走势分析
                trend_analysis = self._calculate_trend_analysis(df, df.index.get_loc(idx))

                record = {
                    "trade_date": row["trade_date"],
                    "index_code": index_code,
                    "index_name": index_name,
                    "open_price": float(row["open_price"]) if pd.notna(row["open_price"]) else None,
                    "high_price": float(row["high_price"]) if pd.notna(row["high_price"]) else None,
                    "low_price": float(row["low_price"]) if pd.notna(row["low_price"]) else None,
                    "close_price": float(row["close_price"]) if pd.notna(row["close_price"]) else None,
                    "volume": int(row["volume"]) if pd.notna(row["volume"]) else None,
                    # Tushare的amount单位是千元，需要乘以1000转换为元
                    "amount": float(row["amount"]) * 1000 if pd.notna(row["amount"]) else None,
                    "change_pct": float(row["change_pct"]) if pd.notna(row["change_pct"]) else None,
                    "amplitude": float(row["amplitude"]) if pd.notna(row["amplitude"]) else None,
                    "ma5": round(float(row["ma5"]), 2) if "ma5" in row and pd.notna(row["ma5"]) else None,
                    "ma10": round(float(row["ma10"]), 2) if "ma10" in row and pd.notna(row["ma10"]) else None,
                    "ma20": round(float(row["ma20"]), 2) if "ma20" in row and pd.notna(row["ma20"]) else None,
                    # 新增：走势分析字段
                    "trend": trend_analysis["trend"],
                    "ma5_position": trend_analysis["ma5_position"],
                    "ma10_position": trend_analysis["ma10_position"],
                    "ma20_position": trend_analysis["ma20_position"],
                    "change_5d": trend_analysis["change_5d"],
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

    def _check_trend_analysis_incomplete(self, index_code: str, trade_date: str) -> bool:
        """
        检查指定日期的走势分析字段是否不完整

        Args:
            index_code: 指数代码
            trade_date: 交易日期

        Returns:
            True 如果走势分析字段为空或不完整，需要修复
        """
        try:
            response = (
                self.supabase.table("market_index")
                .select("trend,ma5_position,ma10_position,ma20_position,change_5d")
                .eq("index_code", index_code)
                .eq("trade_date", trade_date)
                .execute()
            )

            if not response.data:
                return False

            data = response.data[0]
            # 检查关键字段是否为空
            if (data.get("trend") is None or
                data.get("ma5_position") is None or
                data.get("change_5d") is None):
                return True

            return False

        except Exception as e:
            logger.error(f"检查走势分析字段失败: {str(e)}")
            return False

    def collect_incremental(self) -> Dict[str, int]:
        """
        增量采集：只采集数据库中没有的数据
        为了正确计算MA均线和走势分析，会请求更多历史数据，但只保存新数据

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

                # 检查最新数据的走势分析字段是否完整
                needs_repair = False
                if latest_date:
                    needs_repair = self._check_trend_analysis_incomplete(index_code, latest_date)
                    if needs_repair:
                        logger.warning(f"{info['name']} 最新数据({latest_date})走势分析字段不完整，需要修复")

                if latest_date and not needs_repair:
                    # 正常增量采集：实际需要保存的起始日期（最新日期的下一天）
                    actual_start_date = (
                        datetime.strptime(latest_date, "%Y-%m-%d") + timedelta(days=1)
                    ).strftime("%Y-%m-%d")
                    # 为了计算MA20和5日涨跌幅，需要请求更多历史数据（往前推25天）
                    fetch_start_date = (
                        datetime.strptime(latest_date, "%Y-%m-%d") - timedelta(days=25)
                    ).strftime("%Y-%m-%d")
                    logger.info(f"{info['name']} 最新日期: {latest_date}，从 {actual_start_date} 开始增量采集")
                elif latest_date and needs_repair:
                    # 修复模式：重新采集最新日期的数据
                    actual_start_date = latest_date
                    fetch_start_date = (
                        datetime.strptime(latest_date, "%Y-%m-%d") - timedelta(days=25)
                    ).strftime("%Y-%m-%d")
                    logger.info(f"{info['name']} 修复模式：重新采集 {latest_date} 及之后的数据")
                else:
                    # 如果没有数据，采集最近 30 天
                    actual_start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                    fetch_start_date = actual_start_date
                    logger.info(f"{info['name']} 没有历史数据，从 {actual_start_date} 开始采集")

                # 采集数据（包含额外的历史数据用于计算MA）
                df = self.collect_index_daily(symbol, fetch_start_date, end_date)

                if not df.empty:
                    # 只保存新数据（>= actual_start_date）
                    df_to_save = df[df["trade_date"] >= actual_start_date].copy()
                    if not df_to_save.empty:
                        # 重新计算走势分析，使用完整的df作为上下文
                        count = self._save_with_full_context(symbol, df, df_to_save)
                        results[symbol] = count
                    else:
                        logger.info(f"{info['name']} 没有新数据需要保存")
                        results[symbol] = 0
                else:
                    results[symbol] = 0

            except Exception as e:
                logger.error(f"增量采集指数 {symbol} 失败: {str(e)}")
                results[symbol] = 0

        return results

    def _save_with_full_context(self, symbol: str, full_df: pd.DataFrame, df_to_save: pd.DataFrame) -> int:
        """
        使用完整的历史数据上下文保存新数据

        Args:
            symbol: 指数代码
            full_df: 包含历史数据的完整DataFrame（用于计算走势分析）
            df_to_save: 需要保存的新数据DataFrame

        Returns:
            成功保存的记录数
        """
        if df_to_save.empty:
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
            for idx, row in df_to_save.iterrows():
                # 使用完整df计算走势分析（找到当前行在full_df中的位置）
                full_idx = full_df.index.get_loc(idx)
                trend_analysis = self._calculate_trend_analysis(full_df, full_idx)

                record = {
                    "trade_date": row["trade_date"],
                    "index_code": index_code,
                    "index_name": index_name,
                    "open_price": float(row["open_price"]) if pd.notna(row["open_price"]) else None,
                    "high_price": float(row["high_price"]) if pd.notna(row["high_price"]) else None,
                    "low_price": float(row["low_price"]) if pd.notna(row["low_price"]) else None,
                    "close_price": float(row["close_price"]) if pd.notna(row["close_price"]) else None,
                    "volume": int(row["volume"]) if pd.notna(row["volume"]) else None,
                    # Tushare的amount单位是千元，需要乘以1000转换为元
                    "amount": float(row["amount"]) * 1000 if pd.notna(row["amount"]) else None,
                    "change_pct": float(row["change_pct"]) if pd.notna(row["change_pct"]) else None,
                    "amplitude": float(row["amplitude"]) if pd.notna(row["amplitude"]) else None,
                    "ma5": round(float(row["ma5"]), 2) if "ma5" in row and pd.notna(row["ma5"]) else None,
                    "ma10": round(float(row["ma10"]), 2) if "ma10" in row and pd.notna(row["ma10"]) else None,
                    "ma20": round(float(row["ma20"]), 2) if "ma20" in row and pd.notna(row["ma20"]) else None,
                    # 走势分析字段
                    "trend": trend_analysis["trend"],
                    "ma5_position": trend_analysis["ma5_position"],
                    "ma10_position": trend_analysis["ma10_position"],
                    "ma20_position": trend_analysis["ma20_position"],
                    "change_5d": trend_analysis["change_5d"],
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
