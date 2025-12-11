"""
热门概念板块数据采集服务
支持多数据源自动降级机制

数据源优先级（Tushare优先，保证概念名称统一）:
1. Tushare - 同花顺板块日行情 (ths_daily + ths_index) - 需要积分，数据最可靠，概念名称统一，可计算5日涨幅
2. AKShare - 同花顺概念板块 (stock_board_concept_name_ths) - 免费，数据丰富，备用方案
3. AKShare - 东方财富概念板块 (stock_board_concept_name_em) - 免费，实时性好，最终备用

采集逻辑:
1. 按优先级尝试各数据源
2. 第一个成功的数据源完成采集
3. 所有数据源都失败时记录错误
4. 采集后计算每个概念的涨停股数量和龙头股
5. Tushare数据源返回ts_code，避免名称匹配问题，使用5日涨幅排序
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

        # 数据源优先级列表（Tushare优先，保证概念名称统一）
        self.data_source_priority = [
            DataSource.TUSHARE,        # 优先：概念名称统一，有5日历史数据
            DataSource.AKSHARE_THS,    # 备用：有完整的5日历史数据
            DataSource.AKSHARE_EM,     # 备用：东方财富只有当日数据
        ]

    @property
    def tushare_pro(self):
        """懒加载 Tushare Pro API（支持高级账号配置）"""
        if self._tushare_pro is None:
            try:
                import tushare as ts
                token = os.getenv('TUSHARE_TOKEN')
                if token:
                    ts.set_token(token)
                    self._tushare_pro = ts.pro_api()

                    # 配置高级账号的自定义HTTP URL（如果提供）
                    http_url = os.getenv('TUSHARE_HTTP_URL')
                    if http_url:
                        self._tushare_pro._DataApi__token = token
                        self._tushare_pro._DataApi__http_url = http_url
                        logger.info(f"✅ Tushare Pro API 初始化成功（高级账号）: {http_url}")
                    else:
                        logger.debug("Tushare Pro API 初始化成功（标准账号）")
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
        从 Tushare 同花顺板块日行情接口采集数据（优先数据源）

        排序逻辑: 按当日涨跌幅(pct_change)降序排序，取前 top_n 名
        优势: 返回ts_code，后续计算涨停数和龙头股无需名称匹配，覆盖率100%

        Returns:
            (数据列表, 是否成功)
        """
        logger.info("🔄 尝试数据源: Tushare（高级账号，优先）...")

        if self.tushare_pro is None:
            logger.warning("❌ Tushare: API 未初始化")
            return [], False

        try:
            # 获取同花顺概念板块列表
            time.sleep(0.3)  # 避免频率限制
            index_df = self.tushare_pro.ths_index()
            concept_list = index_df[index_df['type'] == 'N']

            if concept_list.empty:
                logger.warning("Tushare: 概念板块列表为空")
                return [], False

            logger.info(f"   获取到 {len(concept_list)} 个概念板块")

            # 获取指定日期的板块日行情（当日数据）
            date_str = trade_date.replace("-", "")
            time.sleep(0.3)  # 避免频率限制
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

            # 计算5日涨幅
            logger.info("   计算概念5日涨幅...")
            change_5d_df = self._calculate_5day_change_tushare(concept_daily, trade_date)

            if change_5d_df is not None and not change_5d_df.empty:
                # 合并5日涨幅数据
                concept_daily = concept_daily.merge(
                    change_5d_df[['ts_code', 'change_5d']],
                    on='ts_code',
                    how='left'
                )
                # 按5日涨幅降序排序
                concept_daily = concept_daily.sort_values('change_5d', ascending=False, na_position='last')
                logger.info(f"   ✅ 按5日涨幅排序")
            else:
                # 如果5日涨幅计算失败，fallback到当日涨幅
                logger.warning("   ⚠️ 5日涨幅计算失败，使用当日涨幅排序")
                concept_daily['change_5d'] = concept_daily['pct_change']
                concept_daily = concept_daily.sort_values('pct_change', ascending=False)

            hot_concepts = []
            for rank, (_, row) in enumerate(concept_daily.head(top_n).iterrows(), 1):
                change_5d = row.get('change_5d', row['pct_change'])
                hot_concepts.append({
                    "trade_date": trade_date,
                    "concept_name": row['name'],
                    "concept_code": row['ts_code'],  # ✨ 添加 ts_code，避免后续名称匹配
                    "day_change_pct": round(float(row['pct_change']), 2),
                    "change_pct": round(float(change_5d), 2),  # 5日涨幅
                    "consecutive_days": 1,
                    "concept_strength": round(float(change_5d), 4),
                    "rank": rank,
                    "is_new_concept": False,
                    "first_seen_date": (
                        datetime.strptime(trade_date, "%Y-%m-%d") - timedelta(days=30)
                    ).strftime("%Y-%m-%d"),
                    "data_source": DataSource.TUSHARE.value,
                })

            logger.info(f"✅ Tushare: 成功采集 {len(hot_concepts)} 个概念（按5日涨幅排序，含ts_code）")
            return hot_concepts, True

        except Exception as e:
            error_msg = str(e)
            # 检查是否是限速错误
            if "频繁" in error_msg or "10秒" in error_msg or "限制" in error_msg:
                logger.error(f"🚫 Tushare 被限速: {error_msg}")
                logger.error("⏰ 请等待后重试，或稍后再采集数据")
            else:
                logger.error(f"❌ Tushare 失败: {error_msg}")
            return [], False

    def _calculate_5day_change_tushare(self, concept_daily: pd.DataFrame, trade_date: str) -> pd.DataFrame:
        """
        计算每个概念的近5日累计涨幅

        优化策略：
        1. 先批量查询所有概念的历史数据
        2. 对于数据不足5天的概念，单独查询补充（降低API调用次数）
        3. 只使用最近5个交易日的数据计算涨幅

        Args:
            concept_daily: 当日概念行情数据
            trade_date: 交易日期

        Returns:
            包含 ts_code 和 change_5d 的 DataFrame
        """
        try:
            # 获取近期交易日的数据（考虑周末和节假日，回溯15天确保有足够数据）
            date_obj = datetime.strptime(trade_date, "%Y-%m-%d")
            start_date = (date_obj - timedelta(days=15)).strftime("%Y%m%d")
            end_date = trade_date.replace("-", "")

            # 步骤1: 批量获取历史行情
            logger.debug(f"   批量查询历史行情: {start_date} 到 {end_date}")
            history_df = self.tushare_pro.ths_daily(
                start_date=start_date,
                end_date=end_date
            )

            if history_df is None or history_df.empty:
                logger.warning("   无法获取历史行情，使用当日涨幅")
                return pd.DataFrame(columns=['ts_code', 'change_5d'])

            # 按概念代码和日期排序
            history_df = history_df.sort_values(['ts_code', 'trade_date'])

            # 统计历史数据
            unique_dates = history_df['trade_date'].unique()
            logger.debug(f"   批量查询: 共 {len(history_df)} 条，覆盖 {len(unique_dates)} 个交易日")

            # 步骤2: 检查哪些概念数据不足5天，需要单独补充
            concepts_need_补充 = []
            for ts_code in concept_daily['ts_code'].unique():
                code_data = history_df[history_df['ts_code'] == ts_code]
                if len(code_data) < 5:
                    concepts_need_补充.append(ts_code)

            # 步骤3: 对数据不足的概念单独查询
            if concepts_need_补充:
                logger.info(f"   发现 {len(concepts_need_补充)} 个概念数据不足5天，开始单独查询...")
                补充_count = 0

                for ts_code in concepts_need_补充:
                    try:
                        time.sleep(0.1)  # 避免频率限制
                        single_df = self.tushare_pro.ths_daily(
                            ts_code=ts_code,
                            start_date=start_date,
                            end_date=end_date
                        )

                        if single_df is not None and not single_df.empty:
                            # 移除该概念的旧数据
                            history_df = history_df[history_df['ts_code'] != ts_code]
                            # 添加新数据
                            history_df = pd.concat([history_df, single_df], ignore_index=True)
                            补充_count += 1

                            if 补充_count <= 3:  # 只打印前3个
                                logger.debug(f"      {ts_code}: 补充成功，现有{len(single_df)}天数据")
                    except Exception as e:
                        logger.debug(f"      {ts_code}: 补充失败 - {e}")

                if 补充_count > 0:
                    logger.info(f"   ✅ 成功补充 {补充_count}/{len(concepts_need_补充)} 个概念的历史数据")
                    # 重新排序
                    history_df = history_df.sort_values(['ts_code', 'trade_date'])

            # 步骤4: 计算每个概念的近5日累计涨幅（只用最近5天）
            results = []
            insufficient_count = 0  # 统计数据不足5天的数量

            for i, ts_code in enumerate(concept_daily['ts_code'].unique()):
                code_data = history_df[history_df['ts_code'] == ts_code]

                # 只取最近5天数据
                if len(code_data) >= 5:
                    code_data = code_data.tail(5)  # ✨ 关键修改：只取最近5天
                elif len(code_data) < 5 and len(code_data) >= 1:
                    insufficient_count += 1

                # 计算涨幅
                if len(code_data) >= 1:
                    days = len(code_data)

                    # 使用涨跌幅复利计算
                    # 公式: ((1 + r1/100) * (1 + r2/100) * ... * (1 + rn/100) - 1) * 100
                    cumulative_return = 1.0
                    for pct in code_data['pct_change'].values:
                        cumulative_return *= (1 + pct / 100)
                    change_5d = (cumulative_return - 1) * 100

                    # 前5个概念打印详细日志
                    if i < 5:
                        date_range = f"{code_data.iloc[0]['trade_date']} 到 {code_data.iloc[-1]['trade_date']}"
                        logger.debug(f"   [{ts_code}] {days}天数据({date_range}), 5日涨幅{change_5d:.2f}%")
                else:
                    # 完全没有数据，使用0
                    change_5d = 0
                    if i < 5:
                        logger.debug(f"   [{ts_code}] 无历史数据")

                results.append({
                    'ts_code': ts_code,
                    'change_5d': round(change_5d, 2)
                })

            if insufficient_count > 0:
                logger.info(f"   ⚠️ {insufficient_count} 个概念历史数据不足5天（使用实际天数计算）")

            logger.info(f"   成功计算 {len(results)} 个概念的近5日涨幅")
            return pd.DataFrame(results)

        except Exception as e:
            logger.warning(f"   计算近5日涨幅失败: {e}")
            return pd.DataFrame(columns=['ts_code', 'change_5d'])

    # ==================== 主采集方法 ====================

    def collect_hot_concepts(self, trade_date: Optional[str] = None, top_n: int = 50) -> List[Dict]:
        """
        采集热门概念板块数据（只使用Tushare数据源）

        优先使用Tushare数据源，如果失败（包括限速）则直接报错，不自动切换到其他数据源。
        这样可以确保涨停数和龙头股数据的完整性（需要ts_code）。

        Args:
            trade_date: 交易日期 YYYY-MM-DD（可选，默认今天）
            top_n: 返回前N个热门概念

        Returns:
            热门概念数据列表

        Raises:
            Exception: 当Tushare数据源失败时抛出异常
        """
        if not trade_date:
            trade_date = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"=" * 50)
        logger.info(f"开始采集 {trade_date} 热门概念板块数据...")
        logger.info(f"数据源: Tushare（唯一数据源）")
        logger.info(f"=" * 50)

        # 只使用Tushare数据源
        concepts, success = self._collect_from_tushare(trade_date, top_n)

        if not success or not concepts:
            error_msg = f"❌ Tushare数据源采集失败！请检查是否被限速或网络问题。"
            logger.error(error_msg)
            raise Exception(error_msg)

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

        self._log_top_concepts(concepts, DataSource.TUSHARE)
        return concepts

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
        获取指定日期的涨停股代码集合（优先从Tushare高级账号获取）

        Args:
            trade_date: 交易日期 YYYY-MM-DD

        Returns:
            涨停股代码集合（带交易所后缀，如 300081.SZ）
        """
        limit_up_stocks = set()

        # 方法1: 优先从 Tushare limit_list_ths 获取（高级账号，最可靠）
        if self.tushare_pro:
            try:
                logger.debug("   尝试从 Tushare limit_list_ths 获取涨停股数据...")
                time.sleep(0.3)  # 避免频率限制
                limit_up_df = self.tushare_pro.limit_list_ths(
                    trade_date=trade_date.replace("-", ""),
                    limit_type='涨停池'
                )

                if limit_up_df is not None and not limit_up_df.empty:
                    for _, row in limit_up_df.iterrows():
                        code = str(row.get('ts_code', ''))
                        if code:
                            limit_up_stocks.add(code)

                    logger.debug(f"   ✅ Tushare 获取到 {len(limit_up_stocks)} 只涨停股")
                    return limit_up_stocks

            except Exception as e:
                logger.debug(f"   Tushare 获取涨停股失败: {e}")

        # 方法2: 从 AKShare 获取实时涨停数据（备用）
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

        # 方法3: 从数据库获取（最后备用）
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
        获取概念名称到概念代码的映射（支持模糊匹配）

        Returns:
            {概念名称: 概念代码} 字典
        """
        if self.tushare_pro is None:
            return {}

        try:
            # 使用 concept() 接口代替 ths_index()
            concept_df = self.tushare_pro.concept()

            # 构建映射字典（精确匹配）
            mapping = dict(zip(concept_df['name'], concept_df['code']))

            # 增加模糊匹配支持：双向匹配"概念"后缀
            for name, code in list(mapping.items()):
                # 情况1：如果原名称不含"概念"，添加带"概念"的变体
                # 例如: "阿尔茨海默" -> 添加 "阿尔茨海默概念"
                if '概念' not in name:
                    mapping[f"{name}概念"] = code
                # 情况2：如果原名称以"概念"结尾，添加去除"概念"的变体
                # 例如: "光纤概念" -> 添加 "光纤"
                elif name.endswith('概念'):
                    mapping[name[:-2]] = code

            return mapping
        except Exception as e:
            logger.warning(f"获取概念代码映射失败: {e}")
            return {}

    def _calculate_limit_up_count(self, concepts: List[Dict], trade_date: str) -> List[Dict]:
        """
        计算每个概念的涨停股数量（使用ths_member获取成分股，然后匹配涨停池）

        Args:
            concepts: 概念数据列表（必须包含concept_code字段）
            trade_date: 交易日期

        Returns:
            添加了 limit_up_count 字段的概念数据列表
        """
        logger.info("📊 开始计算每个概念的涨停股数量...")

        try:
            # 从数据库获取涨停股数据（只需要ts_code）
            result = self.supabase.table('limit_stocks_detail')\
                .select('stock_code', 'stock_name')\
                .eq('trade_date', trade_date)\
                .eq('limit_type', 'limit_up')\
                .execute()

            if not result.data:
                logger.warning("   未获取到涨停股数据，跳过涨停数计算")
                for concept in concepts:
                    concept['limit_up_count'] = None
                    concept['total_count'] = None
                return concepts

            # 构建涨停股代码集合（添加交易所后缀）
            limit_up_codes = set()
            for stock in result.data:
                code = stock['stock_code']
                # 添加两种格式：带后缀和不带后缀
                limit_up_codes.add(code)
                # 根据代码判断交易所
                if code.startswith('6'):
                    limit_up_codes.add(f"{code}.SH")
                else:
                    limit_up_codes.add(f"{code}.SZ")

            logger.info(f"   今日涨停股: {len(result.data)} 只")

            # 为每个概念计算涨停股数量（使用ths_member获取成分股）
            for concept in concepts:
                concept_name = concept['concept_name']
                concept_code = concept.get('concept_code')  # ts_code

                matched_count = 0

                if concept_code and self.tushare_pro:
                    try:
                        # 使用ths_member获取该概念的成分股
                        time.sleep(0.1)  # 避免频率限制
                        members_df = self.tushare_pro.ths_member(ts_code=concept_code)

                        if members_df is not None and not members_df.empty:
                            # 获取成分股代码列表
                            member_codes = set(members_df['con_code'].tolist())

                            # 计算交集：成分股中有多少在涨停池中
                            matched_codes = member_codes & limit_up_codes
                            matched_count = len(matched_codes)

                            logger.debug(f"   {concept_name}: 成分股{len(member_codes)}只, 涨停{matched_count}只")
                        else:
                            logger.debug(f"   {concept_name}: 无成分股数据")

                    except Exception as e:
                        logger.debug(f"   {concept_name}: 获取成分股失败 - {e}")

                concept['limit_up_count'] = matched_count
                concept['total_count'] = None  # 暂不统计总成分股数

            # 统计结果
            calculated = [c for c in concepts if c.get('limit_up_count', 0) > 0]
            logger.info(f"   成功计算 {len(calculated)}/{len(concepts)} 个概念的涨停股数量")

            # 显示涨停数最多的概念
            top_limit_up = sorted(
                [c for c in concepts if c.get('limit_up_count', 0) > 0],
                key=lambda x: x['limit_up_count'],
                reverse=True
            )[:5]
            if top_limit_up:
                logger.info("   涨停数 Top 5:")
                for c in top_limit_up:
                    logger.info(f"      {c['concept_name']}: {c['limit_up_count']} 只涨停")

        except Exception as e:
            logger.error(f"   计算涨停数失败: {e}")
            for concept in concepts:
                concept['limit_up_count'] = None
                concept['total_count'] = None

        return concepts

    def _get_limit_up_pool_data(self, trade_date: str) -> pd.DataFrame:
        """
        获取涨停池完整数据（包含连板数、涨停时间等）
        优先从Tushare高级账号获取，数据更可靠

        Args:
            trade_date: 交易日期 YYYY-MM-DD

        Returns:
            涨停池 DataFrame（统一字段格式）
        """
        # 方法1: 优先从 Tushare limit_list_ths 获取（高级账号）
        if self.tushare_pro:
            try:
                logger.debug("   尝试从 Tushare limit_list_ths 获取涨停池数据...")
                time.sleep(0.3)
                limit_up_df = self.tushare_pro.limit_list_ths(
                    trade_date=trade_date.replace("-", ""),
                    limit_type='涨停池'
                )

                if limit_up_df is not None and not limit_up_df.empty:
                    # 将Tushare字段映射到统一格式
                    mapped_df = pd.DataFrame()

                    # 从ts_code提取股票代码（去掉.SH/.SZ后缀）
                    mapped_df['代码'] = limit_up_df['ts_code'].apply(lambda x: x.split('.')[0] if pd.notna(x) else '')
                    mapped_df['名称'] = limit_up_df['name']
                    mapped_df['涨跌幅'] = limit_up_df['pct_chg']

                    # 从tag字段解析连板数（如"2天2板" -> 2，"首板" -> 1）
                    def parse_continuous_days(tag):
                        if pd.isna(tag):
                            return 1
                        tag_str = str(tag)
                        if '首板' in tag_str:
                            return 1
                        # 匹配"N天N板"格式
                        import re
                        match = re.search(r'(\d+)天', tag_str)
                        if match:
                            return int(match.group(1))
                        return 1

                    mapped_df['连板数'] = limit_up_df['tag'].apply(parse_continuous_days)

                    # 使用limit_order作为封单额参考（需要转换单位）
                    mapped_df['首次封板时间'] = '000000'  # Tushare没有此字段，设置默认值

                    # 保留原始ts_code用于匹配
                    mapped_df['ts_code'] = limit_up_df['ts_code']

                    logger.debug(f"   ✅ Tushare 获取到 {len(mapped_df)} 只涨停股数据")
                    return mapped_df

            except Exception as e:
                logger.debug(f"   Tushare 获取涨停池数据失败: {e}")

        # 方法2: 从 AKShare 获取（备用）
        try:
            logger.debug("   尝试从 AKShare 获取涨停池数据...")
            limit_up_df = ak.stock_zt_pool_em(date=trade_date.replace("-", ""))
            if limit_up_df is not None and not limit_up_df.empty:
                logger.debug(f"   AKShare 获取到 {len(limit_up_df)} 只涨停股数据")
                return limit_up_df
        except Exception as e:
            logger.warning(f"AKShare 获取涨停池数据失败: {e}")

        return pd.DataFrame()

    def _calculate_leader_stock(self, concepts: List[Dict], trade_date: str) -> List[Dict]:
        """
        计算每个概念的龙头股（使用ths_member获取成分股，然后匹配涨停池）

        龙头股定义：
        1. 优先选择连续涨停次数最多的
        2. 若连板数相同，优先选择创业板(300)/科创板(688)
        3. 若板块相同，选择当日涨幅最大的
        4. 若涨幅也相同，选择首次封板时间最早的

        Args:
            concepts: 概念数据列表（必须包含concept_code字段）
            trade_date: 交易日期

        Returns:
            添加了龙头股信息的概念数据列表
        """
        logger.info("📊 开始计算每个概念的龙头股...")

        try:
            # 从数据库获取涨停股数据（包含连板数等信息）
            result = self.supabase.table('limit_stocks_detail')\
                .select('stock_code', 'stock_name', 'continuous_days', 'change_pct', 'first_limit_time')\
                .eq('trade_date', trade_date)\
                .eq('limit_type', 'limit_up')\
                .execute()

            if not result.data:
                logger.warning("   未获取到涨停股数据，跳过龙头股计算")
                for concept in concepts:
                    concept['leader_stock_code'] = None
                    concept['leader_stock_name'] = None
                    concept['leader_continuous_days'] = None
                    concept['leader_change_pct'] = None
                return concepts

            # 构建涨停股字典（key=带后缀的ts_code, value=股票信息）
            limit_up_dict = {}
            for stock in result.data:
                code = stock['stock_code']
                # 添加带后缀的格式
                if code.startswith('6'):
                    ts_code = f"{code}.SH"
                else:
                    ts_code = f"{code}.SZ"

                limit_up_dict[ts_code] = {
                    'code': code,
                    'name': stock['stock_name'],
                    'continuous_days': stock.get('continuous_days') or 1,
                    'change_pct': stock.get('change_pct') or 0,
                    'first_time': stock.get('first_limit_time') or '235959',
                    'is_gem': code.startswith('300') or code.startswith('688'),
                }

            logger.info(f"   涨停池数据: {len(result.data)} 只股票")

            # 为每个概念计算龙头股（使用ths_member获取成分股）
            for concept in concepts:
                concept_name = concept['concept_name']
                concept_code = concept.get('concept_code')  # ts_code

                # 初始化龙头股字段
                concept['leader_stock_code'] = None
                concept['leader_stock_name'] = None
                concept['leader_continuous_days'] = None
                concept['leader_change_pct'] = None

                if not concept_code or not self.tushare_pro:
                    continue

                try:
                    # 使用ths_member获取该概念的成分股
                    time.sleep(0.1)  # 避免频率限制
                    members_df = self.tushare_pro.ths_member(ts_code=concept_code)

                    if members_df is None or members_df.empty:
                        logger.debug(f"   {concept_name}: 无成分股数据")
                        continue

                    # 获取成分股中在涨停池的股票
                    concept_limit_up_stocks = []
                    for _, row in members_df.iterrows():
                        con_code = row['con_code']  # 格式：000001.SZ
                        if con_code in limit_up_dict:
                            concept_limit_up_stocks.append(limit_up_dict[con_code])

                    if not concept_limit_up_stocks:
                        logger.debug(f"   {concept_name}: 成分股中无涨停股")
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

                except Exception as e:
                    logger.debug(f"   {concept_name}: 计算龙头股失败 - {e}")

            # 统计结果
            calculated = [c for c in concepts if c.get('leader_stock_code')]
            logger.info(f"   成功计算 {len(calculated)}/{len(concepts)} 个概念的龙头股")

            # 显示部分龙头股
            if calculated:
                logger.info("   龙头股 Top 5:")
                for c in calculated[:5]:
                    logger.info(f"      {c['concept_name']}: {c['leader_stock_name']}({c['leader_stock_code']}) {c['leader_continuous_days']}连板")

        except Exception as e:
            logger.error(f"   计算龙头股失败: {e}")
            for concept in concepts:
                concept['leader_stock_code'] = None
                concept['leader_stock_name'] = None
                concept['leader_continuous_days'] = None
                concept['leader_change_pct'] = None

        return concepts

    def get_consecutive_days(self, concept_name: str, current_date: str, lookback_days: int = 10) -> int:
        """
        计算概念的连续上榜次数

        逻辑：
        1. 查询最近一次上榜日期
        2. 如果距离当前日期<=3天，认为是连续的，继承上次的consecutive_days并+1
        3. 如果>3天或没有历史记录，返回1（首次上榜）

        Args:
            concept_name: 概念名称
            current_date: 当前日期 YYYY-MM-DD
            lookback_days: 回溯天数，默认10天

        Returns:
            连续上榜次数（包括今天）
        """
        try:
            # 关键修改：查询历史数据时使用 lt (小于) 而不是 lte (小于等于)
            # 因为当前日期的数据还没有保存到数据库
            response = self.supabase.table("hot_concepts")\
                .select("trade_date, consecutive_days")\
                .eq("concept_name", concept_name)\
                .lt("trade_date", current_date)\
                .order("trade_date", desc=True)\
                .limit(1)\
                .execute()

            if not response.data:
                # 没有历史记录，今天是第一次上榜
                return 1

            # 获取最近一次上榜的记录
            last_record = response.data[0]
            last_date = datetime.strptime(last_record['trade_date'], "%Y-%m-%d")
            current_date_obj = datetime.strptime(current_date, "%Y-%m-%d")
            days_diff = (current_date_obj - last_date).days

            # 如果距离上一次上榜不超过3天（考虑周末），则认为是连续的
            if days_diff <= 3:
                # 继承上次的连续天数并+1
                last_consecutive = last_record.get('consecutive_days', 1)
                return last_consecutive + 1
            else:
                # 中断了，重新开始计数
                return 1

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

            # 移除 data_source 和 concept_code 字段（仅用于内部计算，数据库没有这些列）
            records = []
            for c in concepts:
                record = {k: v for k, v in c.items() if k not in ['data_source', 'concept_code']}
                records.append(record)

            response = self.supabase.table("hot_concepts").upsert(
                records, on_conflict="trade_date,concept_name"
            ).execute()

            logger.info(f"✅ 成功保存 {len(records)} 个热门概念数据")
            return len(records)

        except Exception as e:
            logger.error(f"保存热门概念数据失败: {e}")
            return 0

    def collect_and_save(self, trade_date: Optional[str] = None, top_n: int = 10) -> int:
        """
        采集并保存热门概念数据

        Args:
            trade_date: 交易日期 YYYY-MM-DD
            top_n: 保存前N个热门概念（默认10个，按5日涨幅排序）

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
