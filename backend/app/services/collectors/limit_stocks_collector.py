"""
涨停池/跌停池数据采集服务
使用 AKShare 采集涨停和跌停个股的详细信息

数据来源:
- stock_zt_pool_em: 涨停股池（真实数据）
- stock_zt_pool_dtgc_em: 跌停股池（真实数据）
包含: 股票代码、名称、涨跌幅、封板时间、连板天数、开板次数、封单金额等
"""

import akshare as ak
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict
from loguru import logger

from app.utils.supabase_client import get_supabase


class LimitStocksCollector:
    """涨停/跌停股池数据采集器"""

    def __init__(self):
        self.supabase = get_supabase()

    def collect_limit_up_stocks(self, date: Optional[str] = None) -> pd.DataFrame:
        """
        采集涨停股池详细数据（真实数据）

        Args:
            date: 日期 YYYYMMDD，默认为今天

        Returns:
            DataFrame with limit-up stocks details
        """
        try:
            date_str = date or datetime.now().strftime("%Y%m%d")
            logger.info(f"采集 {date_str} 涨停股池数据...")

            df = ak.stock_zt_pool_em(date=date_str)

            if df is None or df.empty:
                logger.warning(f"{date_str} 涨停股池数据为空")
                return pd.DataFrame()

            logger.info(f"成功采集涨停股池，共 {len(df)} 只股票")

            # 显示列名以便调试
            logger.debug(f"涨停股池列名: {df.columns.tolist()}")

            return df

        except Exception as e:
            logger.error(f"采集涨停股池失败: {str(e)}")
            return pd.DataFrame()

    def collect_limit_down_stocks(self, date: Optional[str] = None) -> pd.DataFrame:
        """
        采集跌停股池详细数据（真实数据）

        Args:
            date: 日期 YYYYMMDD，默认为今天

        Returns:
            DataFrame with limit-down stocks details
        """
        try:
            date_str = date or datetime.now().strftime("%Y%m%d")
            logger.info(f"采集 {date_str} 跌停股池数据...")

            df = ak.stock_zt_pool_dtgc_em(date=date_str)

            if df is None or df.empty:
                logger.warning(f"{date_str} 跌停股池数据为空")
                return pd.DataFrame()

            logger.info(f"成功采集跌停股池，共 {len(df)} 只股票")

            # 显示列名以便调试
            logger.debug(f"跌停股池列名: {df.columns.tolist()}")

            return df

        except Exception as e:
            logger.error(f"采集跌停股池失败: {str(e)}")
            return pd.DataFrame()

    def process_limit_up_data(self, df: pd.DataFrame, trade_date: str) -> List[Dict]:
        """
        处理涨停股池数据，转换为数据库格式

        Args:
            df: 涨停股池 DataFrame
            trade_date: 交易日期 YYYY-MM-DD

        Returns:
            处理后的记录列表
        """
        if df.empty:
            return []

        records = []

        # 列名映射（处理可能的不同列名）
        column_mapping = {
            "代码": "stock_code",
            "股票代码": "stock_code",
            "名称": "stock_name",
            "股票名称": "stock_name",
            "涨跌幅": "change_pct",
            "最新价": "close_price",
            "现价": "close_price",
            "收盘价": "close_price",
            "换手率": "turnover_rate",
            "成交额": "amount",
            "首次封板时间": "first_limit_time",
            "最后封板时间": "last_limit_time",
            "封板时间": "first_limit_time",
            "连板数": "continuous_days",
            "打开次数": "opening_times",
            "开板次数": "opening_times",
            "封单金额": "sealed_amount",
            "总市值": "market_cap",
            "流通市值": "circulation_market_cap",
        }

        for _, row in df.iterrows():
            try:
                record = {
                    "trade_date": trade_date,
                    "limit_type": "limit_up",
                }

                # 处理各字段
                for ak_col, db_col in column_mapping.items():
                    if ak_col in df.columns:
                        value = row[ak_col]

                        # 处理不同类型的值
                        if pd.isna(value):
                            record[db_col] = None
                        elif db_col in ["stock_code", "stock_name"]:
                            record[db_col] = str(value)
                        elif db_col in ["first_limit_time", "last_limit_time"]:
                            # 时间格式处理
                            if value and value != "-":
                                try:
                                    # 可能的格式: "09:30:00", "09:30", "093000"
                                    time_str = str(value).strip()
                                    if len(time_str) == 6:  # 093000
                                        time_str = f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
                                    elif len(time_str) == 5:  # 09:30
                                        time_str = f"{time_str}:00"
                                    record[db_col] = time_str
                                except:
                                    record[db_col] = None
                            else:
                                record[db_col] = None
                        elif db_col in ["continuous_days", "opening_times"]:
                            try:
                                record[db_col] = int(value) if value and value != "-" else 0
                            except:
                                record[db_col] = 0
                        else:
                            try:
                                record[db_col] = float(value) if value and value != "-" else None
                            except:
                                record[db_col] = None

                # 处理概念字段（如果存在）
                if "所属概念" in df.columns:
                    concepts_str = row["所属概念"]
                    if pd.notna(concepts_str) and concepts_str:
                        # 分割概念（可能用逗号、分号等分隔）
                        concepts = [c.strip() for c in str(concepts_str).replace("；", ",").split(",") if c.strip()]
                        record["concepts"] = concepts[:5]  # 最多保存5个概念
                    else:
                        record["concepts"] = []
                else:
                    record["concepts"] = []

                # 判断是否一字板（开板次数为0）
                record["is_strong_limit"] = (record.get("opening_times", 0) == 0)

                # 必需字段校验
                if "stock_code" in record and "stock_name" in record:
                    records.append(record)

            except Exception as e:
                logger.warning(f"处理涨停股数据失败: {e}, row: {row.to_dict()}")
                continue

        logger.info(f"处理涨停股数据完成，共 {len(records)} 条有效记录")
        return records

    def process_limit_down_data(self, df: pd.DataFrame, trade_date: str) -> List[Dict]:
        """
        处理跌停股池数据，转换为数据库格式

        Args:
            df: 跌停股池 DataFrame
            trade_date: 交易日期 YYYY-MM-DD

        Returns:
            处理后的记录列表
        """
        if df.empty:
            return []

        records = []

        # 列名映射
        column_mapping = {
            "代码": "stock_code",
            "名称": "stock_name",
            "涨跌幅": "change_pct",
            "最新价": "close_price",
            "换手率": "turnover_rate",
            "成交额": "amount",
            "总市值": "market_cap",
            "流通市值": "circulation_market_cap",
        }

        for _, row in df.iterrows():
            try:
                record = {
                    "trade_date": trade_date,
                    "limit_type": "limit_down",
                }

                for ak_col, db_col in column_mapping.items():
                    if ak_col in df.columns:
                        value = row[ak_col]
                        if pd.isna(value):
                            record[db_col] = None
                        elif db_col in ["stock_code", "stock_name"]:
                            record[db_col] = str(value)
                        else:
                            try:
                                record[db_col] = float(value)
                            except:
                                record[db_col] = None

                # 处理概念
                if "所属概念" in df.columns:
                    concepts_str = row["所属概念"]
                    if pd.notna(concepts_str) and concepts_str:
                        concepts = [c.strip() for c in str(concepts_str).replace("；", ",").split(",") if c.strip()]
                        record["concepts"] = concepts[:5]
                    else:
                        record["concepts"] = []
                else:
                    record["concepts"] = []

                if "stock_code" in record and "stock_name" in record:
                    records.append(record)

            except Exception as e:
                logger.warning(f"处理跌停股数据失败: {e}")
                continue

        logger.info(f"处理跌停股数据完成，共 {len(records)} 条有效记录")
        return records

    def save_to_database(self, records: List[Dict]) -> int:
        """
        保存涨跌停股票数据到 Supabase

        Args:
            records: 股票记录列表

        Returns:
            成功保存的记录数
        """
        if not records:
            logger.warning("没有数据需要保存")
            return 0

        try:
            logger.info(f"准备保存 {len(records)} 条涨跌停股票数据...")

            # 批量插入（使用 upsert）
            response = self.supabase.table("limit_stocks_detail").upsert(
                records, on_conflict="trade_date,stock_code,limit_type"
            ).execute()

            logger.info(f"成功保存 {len(records)} 条涨跌停股票数据")
            return len(records)

        except Exception as e:
            logger.error(f"保存涨跌停数据失败: {str(e)}")
            return 0

    def collect_and_save(self, trade_date: Optional[str] = None) -> Dict[str, int]:
        """
        采集并保存涨跌停股池数据

        Args:
            trade_date: 交易日期 YYYY-MM-DD，默认为今天

        Returns:
            {"limit_up": count, "limit_down": count}
        """
        if not trade_date:
            trade_date = datetime.now().strftime("%Y-%m-%d")

        date_akshare = trade_date.replace("-", "")

        logger.info(f"开始采集 {trade_date} 涨跌停股池数据...")

        results = {"limit_up": 0, "limit_down": 0}

        # 1. 采集并处理涨停股池
        limit_up_df = self.collect_limit_up_stocks(date_akshare)
        if not limit_up_df.empty:
            limit_up_records = self.process_limit_up_data(limit_up_df, trade_date)
            results["limit_up"] = self.save_to_database(limit_up_records)

        # 2. 采集并处理跌停股池
        limit_down_df = self.collect_limit_down_stocks(date_akshare)
        if not limit_down_df.empty:
            limit_down_records = self.process_limit_down_data(limit_down_df, trade_date)
            results["limit_down"] = self.save_to_database(limit_down_records)

        logger.info(f"涨跌停数据采集完成: 涨停{results['limit_up']}只, 跌停{results['limit_down']}只")

        return results


# 便捷函数
def collect_limit_stocks(trade_date: Optional[str] = None) -> Dict[str, int]:
    """采集涨跌停股池数据"""
    collector = LimitStocksCollector()
    return collector.collect_and_save(trade_date)
