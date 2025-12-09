"""
热门概念板块数据采集服务
支持多数据源自动降级机制

数据源优先级:
1. AKShare - 同花顺概念板块 (stock_board_concept_name_ths) - 免费，数据丰富
2. AKShare - 东方财富概念板块 (stock_board_concept_name_em) - 免费，实时性好
3. Tushare - 同花顺板块日行情 (ths_daily) - 需要积分，稳定可靠

采集逻辑:
1. 按优先级尝试各数据源
2. 第一个成功的数据源完成采集
3. 所有数据源都失败时记录错误
4. 采集后计算每个概念的涨停股数量
"""

import akshare as ak
import pandas as pd
import os
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple, Set
from loguru import logger
from enum import Enum

from app.utils.supabase_client import get_supabase


class DataSource(Enum):
    """数据源枚举"""
    AKSHARE_THS = "akshare_ths"      # AKShare 同花顺
    AKSHARE_EM = "akshare_em"        # AKShare 东方财富
    TUSHARE = "tushare"              # Tushare


class HotConceptsCollector:
    """热门概念板块数据采集器（支持多数据源降级）"""

    def __init__(self):
        self.supabase = get_supabase()
        self._tushare_pro = None

        # 数据源优先级列表
        self.data_source_priority = [
            DataSource.AKSHARE_THS,
            DataSource.AKSHARE_EM,
            DataSource.TUSHARE,
        ]

    @property
    def tushare_pro(self):
        """懒加载 Tushare Pro API"""
        if self._tushare_pro is None:
            try:
                import tushare as ts
                token = os.getenv('TUSHARE_TOKEN')
                if token:
                    ts.set_token(token)
                    self._tushare_pro = ts.pro_api()
                    logger.debug("Tushare Pro API 初始化成功")
                else:
                    logger.warning("TUSHARE_TOKEN 未配置，Tushare 数据源不可用")
            except Exception as e:
                logger.warning(f"Tushare 初始化失败: {e}")
        return self._tushare_pro

    # ==================== 数据源1: AKShare 同花顺 ====================

    def _collect_from_akshare_ths(self, trade_date: str, top_n: int) -> Tuple[List[Dict], bool]:
        """
        从 AKShare 同花顺接口采集数据

        Returns:
            (数据列表, 是否成功)
        """
        logger.info("🔄 尝试数据源: AKShare 同花顺...")

        try:
            # 获取概念板块列表
            concepts_df = ak.stock_board_concept_name_ths()

            if concepts_df is None or concepts_df.empty:
                logger.warning("AKShare 同花顺: 概念板块列表为空")
                return [], False

            logger.info(f"   获取到 {len(concepts_df)} 个概念板块")

            # 准备日期参数
            date_obj = datetime.strptime(trade_date, "%Y-%m-%d")
            end_date_str = date_obj.strftime("%Y%m%d")
            start_date_str = (date_obj - timedelta(days=15)).strftime("%Y%m%d")

            hot_concepts = []
            total = len(concepts_df)

            for idx, row in concepts_df.iterrows():
                try:
                    concept_name = str(row.get('name', ''))
                    if not concept_name:
                        continue

                    # 获取概念指数数据
                    index_df = ak.stock_board_concept_index_ths(
                        symbol=concept_name,
                        start_date=start_date_str,
                        end_date=end_date_str
                    )

                    if index_df is None or index_df.empty:
                        continue

                    # 取最后5个交易日
                    last_5_days = index_df.tail(5) if len(index_df) >= 5 else index_df
                    if len(last_5_days) < 2:
                        continue

                    # 获取最新数据
                    latest = last_5_days.iloc[-1]
                    actual_trade_date = pd.to_datetime(latest['日期']).strftime("%Y-%m-%d")

                    # 计算当日涨幅（今日收盘价 vs 昨日收盘价）
                    day_close = latest['收盘价']
                    prev_close = last_5_days.iloc[-2]['收盘价'] if len(last_5_days) >= 2 else day_close
                    day_change_pct = ((day_close - prev_close) / prev_close) * 100 if prev_close > 0 else 0

                    # 计算近5日累计涨幅
                    first_close = last_5_days.iloc[0]['收盘价']
                    total_change_pct = ((day_close - first_close) / first_close) * 100

                    hot_concepts.append({
                        "trade_date": actual_trade_date,
                        "concept_name": concept_name,
                        "day_change_pct": round(day_change_pct, 2),
                        "change_pct": round(total_change_pct, 2),
                        "consecutive_days": 1,
                        "concept_strength": round(total_change_pct, 4),
                        "rank": 0,
                        "is_new_concept": len(last_5_days) < 5,
                        "first_seen_date": actual_trade_date if len(last_5_days) < 5 else (
                            datetime.strptime(actual_trade_date, "%Y-%m-%d") - timedelta(days=30)
                        ).strftime("%Y-%m-%d"),
                        "data_source": DataSource.AKSHARE_THS.value,
                    })

                    if (idx + 1) % 50 == 0:
                        logger.info(f"   已处理 {idx + 1}/{total} 个概念")

                except Exception as e:
                    logger.debug(f"处理概念失败: {concept_name}, {e}")
                    continue

            if not hot_concepts:
                return [], False

            # 排序并取 top_n
            hot_concepts.sort(key=lambda x: x['change_pct'], reverse=True)
            hot_concepts = hot_concepts[:top_n]

            for rank, c in enumerate(hot_concepts, 1):
                c['rank'] = rank

            logger.info(f"✅ AKShare 同花顺: 成功采集 {len(hot_concepts)} 个概念")
            return hot_concepts, True

        except Exception as e:
            logger.warning(f"❌ AKShare 同花顺失败: {e}")
            return [], False

    # ==================== 数据源2: AKShare 东方财富 ====================

    def _collect_from_akshare_em(self, trade_date: str, top_n: int) -> Tuple[List[Dict], bool]:
        """
        从 AKShare 东方财富接口采集数据

        Returns:
            (数据列表, 是否成功)
        """
        logger.info("🔄 尝试数据源: AKShare 东方财富...")

        try:
            # 获取概念板块列表（包含实时涨跌幅）
            concepts_df = ak.stock_board_concept_name_em()

            if concepts_df is None or concepts_df.empty:
                logger.warning("AKShare 东方财富: 概念板块列表为空")
                return [], False

            logger.info(f"   获取到 {len(concepts_df)} 个概念板块")

            # 东方财富接口直接返回当日涨跌幅
            # 列名: ['排名', '板块名称', '板块代码', '最新价', '涨跌额', '涨跌幅', ...]
            hot_concepts = []

            for idx, row in concepts_df.iterrows():
                try:
                    concept_name = str(row.get('板块名称', ''))
                    change_pct = float(row.get('涨跌幅', 0))

                    if not concept_name:
                        continue

                    hot_concepts.append({
                        "trade_date": trade_date,
                        "concept_name": concept_name,
                        "day_change_pct": round(change_pct, 2),
                        "change_pct": round(change_pct, 2),  # 东方财富只有当日数据
                        "consecutive_days": 1,
                        "concept_strength": round(change_pct, 4),
                        "rank": 0,
                        "is_new_concept": False,
                        "first_seen_date": (
                            datetime.strptime(trade_date, "%Y-%m-%d") - timedelta(days=30)
                        ).strftime("%Y-%m-%d"),
                        "data_source": DataSource.AKSHARE_EM.value,
                    })

                except Exception as e:
                    logger.debug(f"处理概念失败: {e}")
                    continue

            if not hot_concepts:
                return [], False

            # 排序并取 top_n
            hot_concepts.sort(key=lambda x: x['change_pct'], reverse=True)
            hot_concepts = hot_concepts[:top_n]

            for rank, c in enumerate(hot_concepts, 1):
                c['rank'] = rank

            logger.info(f"✅ AKShare 东方财富: 成功采集 {len(hot_concepts)} 个概念")
            return hot_concepts, True

        except Exception as e:
            logger.warning(f"❌ AKShare 东方财富失败: {e}")
            return [], False

    # ==================== 数据源3: Tushare ====================

    def _collect_from_tushare(self, trade_date: str, top_n: int) -> Tuple[List[Dict], bool]:
        """
        从 Tushare 同花顺板块日行情接口采集数据

        排序逻辑: 按近5日累计涨幅降序排序，取前 top_n 名

        Returns:
            (数据列表, 是否成功)
        """
        logger.info("🔄 尝试数据源: Tushare...")

        if self.tushare_pro is None:
            logger.warning("❌ Tushare: API 未初始化")
            return [], False

        try:
            # 获取同花顺概念板块列表
            index_df = self.tushare_pro.ths_index()
            concept_list = index_df[index_df['type'] == 'N']

            if concept_list.empty:
                logger.warning("Tushare: 概念板块列表为空")
                return [], False

            logger.info(f"   获取到 {len(concept_list)} 个概念板块")

            # 获取指定日期的板块日行情（当日数据）
            date_str = trade_date.replace("-", "")
            daily_df = self.tushare_pro.ths_daily(trade_date=date_str)

            if daily_df is None or daily_df.empty:
                logger.warning(f"Tushare: {trade_date} 无板块日行情数据")
                return [], False

            logger.info(f"   获取到 {len(daily_df)} 条当日行情")

            # 合并数据，只保留概念板块
            concept_codes = set(concept_list['ts_code'].tolist())
            concept_daily = daily_df[daily_df['ts_code'].isin(concept_codes)].copy()

            if concept_daily.empty:
                logger.warning("Tushare: 无概念板块日行情数据")
                return [], False

            # 合并概念名称
            concept_daily = concept_daily.merge(
                concept_list[['ts_code', 'name']],
                on='ts_code',
                how='left'
            )

            # 计算近5日累计涨幅
            logger.info("   正在计算近5日累计涨幅...")
            five_day_change = self._calculate_5day_change_tushare(concept_daily, trade_date)

            # 合并近5日涨幅数据
            concept_daily = concept_daily.merge(
                five_day_change,
                on='ts_code',
                how='left'
            )

            # 填充缺失的近5日涨幅（用当日涨幅）
            concept_daily['change_5d'] = concept_daily['change_5d'].fillna(concept_daily['pct_change'])

            # 按近5日涨幅降序排序
            concept_daily = concept_daily.sort_values('change_5d', ascending=False)

            hot_concepts = []
            for rank, (_, row) in enumerate(concept_daily.head(top_n).iterrows(), 1):
                hot_concepts.append({
                    "trade_date": trade_date,
                    "concept_name": row['name'],
                    "day_change_pct": round(float(row['pct_change']), 2),
                    "change_pct": round(float(row['change_5d']), 2),  # 近5日涨幅
                    "consecutive_days": 1,
                    "concept_strength": round(float(row['change_5d']), 4),
                    "rank": rank,
                    "is_new_concept": False,
                    "first_seen_date": (
                        datetime.strptime(trade_date, "%Y-%m-%d") - timedelta(days=30)
                    ).strftime("%Y-%m-%d"),
                    "data_source": DataSource.TUSHARE.value,
                })

            logger.info(f"✅ Tushare: 成功采集 {len(hot_concepts)} 个概念（按近5日涨幅排序）")
            return hot_concepts, True

        except Exception as e:
            logger.warning(f"❌ Tushare 失败: {e}")
            return [], False

    def _calculate_5day_change_tushare(self, concept_daily: pd.DataFrame, trade_date: str) -> pd.DataFrame:
        """
        计算每个概念的近5日累计涨幅

        Args:
            concept_daily: 当日概念行情数据
            trade_date: 交易日期

        Returns:
            包含 ts_code 和 change_5d 的 DataFrame
        """
        try:
            # 获取近10个交易日的数据（确保有足够数据）
            date_obj = datetime.strptime(trade_date, "%Y-%m-%d")
            start_date = (date_obj - timedelta(days=15)).strftime("%Y%m%d")
            end_date = trade_date.replace("-", "")

            # 获取历史行情
            history_df = self.tushare_pro.ths_daily(
                start_date=start_date,
                end_date=end_date
            )

            if history_df is None or history_df.empty:
                logger.warning("   无法获取历史行情，使用当日涨幅")
                return pd.DataFrame(columns=['ts_code', 'change_5d'])

            # 按概念代码和日期排序
            history_df = history_df.sort_values(['ts_code', 'trade_date'])

            # 计算每个概念的近5日累计涨幅
            results = []
            for ts_code in concept_daily['ts_code'].unique():
                code_data = history_df[history_df['ts_code'] == ts_code].tail(5)

                if len(code_data) >= 2:
                    # 用收盘价计算累计涨幅: (最新收盘价 / 5日前收盘价 - 1) * 100
                    first_close = code_data.iloc[0]['close']
                    last_close = code_data.iloc[-1]['close']

                    if first_close > 0:
                        change_5d = ((last_close / first_close) - 1) * 100
                    else:
                        change_5d = code_data['pct_change'].sum()  # 退化为涨幅累加
                else:
                    # 数据不足，使用当日涨幅
                    change_5d = code_data['pct_change'].iloc[-1] if len(code_data) > 0 else 0

                results.append({
                    'ts_code': ts_code,
                    'change_5d': round(change_5d, 2)
                })

            logger.info(f"   成功计算 {len(results)} 个概念的近5日涨幅")
            return pd.DataFrame(results)

        except Exception as e:
            logger.warning(f"   计算近5日涨幅失败: {e}")
            return pd.DataFrame(columns=['ts_code', 'change_5d'])

    # ==================== 主采集方法 ====================

    def collect_hot_concepts(self, trade_date: Optional[str] = None, top_n: int = 50) -> List[Dict]:
        """
        采集热门概念板块数据（自动降级多数据源）

        按优先级尝试各数据源：
        1. AKShare 同花顺 - 数据最丰富，有5日累计涨幅
        2. AKShare 东方财富 - 实时性好，只有当日涨幅
        3. Tushare - 最稳定，需要积分

        Args:
            trade_date: 交易日期 YYYY-MM-DD（可选，默认今天）
            top_n: 返回前N个热门概念

        Returns:
            热门概念数据列表
        """
        if not trade_date:
            trade_date = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"=" * 50)
        logger.info(f"开始采集 {trade_date} 热门概念板块数据...")
        logger.info(f"数据源优先级: {' -> '.join(ds.value for ds in self.data_source_priority)}")
        logger.info(f"=" * 50)

        # 按优先级尝试各数据源
        collectors = {
            DataSource.AKSHARE_THS: self._collect_from_akshare_ths,
            DataSource.AKSHARE_EM: self._collect_from_akshare_em,
            DataSource.TUSHARE: self._collect_from_tushare,
        }

        for data_source in self.data_source_priority:
            collector_func = collectors.get(data_source)
            if collector_func:
                concepts, success = collector_func(trade_date, top_n)
                if success and concepts:
                    # 更新连续上榜天数（基于数据库历史）
                    for concept in concepts:
                        concept['consecutive_days'] = self.get_consecutive_days(
                            concept['concept_name'],
                            concept['trade_date']
                        )

                    # 计算每个概念的涨停股数量
                    concepts = self._calculate_limit_up_count(concepts, trade_date)

                    # 计算每个概念的龙头股
                    concepts = self._calculate_leader_stock(concepts, trade_date)

                    self._log_top_concepts(concepts, data_source)
                    return concepts

        logger.error("❌ 所有数据源都采集失败！")
        return []

    def _log_top_concepts(self, concepts: List[Dict], data_source: DataSource):
        """打印采集结果摘要"""
        logger.info(f"\n{'=' * 50}")
        logger.info(f"📊 采集完成 - 数据源: {data_source.value}")
        logger.info(f"   交易日期: {concepts[0]['trade_date'] if concepts else 'N/A'}")
        logger.info(f"   概念数量: {len(concepts)}")
        logger.info(f"\n   涨幅前5的概念:")
        for c in concepts[:5]:
            logger.info(f"   [{c['rank']}] {c['concept_name']}: {c['change_pct']}%")
        logger.info(f"{'=' * 50}\n")

    # ==================== 涨停股数量计算 ====================

    def _get_limit_up_stocks(self, trade_date: str) -> Set[str]:
        """
        获取指定日期的涨停股代码集合（优先从AKShare获取实时数据）

        Args:
            trade_date: 交易日期 YYYY-MM-DD

        Returns:
            涨停股代码集合（带交易所后缀，如 300081.SZ）
        """
        limit_up_stocks = set()

        # 方法1: 从 AKShare 获取实时涨停数据
        try:
            logger.debug("   尝试从 AKShare 获取涨停股数据...")
            # 获取今日涨停股
            limit_up_df = ak.stock_zt_pool_em(date=trade_date.replace("-", ""))

            if limit_up_df is not None and not limit_up_df.empty:
                for _, row in limit_up_df.iterrows():
                    code = str(row.get('代码', ''))
                    if code:
                        # 转换为带交易所后缀的格式
                        if code.startswith('6'):
                            limit_up_stocks.add(f"{code}.SH")
                        else:
                            limit_up_stocks.add(f"{code}.SZ")

                logger.debug(f"   AKShare 获取到 {len(limit_up_stocks)} 只涨停股")
                return limit_up_stocks

        except Exception as e:
            logger.debug(f"   AKShare 获取涨停股失败: {e}")

        # 方法2: 从数据库获取（备用）
        try:
            result = self.supabase.table('limit_stocks_detail')\
                .select('stock_code')\
                .eq('trade_date', trade_date)\
                .eq('limit_type', 'limit_up')\
                .execute()

            for row in result.data:
                code = row['stock_code']
                # 转换为带交易所后缀的格式
                if code.startswith('6'):
                    limit_up_stocks.add(f"{code}.SH")
                else:
                    limit_up_stocks.add(f"{code}.SZ")

            if limit_up_stocks:
                logger.debug(f"   数据库获取到 {len(limit_up_stocks)} 只涨停股")

            return limit_up_stocks
        except Exception as e:
            logger.warning(f"获取涨停股列表失败: {e}")
            return set()

    def _get_concept_code_mapping(self) -> Dict[str, str]:
        """
        获取概念名称到概念代码的映射

        Returns:
            {概念名称: 概念代码} 字典
        """
        if self.tushare_pro is None:
            return {}

        try:
            index_df = self.tushare_pro.ths_index()
            concept_list = index_df[index_df['type'] == 'N'][['ts_code', 'name']]
            return dict(zip(concept_list['name'], concept_list['ts_code']))
        except Exception as e:
            logger.warning(f"获取概念代码映射失败: {e}")
            return {}

    def _calculate_limit_up_count(self, concepts: List[Dict], trade_date: str) -> List[Dict]:
        """
        计算每个概念的涨停股数量

        Args:
            concepts: 概念数据列表
            trade_date: 交易日期

        Returns:
            添加了 limit_up_count 字段的概念数据列表
        """
        logger.info("📊 开始计算每个概念的涨停股数量...")

        # 获取今日涨停股
        limit_up_stocks = self._get_limit_up_stocks(trade_date)
        if not limit_up_stocks:
            logger.warning("   未获取到涨停股数据，跳过涨停数计算")
            for concept in concepts:
                concept['limit_up_count'] = None
            return concepts

        logger.info(f"   今日涨停股: {len(limit_up_stocks)} 只")

        # 获取概念代码映射
        concept_code_mapping = self._get_concept_code_mapping()
        if not concept_code_mapping:
            logger.warning("   未获取到概念代码映射，跳过涨停数计算")
            for concept in concepts:
                concept['limit_up_count'] = None
            return concepts

        # 缓存已查询的概念成分股
        concept_members_cache: Dict[str, Set[str]] = {}

        for concept in concepts:
            concept_name = concept['concept_name']

            # 查找概念代码（处理括号等特殊字符）
            ts_code = None

            # 精确匹配
            if concept_name in concept_code_mapping:
                ts_code = concept_code_mapping[concept_name]
            else:
                # 模糊匹配（去掉括号）
                search_name = concept_name.replace('(', '').replace(')', '').replace('（', '').replace('）', '')
                for name, code in concept_code_mapping.items():
                    clean_name = name.replace('(', '').replace(')', '').replace('（', '').replace('）', '')
                    if clean_name == search_name or search_name in clean_name or clean_name in search_name:
                        ts_code = code
                        break

            if not ts_code:
                concept['limit_up_count'] = None
                continue

            # 检查缓存
            if ts_code in concept_members_cache:
                member_codes = concept_members_cache[ts_code]
            else:
                member_codes = set()
                # 从 Tushare 获取成分股（主要方法）
                if self.tushare_pro:
                    try:
                        time.sleep(0.3)  # 避免频率限制
                        members = self.tushare_pro.ths_member(ts_code=ts_code)
                        if members is not None and not members.empty:
                            member_codes = set(members['con_code'].tolist())
                            logger.debug(f"   Tushare获取 {concept_name} 成分股: {len(member_codes)} 只")
                    except Exception as e:
                        logger.debug(f"   Tushare获取 {concept_name} 成分股失败: {e}")

                if member_codes:
                    concept_members_cache[ts_code] = member_codes
                else:
                    concept['limit_up_count'] = None
                    continue

            # 计算涨停数（成分股与涨停股的交集）
            limit_up_in_concept = limit_up_stocks & member_codes
            concept['limit_up_count'] = len(limit_up_in_concept)
            concept['total_count'] = len(member_codes)

        # 统计结果
        calculated = [c for c in concepts if c.get('limit_up_count') is not None]
        logger.info(f"   成功计算 {len(calculated)}/{len(concepts)} 个概念的涨停股数量")

        # 显示涨停数最多的概念
        top_limit_up = sorted(
            [c for c in concepts if c.get('limit_up_count')],
            key=lambda x: x['limit_up_count'],
            reverse=True
        )[:5]
        if top_limit_up:
            logger.info("   涨停数 Top 5:")
            for c in top_limit_up:
                logger.info(f"      {c['concept_name']}: {c['limit_up_count']} 只涨停")

        return concepts

    def _get_limit_up_pool_data(self, trade_date: str) -> pd.DataFrame:
        """
        获取涨停池完整数据（包含连板数、涨停时间等）

        Args:
            trade_date: 交易日期 YYYY-MM-DD

        Returns:
            涨停池 DataFrame
        """
        try:
            limit_up_df = ak.stock_zt_pool_em(date=trade_date.replace("-", ""))
            if limit_up_df is not None and not limit_up_df.empty:
                return limit_up_df
        except Exception as e:
            logger.warning(f"获取涨停池数据失败: {e}")
        return pd.DataFrame()

    def _calculate_leader_stock(self, concepts: List[Dict], trade_date: str) -> List[Dict]:
        """
        计算每个概念的龙头股

        龙头股定义：
        1. 优先选择连续涨停次数最多的
        2. 若连板数相同，优先选择创业板(300)/科创板(688)
        3. 若板块相同，选择当日涨幅最大的
        4. 若涨幅也相同，选择首次封板时间最早的

        Args:
            concepts: 概念数据列表
            trade_date: 交易日期

        Returns:
            添加了龙头股信息的概念数据列表
        """
        logger.info("📊 开始计算每个概念的龙头股...")

        # 获取涨停池数据
        limit_up_df = self._get_limit_up_pool_data(trade_date)
        if limit_up_df.empty:
            logger.warning("   未获取到涨停池数据，跳过龙头股计算")
            for concept in concepts:
                concept['leader_stock_code'] = None
                concept['leader_stock_name'] = None
                concept['leader_continuous_days'] = None
                concept['leader_change_pct'] = None
            return concepts

        logger.info(f"   涨停池数据: {len(limit_up_df)} 只股票")

        # 构建涨停股信息字典 {code: {name, continuous_days, change_pct, first_time}}
        limit_up_info = {}
        for _, row in limit_up_df.iterrows():
            code = str(row.get('代码', ''))
            if not code:
                continue
            # 转换为带交易所后缀的格式
            if code.startswith('6'):
                full_code = f"{code}.SH"
            else:
                full_code = f"{code}.SZ"

            limit_up_info[full_code] = {
                'code': code,
                'name': str(row.get('名称', '')),
                'continuous_days': int(row.get('连板数', 1)),
                'change_pct': float(row.get('涨跌幅', 0)),
                'first_time': str(row.get('首次封板时间', '235959')),
            }

        # 获取概念代码映射
        concept_code_mapping = self._get_concept_code_mapping()

        # 缓存已查询的概念成分股
        concept_members_cache: Dict[str, Set[str]] = {}

        for concept in concepts:
            concept_name = concept['concept_name']

            # 初始化龙头股字段
            concept['leader_stock_code'] = None
            concept['leader_stock_name'] = None
            concept['leader_continuous_days'] = None
            concept['leader_change_pct'] = None

            # 查找概念代码
            ts_code = None
            if concept_name in concept_code_mapping:
                ts_code = concept_code_mapping[concept_name]
            else:
                search_name = concept_name.replace('(', '').replace(')', '').replace('（', '').replace('）', '')
                for name, code in concept_code_mapping.items():
                    clean_name = name.replace('(', '').replace(')', '').replace('（', '').replace('）', '')
                    if clean_name == search_name or search_name in clean_name or clean_name in search_name:
                        ts_code = code
                        break

            if not ts_code:
                continue

            # 获取概念成分股
            if ts_code in concept_members_cache:
                member_codes = concept_members_cache[ts_code]
            else:
                member_codes = set()
                if self.tushare_pro:
                    try:
                        members = self.tushare_pro.ths_member(ts_code=ts_code)
                        if members is not None and not members.empty:
                            member_codes = set(members['con_code'].tolist())
                            concept_members_cache[ts_code] = member_codes
                    except Exception as e:
                        logger.debug(f"   获取 {concept_name} 成分股失败: {e}")

            if not member_codes:
                continue

            # 找出该概念中的涨停股
            concept_limit_up_stocks = []
            for code in member_codes:
                if code in limit_up_info:
                    stock_info = limit_up_info[code]
                    # 判断是否创业板/科创板
                    is_gem = stock_info['code'].startswith('300') or stock_info['code'].startswith('688')
                    concept_limit_up_stocks.append({
                        'code': stock_info['code'],
                        'name': stock_info['name'],
                        'continuous_days': stock_info['continuous_days'],
                        'change_pct': stock_info['change_pct'],
                        'first_time': stock_info['first_time'],
                        'is_gem': is_gem,
                    })

            if not concept_limit_up_stocks:
                continue

            # 排序找龙头：
            # 1. 连板数降序
            # 2. 创业板/科创板优先 (is_gem=True 优先)
            # 3. 涨幅降序
            # 4. 首次封板时间升序
            concept_limit_up_stocks.sort(
                key=lambda x: (
                    -x['continuous_days'],  # 连板数降序
                    not x['is_gem'],        # 创业板/科创板优先 (False < True, 所以 not is_gem)
                    -x['change_pct'],       # 涨幅降序
                    x['first_time'],        # 首次封板时间升序
                )
            )

            leader = concept_limit_up_stocks[0]
            concept['leader_stock_code'] = leader['code']
            concept['leader_stock_name'] = leader['name']
            concept['leader_continuous_days'] = leader['continuous_days']
            concept['leader_change_pct'] = round(leader['change_pct'], 2)

        # 统计结果
        calculated = [c for c in concepts if c.get('leader_stock_code')]
        logger.info(f"   成功计算 {len(calculated)}/{len(concepts)} 个概念的龙头股")

        # 显示部分龙头股
        if calculated:
            logger.info("   部分概念龙头股:")
            for c in calculated[:5]:
                logger.info(f"      {c['concept_name']}: {c['leader_stock_name']}({c['leader_stock_code']}) {c['leader_continuous_days']}连板")

        return concepts

    def get_consecutive_days(self, concept_name: str, current_date: str, lookback_days: int = 10) -> int:
        """
        计算概念的连续上榜次数

        Args:
            concept_name: 概念名称
            current_date: 当前日期 YYYY-MM-DD
            lookback_days: 回溯天数，默认10天

        Returns:
            连续上榜次数（包括今天）
        """
        try:
            response = self.supabase.table("hot_concepts")\
                .select("trade_date")\
                .eq("concept_name", concept_name)\
                .lte("trade_date", current_date)\
                .order("trade_date", desc=True)\
                .limit(lookback_days)\
                .execute()

            if not response.data:
                return 1

            trade_dates = [r['trade_date'] for r in response.data]
            consecutive_count = 0
            current_check_date = datetime.strptime(current_date, "%Y-%m-%d")

            for trade_date_str in trade_dates:
                trade_date = datetime.strptime(trade_date_str, "%Y-%m-%d")
                days_diff = (current_check_date - trade_date).days

                if days_diff == 0:
                    consecutive_count = 1
                    current_check_date = trade_date
                elif days_diff <= 3 and consecutive_count > 0:
                    consecutive_count += 1
                    current_check_date = trade_date
                else:
                    break

            return consecutive_count if consecutive_count > 0 else 1

        except Exception as e:
            logger.debug(f"计算连续上榜次数失败: {concept_name}, {e}")
            return 1

    def save_to_database(self, concepts: List[Dict]) -> int:
        """
        保存热门概念数据到 Supabase

        Args:
            concepts: 概念板块数据列表

        Returns:
            成功保存的记录数
        """
        if not concepts:
            logger.warning("没有概念数据需要保存")
            return 0

        try:
            logger.info(f"准备保存 {len(concepts)} 个热门概念数据...")

            # 移除 data_source 字段（数据库可能没有这个列）
            records = []
            for c in concepts:
                record = {k: v for k, v in c.items() if k != 'data_source'}
                records.append(record)

            response = self.supabase.table("hot_concepts").upsert(
                records, on_conflict="trade_date,concept_name"
            ).execute()

            logger.info(f"✅ 成功保存 {len(records)} 个热门概念数据")
            return len(records)

        except Exception as e:
            logger.error(f"保存热门概念数据失败: {e}")
            return 0

    def collect_and_save(self, trade_date: Optional[str] = None, top_n: int = 50) -> int:
        """
        采集并保存热门概念数据

        Args:
            trade_date: 交易日期 YYYY-MM-DD
            top_n: 保存前N个热门概念

        Returns:
            成功保存的记录数
        """
        hot_concepts = self.collect_hot_concepts(trade_date, top_n)
        return self.save_to_database(hot_concepts)


# 便捷函数
def collect_hot_concepts(trade_date: Optional[str] = None, top_n: int = 50) -> int:
    """采集热门概念板块数据"""
    collector = HotConceptsCollector()
    return collector.collect_and_save(trade_date, top_n)
