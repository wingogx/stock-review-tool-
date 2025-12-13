"""
涨停池/跌停池数据采集服务
优先使用 Tushare limit_list_ths 采集涨停和跌停个股的详细信息

数据来源:
- limit_list_ths: Tushare涨停池（高级账号，10000积分）
- stock_zt_pool_em: AKShare涨停股池（备用）
- stock_zt_pool_dtgc_em: AKShare跌停股池（备用）
- stock_individual_fund_flow: 个股资金流向（主力/散户净流入）
包含: 股票代码、名称、涨跌幅、封板时间、连板天数、开板次数、封单金额、概念板块等
"""

import akshare as ak
import pandas as pd
import tushare as ts
from datetime import datetime
from typing import Optional, List, Dict
from loguru import logger
import time
import os

from app.utils.supabase_client import get_supabase
from app.utils.trading_date import get_latest_trading_date, get_previous_trading_date
from app.services.collectors.ths_concept_collector import ThsConceptCollector


class LimitStocksCollector:
    """涨停/跌停股池数据采集器"""

    def __init__(self):
        self.supabase = get_supabase()
        self._fund_flow_cache = {}  # 缓存资金流向数据
        self._concept_cache = {}  # 缓存股票概念数据
        self._tushare_pro = None  # Tushare Pro API实例

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
                        # 手动设置token和http_url
                        self._tushare_pro._DataApi__token = token
                        self._tushare_pro._DataApi__http_url = http_url
                        logger.info(f"✅ Tushare Pro API 初始化成功（高级账号）: {http_url}")
                    else:
                        # 使用默认API地址
                        self._tushare_pro = ts.pro_api(token)
                        logger.info("✅ Tushare Pro API 初始化成功（标准账号）")
                except Exception as e:
                    logger.warning(f"Tushare Pro 初始化失败: {e}")

        return self._tushare_pro

    def get_fund_flow_data(self, stock_code: str, trade_date: str) -> Dict:
        """
        获取个股资金流向数据

        Args:
            stock_code: 股票代码（6位数字）
            trade_date: 交易日期 YYYY-MM-DD

        Returns:
            包含主力净流入和散户净流入的字典
        """
        cache_key = f"{stock_code}_{trade_date}"
        if cache_key in self._fund_flow_cache:
            return self._fund_flow_cache[cache_key]

        result = {
            "main_net_inflow": None,
            "main_net_inflow_pct": None,
        }

        try:
            # 判断市场：6开头为上海，0/3开头为深圳
            if stock_code.startswith("6"):
                market = "sh"
            else:
                market = "sz"

            df = ak.stock_individual_fund_flow(stock=stock_code, market=market)

            if df is not None and not df.empty:
                df["日期"] = pd.to_datetime(df["日期"])
                row = df[df["日期"] == trade_date]

                if not row.empty:
                    r = row.iloc[0]
                    result["main_net_inflow"] = float(r["主力净流入-净额"]) if pd.notna(r["主力净流入-净额"]) else None
                    result["main_net_inflow_pct"] = float(r["主力净流入-净占比"]) if pd.notna(r["主力净流入-净占比"]) else None

        except Exception as e:
            logger.warning(f"获取 {stock_code} 资金流向失败: {e}")

        self._fund_flow_cache[cache_key] = result
        return result

    def get_stock_concepts(self, ts_code: str) -> List[str]:
        """
        获取股票所属的概念板块（使用Tushare concept_detail接口）

        Args:
            ts_code: 股票代码（带交易所后缀，如 000035.SZ）

        Returns:
            概念板块名称列表
        """
        # 缓存检查
        if ts_code in self._concept_cache:
            return self._concept_cache[ts_code]

        concepts = []

        try:
            if self.tushare_pro:
                time.sleep(0.1)  # 避免频率限制
                df = self.tushare_pro.concept_detail(ts_code=ts_code)

                if df is not None and not df.empty:
                    concepts = df['concept_name'].tolist()
                    logger.debug(f"   {ts_code} 获取到 {len(concepts)} 个概念")
                else:
                    logger.debug(f"   {ts_code} 无概念数据")
            else:
                logger.debug("   Tushare Pro API 未初始化，无法获取概念")

        except Exception as e:
            logger.debug(f"   获取 {ts_code} 概念失败: {e}")

        # 缓存结果
        self._concept_cache[ts_code] = concepts
        return concepts

    def collect_limit_up_stocks(self, date: Optional[str] = None) -> pd.DataFrame:
        """
        采集涨停股池详细数据（优先使用Tushare）

        Args:
            date: 日期 YYYYMMDD，默认为今天

        Returns:
            DataFrame with limit-up stocks details
        """
        date_str = date or datetime.now().strftime("%Y%m%d")
        logger.info(f"采集 {date_str} 涨停股池数据...")

        # 方法1: 优先从 Tushare limit_list_d 获取（更稳定，包含连板数据）
        if self.tushare_pro:
            try:
                logger.info("   尝试从 Tushare limit_list_d 获取涨停池数据...")
                time.sleep(0.3)  # 避免频率限制

                df = self.tushare_pro.limit_list_d(
                    trade_date=date_str,
                    limit_type='U'
                )

                if df is not None and not df.empty:
                    logger.info(f"✅ Tushare 成功采集涨停股池，共 {len(df)} 只股票")
                    logger.debug(f"   Tushare涨停池列名: {df.columns.tolist()}")
                    return df
                else:
                    logger.warning("   Tushare 涨停池数据为空，尝试备用方案...")
            except Exception as e:
                logger.warning(f"   Tushare 采集涨停池失败: {e}，尝试备用方案...")

        # 方法2: 从 AKShare 获取（备用方案）
        try:
            logger.info("   尝试从 AKShare 获取涨停股池数据...")
            df = ak.stock_zt_pool_em(date=date_str)

            if df is None or df.empty:
                logger.warning(f"{date_str} AKShare涨停股池数据为空")
                return pd.DataFrame()

            logger.info(f"✅ AKShare 成功采集涨停股池，共 {len(df)} 只股票")
            logger.debug(f"   AKShare涨停池列名: {df.columns.tolist()}")

            return df

        except Exception as e:
            logger.error(f"❌ AKShare 采集涨停股池失败: {str(e)}")
            return pd.DataFrame()

    def collect_limit_down_stocks(self, date: Optional[str] = None) -> pd.DataFrame:
        """
        采集跌停股池详细数据（优先使用Tushare）

        Args:
            date: 日期 YYYYMMDD，默认为今天

        Returns:
            DataFrame with limit-down stocks details
        """
        date_str = date or datetime.now().strftime("%Y%m%d")
        logger.info(f"采集 {date_str} 跌停股池数据...")

        # 方法1: 优先从 Tushare limit_list_d 获取（更稳定，包含连板数据）
        if self.tushare_pro:
            try:
                logger.info("   尝试从 Tushare limit_list_d 获取跌停池数据...")
                time.sleep(0.3)  # 避免频率限制

                df = self.tushare_pro.limit_list_d(
                    trade_date=date_str,
                    limit_type='D'
                )

                if df is not None and not df.empty:
                    logger.info(f"✅ Tushare 成功采集跌停股池，共 {len(df)} 只股票")
                    logger.debug(f"   Tushare跌停池列名: {df.columns.tolist()}")
                    return df
                else:
                    logger.warning("   Tushare 跌停池数据为空，尝试备用方案...")
            except Exception as e:
                logger.warning(f"   Tushare 采集跌停池失败: {e}，尝试备用方案...")

        # 方法2: 从 AKShare 获取（备用方案）
        try:
            logger.info("   尝试从 AKShare 获取跌停股池数据...")
            df = ak.stock_zt_pool_dtgc_em(date=date_str)

            if df is None or df.empty:
                logger.warning(f"{date_str} AKShare跌停股池数据为空")
                return pd.DataFrame()

            logger.info(f"✅ AKShare 成功采集跌停股池，共 {len(df)} 只股票")
            logger.debug(f"   AKShare跌停池列名: {df.columns.tolist()}")

            return df

        except Exception as e:
            logger.error(f"❌ AKShare 采集跌停股池失败: {str(e)}")
            return pd.DataFrame()

    def process_limit_up_data(self, df: pd.DataFrame, trade_date: str) -> List[Dict]:
        """
        处理涨停股池数据，转换为数据库格式（支持Tushare和AKShare）

        Args:
            df: 涨停股池 DataFrame
            trade_date: 交易日期 YYYY-MM-DD

        Returns:
            处理后的记录列表
        """
        if df.empty:
            return []

        records = []

        # 检测数据来源（Tushare vs AKShare）
        is_tushare = 'ts_code' in df.columns

        # 列名映射（处理Tushare和AKShare的不同列名）
        if is_tushare:
            # Tushare limit_list_d 列名映射
            column_mapping = {
                "ts_code": "stock_code",
                "name": "stock_name",
                "pct_chg": "change_pct",
                "close": "close_price",
                # "trade_date": 不映射，使用参数传入的trade_date
                "fd_amount": "sealed_amount",
                "first_time": "first_limit_time",
                "last_time": "last_limit_time",
                "open_times": "opening_times",
                "up_stat": "limit_stats",  # 涨停统计，格式 "1/1" (当前连板/历史最大连板)
                "limit_times": "continuous_days",  # 连板数
                "lu_desc": "lu_desc",  # 涨停原因/概念板块
                "amount": "amount",
                "total_mv": "market_cap",
                "float_mv": "circulation_market_cap",  # 流通市值
                "turnover_ratio": "turnover_rate",  # 换手率
                "industry": "industry",  # 所属行业
            }
            logger.debug("   使用Tushare列名映射处理数据")
        else:
            # AKShare 列名映射
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
                "炸板次数": "opening_times",
                "封单金额": "sealed_amount",
                "封板资金": "sealed_amount",
                "总市值": "market_cap",
                "流通市值": "circulation_market_cap",
                "涨停统计": "limit_stats",
                "所属行业": "industry",
                "所属概念": "concepts_str",  # AKShare的概念字段
            }
            logger.debug("   使用AKShare列名映射处理数据")

        for _, row in df.iterrows():
            try:
                # 获取股票名称，检查是否为ST股票
                stock_name = None
                if "name" in df.columns:  # Tushare
                    stock_name = str(row["name"])
                elif "名称" in df.columns:  # AKShare
                    stock_name = str(row["名称"])
                elif "股票名称" in df.columns:  # AKShare
                    stock_name = str(row["股票名称"])

                # 排除ST股票（包括ST、*ST、S*ST等）
                if stock_name and ("ST" in stock_name.upper()):
                    logger.debug(f"   跳过ST股票: {stock_name}")
                    continue

                record = {
                    "trade_date": trade_date,
                    "limit_type": "limit_up",
                }

                # 处理各字段
                for source_col, db_col in column_mapping.items():
                    if source_col in df.columns:
                        value = row[source_col]

                        # 处理不同类型的值
                        if pd.isna(value):
                            record[db_col] = None
                        elif db_col == "stock_code":
                            # 处理股票代码
                            if is_tushare:
                                # Tushare: 去除交易所后缀 (000001.SZ -> 000001)
                                code_str = str(value).split('.')[0]
                                record[db_col] = code_str
                            else:
                                # AKShare: 直接使用6位代码
                                record[db_col] = str(value)
                        elif db_col == "lu_desc":
                            # Tushare专有：涨停原因/概念板块描述
                            record[db_col] = str(value) if value else None
                        elif db_col in ["stock_name", "limit_stats", "industry", "concepts_str"]:
                            record[db_col] = str(value)
                        elif db_col in ["first_limit_time", "last_limit_time"]:
                            # 时间格式处理
                            if value and value != "-":
                                try:
                                    # 可能的格式: "09:30:00", "09:30", "093000", "94539" (5位数字HMMSS)
                                    time_str = str(value).strip()

                                    # 检查是否已经是标准格式 HH:MM:SS
                                    if ':' in time_str and len(time_str.split(':')) == 3:
                                        # 验证时间合法性
                                        parts = time_str.split(':')
                                        hour = int(parts[0])
                                        minute = int(parts[1])
                                        second = int(parts[2])
                                        if 0 <= hour < 24 and 0 <= minute < 60 and 0 <= second < 60:
                                            record[db_col] = time_str
                                        else:
                                            record[db_col] = None
                                    elif len(time_str) == 6 and time_str.isdigit():  # 093000 (HHMMSS)
                                        hour = int(time_str[:2])
                                        minute = int(time_str[2:4])
                                        second = int(time_str[4:6])
                                        if 0 <= hour < 24 and 0 <= minute < 60 and 0 <= second < 60:
                                            record[db_col] = f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
                                        else:
                                            record[db_col] = None
                                    elif len(time_str) == 5 and time_str.isdigit():  # 94539 (HMMSS，9点45分39秒)
                                        hour = int(time_str[0])  # 单个数字，如9
                                        minute = int(time_str[1:3])
                                        second = int(time_str[3:5])
                                        if 0 <= hour < 24 and 0 <= minute < 60 and 0 <= second < 60:
                                            record[db_col] = f"{hour:02d}:{minute:02d}:{second:02d}"
                                        else:
                                            record[db_col] = None
                                    elif len(time_str) == 5 and ':' in time_str:  # 09:30
                                        hour = int(time_str[:2])
                                        minute = int(time_str[3:5])
                                        if 0 <= hour < 24 and 0 <= minute < 60:
                                            record[db_col] = f"{time_str}:00"
                                        else:
                                            record[db_col] = None
                                    else:
                                        # 无法识别的格式，设为None
                                        logger.debug(f"   无效时间格式: {value}")
                                        record[db_col] = None
                                except Exception as e:
                                    logger.debug(f"   解析时间 {db_col} 失败: {value}, 错误: {e}")
                                    record[db_col] = None
                            else:
                                record[db_col] = None
                        elif db_col in ["continuous_days", "opening_times"]:
                            try:
                                if value and value != "-":
                                    # 处理 up_stat 字段格式 "1/1" (当前连板/历史最大连板)
                                    if isinstance(value, str) and '/' in value:
                                        record[db_col] = int(value.split('/')[0])
                                    else:
                                        record[db_col] = int(value)
                                else:
                                    record[db_col] = 0
                            except Exception as e:
                                logger.debug(f"   解析 {db_col} 失败: {value}, 错误: {e}")
                                record[db_col] = 0
                        else:
                            try:
                                record[db_col] = float(value) if value and value != "-" else None
                            except:
                                record[db_col] = None

                # 处理概念字段（Tushare的lu_desc或AKShare的所属概念）
                concepts = []
                if is_tushare and "lu_desc" in record and record["lu_desc"]:
                    # Tushare: 解析 lu_desc 字段（格式："概念1+概念2+概念3"）
                    lu_desc = record["lu_desc"]
                    concepts = [c.strip() for c in lu_desc.split('+') if c.strip()]
                    logger.debug(f"   Tushare解析概念: {concepts}")
                elif is_tushare and "ts_code" in df.columns:
                    # Tushare: 如果没有lu_desc字段，使用concept_detail接口获取概念
                    ts_code = row["ts_code"]
                    concepts = self.get_stock_concepts(ts_code)
                elif "concepts_str" in record and record["concepts_str"]:
                    # AKShare: 解析"所属概念"字段（格式："概念1,概念2"或"概念1；概念2"）
                    concepts_str = record["concepts_str"]
                    concepts = [c.strip() for c in str(concepts_str).replace("；", ",").split(",") if c.strip()]
                    logger.debug(f"   AKShare解析概念: {concepts}")

                # 保存概念数组（最多5个）
                record["concepts"] = concepts[:5]

                # 清理中间字段（lu_desc和concepts_str不保存到数据库）
                record.pop("lu_desc", None)
                record.pop("concepts_str", None)

                # 判断是否一字板：炸板次数为0 且 首次封板时间 <= 09:30:00
                opening_times = record.get("opening_times")
                first_limit_time = record.get("first_limit_time")

                # 一字板条件：
                # 1. 炸板次数为0（从未开板）
                # 2. 首次封板时间在 09:30:00 及之前（集合竞价或开盘瞬间涨停）
                is_no_open = (opening_times is not None and opening_times == 0)
                is_early_limit = False
                if first_limit_time:
                    try:
                        # 时间格式可能是 "09:25:00", "09:30:00" 等
                        time_str = str(first_limit_time).strip()
                        is_early_limit = (time_str <= "09:30:00")
                    except:
                        is_early_limit = False

                record["is_strong_limit"] = (is_no_open and is_early_limit)

                # 必需字段校验
                if "stock_code" in record and "stock_name" in record:
                    records.append(record)

            except Exception as e:
                logger.warning(f"处理涨停股数据失败: {e}, row: {row.to_dict()}")
                continue

        # 批量获取资金流向数据
        logger.info(f"开始获取 {len(records)} 只涨停股的资金流向数据...")
        for i, record in enumerate(records):
            try:
                fund_flow = self.get_fund_flow_data(record["stock_code"], trade_date)
                record.update(fund_flow)
                # 每获取10只股票休息一下，避免请求过快
                if (i + 1) % 10 == 0:
                    logger.info(f"已获取 {i + 1}/{len(records)} 只股票的资金流向")
                    time.sleep(0.5)
            except Exception as e:
                logger.warning(f"获取 {record['stock_code']} 资金流向失败: {e}")

        # 补全同花顺概念数据
        logger.info("开始补全同花顺概念数据...")
        try:
            ths_collector = ThsConceptCollector()
            stock_codes = [r["stock_code"] for r in records]
            ths_concepts_map = ths_collector.get_stocks_concepts_batch(stock_codes)

            supplement_count = 0
            for record in records:
                stock_code = record["stock_code"]
                ths_concepts = ths_concepts_map.get(stock_code, [])

                if ths_concepts:
                    # 合并概念（去重）
                    existing_concepts = record.get("concepts") or []
                    merged_concepts = list(set(existing_concepts + ths_concepts))
                    record["concepts"] = merged_concepts
                    supplement_count += 1

            logger.info(f"✅ 成功为 {supplement_count}/{len(records)} 只股票补全同花顺概念")
        except Exception as e:
            logger.warning(f"补全同花顺概念失败: {e}")

        logger.info(f"处理涨停股数据完成，共 {len(records)} 条有效记录")
        return records

    def process_limit_down_data(self, df: pd.DataFrame, trade_date: str) -> List[Dict]:
        """
        处理跌停股池数据，转换为数据库格式（支持Tushare和AKShare）

        Args:
            df: 跌停股池 DataFrame
            trade_date: 交易日期 YYYY-MM-DD

        Returns:
            处理后的记录列表
        """
        if df.empty:
            return []

        records = []

        # 检测数据来源（Tushare vs AKShare）
        is_tushare = 'ts_code' in df.columns

        # 列名映射（处理Tushare和AKShare的不同列名）
        if is_tushare:
            # Tushare limit_list_ths 列名映射
            column_mapping = {
                "ts_code": "stock_code",
                "name": "stock_name",
                "pct_chg": "change_pct",
                "close": "close_price",
                # "trade_date": 不映射，使用参数传入的trade_date
                "amount": "amount",
                "total_mv": "market_cap",
                "circ_mv": "circulation_market_cap",
                "lu_desc": "lu_desc",  # 跌停原因/概念板块
            }
            logger.debug("   使用Tushare列名映射处理跌停数据")
        else:
            # AKShare 列名映射
            column_mapping = {
                "代码": "stock_code",
                "名称": "stock_name",
                "涨跌幅": "change_pct",
                "最新价": "close_price",
                "换手率": "turnover_rate",
                "成交额": "amount",
                "总市值": "market_cap",
                "流通市值": "circulation_market_cap",
                "所属概念": "concepts_str",
            }
            logger.debug("   使用AKShare列名映射处理跌停数据")

        for _, row in df.iterrows():
            try:
                # 获取股票名称，检查是否为ST股票
                stock_name = None
                if "name" in df.columns:  # Tushare
                    stock_name = str(row["name"])
                elif "名称" in df.columns:  # AKShare
                    stock_name = str(row["名称"])

                # 排除ST股票（包括ST、*ST、S*ST等）
                if stock_name and ("ST" in stock_name.upper()):
                    logger.debug(f"   跳过ST股票: {stock_name}")
                    continue

                record = {
                    "trade_date": trade_date,
                    "limit_type": "limit_down",
                }

                for source_col, db_col in column_mapping.items():
                    if source_col in df.columns:
                        value = row[source_col]
                        if pd.isna(value):
                            record[db_col] = None
                        elif db_col == "stock_code":
                            # 处理股票代码
                            if is_tushare:
                                # Tushare: 去除交易所后缀
                                code_str = str(value).split('.')[0]
                                record[db_col] = code_str
                            else:
                                # AKShare: 直接使用
                                record[db_col] = str(value)
                        elif db_col == "lu_desc":
                            # Tushare专有：跌停原因/概念板块描述
                            record[db_col] = str(value) if value else None
                        elif db_col in ["stock_name", "concepts_str"]:
                            record[db_col] = str(value)
                        else:
                            try:
                                record[db_col] = float(value)
                            except:
                                record[db_col] = None

                # 处理概念字段（Tushare的lu_desc或AKShare的所属概念）
                concepts = []
                if is_tushare and "lu_desc" in record and record["lu_desc"]:
                    # Tushare: 解析 lu_desc 字段
                    lu_desc = record["lu_desc"]
                    concepts = [c.strip() for c in lu_desc.split('+') if c.strip()]
                    logger.debug(f"   Tushare解析跌停概念: {concepts}")
                elif "concepts_str" in record and record["concepts_str"]:
                    # AKShare: 解析"所属概念"字段
                    concepts_str = record["concepts_str"]
                    concepts = [c.strip() for c in str(concepts_str).replace("；", ",").split(",") if c.strip()]
                    logger.debug(f"   AKShare解析跌停概念: {concepts}")

                # 保存概念数组（最多5个）
                record["concepts"] = concepts[:5]

                # 清理中间字段
                record.pop("lu_desc", None)
                record.pop("concepts_str", None)

                if "stock_code" in record and "stock_name" in record:
                    records.append(record)

            except Exception as e:
                logger.warning(f"处理跌停股数据失败: {e}")
                continue

        # 批量获取资金流向数据
        logger.info(f"开始获取 {len(records)} 只跌停股的资金流向数据...")
        for i, record in enumerate(records):
            try:
                fund_flow = self.get_fund_flow_data(record["stock_code"], trade_date)
                record.update(fund_flow)
                if (i + 1) % 10 == 0:
                    logger.info(f"已获取 {i + 1}/{len(records)} 只股票的资金流向")
                    time.sleep(0.5)
            except Exception as e:
                logger.warning(f"获取 {record['stock_code']} 资金流向失败: {e}")

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

    def _get_previous_day_limit_up_stocks(self, previous_date: str) -> List[Dict]:
        """
        从数据库查询前一交易日涨停的股票列表

        Args:
            previous_date: 前一交易日期 YYYY-MM-DD

        Returns:
            股票列表 [{"stock_code": "000001", "stock_name": "平安银行"}, ...]
        """
        try:
            response = self.supabase.table("limit_stocks_detail")\
                .select("stock_code, stock_name")\
                .eq("trade_date", previous_date)\
                .eq("limit_type", "limit_up")\
                .execute()

            stocks = response.data
            logger.info(f"查询到 {previous_date} 涨停股票 {len(stocks)} 只")
            return stocks

        except Exception as e:
            logger.error(f"查询前一交易日涨停股票失败: {e}")
            return []

    def _collect_stocks_daily_data(self, stock_codes: List[str], trade_date: str) -> pd.DataFrame:
        """
        使用Tushare批量获取股票的日线数据

        Args:
            stock_codes: 股票代码列表（6位数字）
            trade_date: 交易日期 YYYY-MM-DD

        Returns:
            DataFrame 包含所有股票的日线数据
        """
        if not self.tushare_pro:
            logger.warning("Tushare Pro API 未初始化，无法获取日线数据")
            return pd.DataFrame()

        all_data = []
        ts_date = trade_date.replace('-', '')  # YYYY-MM-DD -> YYYYMMDD

        logger.info(f"开始获取 {len(stock_codes)} 只股票的 {trade_date} 日线数据...")

        for i, stock_code in enumerate(stock_codes):
            try:
                # 转换股票代码格式：XXXXXX -> XXXXXX.SH/SZ
                if stock_code.startswith(('6', '900')):
                    ts_code = f"{stock_code}.SH"
                elif stock_code.startswith(('0', '2', '3')):
                    ts_code = f"{stock_code}.SZ"
                elif stock_code.startswith(('8', '4')):
                    ts_code = f"{stock_code}.BJ"
                else:
                    ts_code = f"{stock_code}.SH"

                # 调用Tushare API
                time.sleep(0.05)  # 避免频率限制
                df = self.tushare_pro.daily(
                    ts_code=ts_code,
                    start_date=ts_date,
                    end_date=ts_date
                )

                if df is not None and not df.empty:
                    all_data.append(df)
                else:
                    logger.debug(f"  {stock_code} 无数据（可能停牌）")

                # 每20只股票输出进度
                if (i + 1) % 20 == 0:
                    logger.info(f"  已获取 {i + 1}/{len(stock_codes)} 只股票")

            except Exception as e:
                logger.warning(f"获取 {stock_code} 日线数据失败: {e}")
                continue

        if all_data:
            result_df = pd.concat(all_data, ignore_index=True)
            logger.info(f"✅ 成功获取 {len(result_df)} 只股票的日线数据")
            return result_df
        else:
            logger.warning("未获取到任何日线数据")
            return pd.DataFrame()

    def _process_daily_data(
        self,
        df: pd.DataFrame,
        trade_date: str,
        stock_name_map: Dict[str, str]
    ) -> List[Dict]:
        """
        处理日线数据，转换为数据库格式

        Args:
            df: Tushare日线数据 DataFrame
            trade_date: 交易日期 YYYY-MM-DD
            stock_name_map: 股票代码->名称映射 {"000001": "平安银行"}

        Returns:
            处理后的记录列表
        """
        if df.empty:
            return []

        records = []

        for _, row in df.iterrows():
            try:
                # 提取股票代码（去除交易所后缀）
                ts_code = row['ts_code']
                stock_code = ts_code.split('.')[0]
                stock_name = stock_name_map.get(stock_code, "未知")

                # 检查是否为ST股票
                if "ST" in stock_name.upper():
                    logger.debug(f"   跳过ST股票: {stock_name}")
                    continue

                # 涨跌幅
                change_pct = row['pct_chg']

                # 判断涨跌停类型
                limit_type = None
                if change_pct >= 9.9:
                    limit_type = "limit_up"
                elif change_pct <= -9.9:
                    limit_type = "limit_down"
                else:
                    limit_type = "normal"  # 正常涨跌

                record = {
                    "trade_date": trade_date,
                    "stock_code": stock_code,
                    "stock_name": stock_name,
                    "limit_type": limit_type,
                    "change_pct": change_pct,
                    "close_price": row['close'],
                    "amount": row['amount'] * 1000 if pd.notna(row['amount']) else None,  # 金额单位转换（千元->元）
                    "turnover_rate": row.get('turnover_rate'),
                    "market_cap": row.get('total_mv') * 10000 if pd.notna(row.get('total_mv')) else None,  # 万元->元
                    "circulation_market_cap": row.get('circ_mv') * 10000 if pd.notna(row.get('circ_mv')) else None,
                }

                records.append(record)

            except Exception as e:
                logger.warning(f"处理日线数据失败: {e}, row: {row.to_dict()}")
                continue

        # 批量获取资金流向数据
        logger.info(f"开始获取 {len(records)} 只股票的资金流向数据...")
        for i, record in enumerate(records):
            try:
                fund_flow = self.get_fund_flow_data(record["stock_code"], trade_date)
                record.update(fund_flow)
                if (i + 1) % 10 == 0:
                    logger.info(f"已获取 {i + 1}/{len(records)} 只股票的资金流向")
                    time.sleep(0.5)
            except Exception as e:
                logger.warning(f"获取 {record['stock_code']} 资金流向失败: {e}")

        # 补全同花顺概念数据
        logger.info("开始补全同花顺概念数据...")
        try:
            ths_collector = ThsConceptCollector()
            stock_codes = [r["stock_code"] for r in records]
            ths_concepts_map = ths_collector.get_stocks_concepts_batch(stock_codes)

            for record in records:
                stock_code = record["stock_code"]
                concepts = ths_concepts_map.get(stock_code, [])
                record["concepts"] = concepts[:5]  # 最多保存5个概念

        except Exception as e:
            logger.warning(f"补全同花顺概念失败: {e}")
            # 如果失败，给所有记录设置空概念
            for record in records:
                record["concepts"] = []

        logger.info(f"处理日线数据完成，共 {len(records)} 条有效记录")
        return records

    def collect_and_save(self, trade_date: Optional[str] = None) -> Dict[str, int]:
        """
        采集并保存涨跌停股池数据

        Args:
            trade_date: 交易日期 YYYY-MM-DD，默认为最近交易日

        Returns:
            {"limit_up": count, "limit_down": count, "yesterday_limit_performance": count}
        """
        if not trade_date:
            trade_date = get_latest_trading_date()  # 使用最近交易日而不是系统当前日期

        date_akshare = trade_date.replace("-", "")

        logger.info(f"开始采集 {trade_date} 涨跌停股池数据...")

        results = {"limit_up": 0, "limit_down": 0, "yesterday_limit_performance": 0}

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

        # 3. 【新增】采集前一交易日涨停股票的今日表现
        logger.info(f"开始采集前一交易日涨停股票的今日表现...")
        previous_date = get_previous_trading_date(trade_date)

        if previous_date:
            logger.info(f"前一交易日: {previous_date}")

            # 3.1 查询前一交易日涨停的股票列表
            yesterday_stocks = self._get_previous_day_limit_up_stocks(previous_date)

            if yesterday_stocks:
                # 3.2 获取这些股票今日的日线数据
                stock_codes = [s["stock_code"] for s in yesterday_stocks]
                stock_name_map = {s["stock_code"]: s["stock_name"] for s in yesterday_stocks}

                daily_df = self._collect_stocks_daily_data(stock_codes, trade_date)

                # 3.3 处理并保存数据
                if not daily_df.empty:
                    performance_records = self._process_daily_data(daily_df, trade_date, stock_name_map)

                    # 过滤掉已经在今日涨停/跌停池中的股票（避免重复）
                    existing_codes = set()
                    if not limit_up_df.empty:
                        if 'ts_code' in limit_up_df.columns:
                            existing_codes.update(limit_up_df['ts_code'].str.split('.').str[0].tolist())
                        elif '代码' in limit_up_df.columns:
                            existing_codes.update(limit_up_df['代码'].tolist())
                    if not limit_down_df.empty:
                        if 'ts_code' in limit_down_df.columns:
                            existing_codes.update(limit_down_df['ts_code'].str.split('.').str[0].tolist())
                        elif '代码' in limit_down_df.columns:
                            existing_codes.update(limit_down_df['代码'].tolist())

                    # 只保存不在今日涨停/跌停池中的股票
                    filtered_records = [
                        r for r in performance_records
                        if r["stock_code"] not in existing_codes
                    ]

                    if filtered_records:
                        results["yesterday_limit_performance"] = self.save_to_database(filtered_records)
                        logger.info(f"✅ 保存前一交易日涨停股票今日表现: {results['yesterday_limit_performance']} 只")
                    else:
                        logger.info("所有前一交易日涨停股票今日均已涨停/跌停，无需额外保存")
                else:
                    logger.warning("未获取到前一交易日涨停股票的今日数据")
            else:
                logger.info(f"{previous_date} 无涨停股票数据")
        else:
            logger.warning("无法获取前一交易日，跳过前一交易日涨停股票表现采集")

        logger.info(
            f"数据采集完成: "
            f"涨停{results['limit_up']}只, "
            f"跌停{results['limit_down']}只, "
            f"昨日涨停今日表现{results['yesterday_limit_performance']}只"
        )

        return results


# 便捷函数
def collect_limit_stocks(trade_date: Optional[str] = None) -> Dict[str, int]:
    """采集涨跌停股池数据"""
    collector = LimitStocksCollector()
    return collector.collect_and_save(trade_date)
