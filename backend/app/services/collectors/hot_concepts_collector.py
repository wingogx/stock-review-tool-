"""
热门概念板块数据采集服务
使用 AKShare 采集同花顺概念板块数据（真实数据）

数据来源:
- stock_board_concept_name_ths: 获取所有概念板块列表（同花顺）
- stock_board_concept_index_ths: 获取概念板块指数数据（同花顺）

采集逻辑:
1. 获取所有概念板块列表
2. 获取每个概念最近15个自然日的指数数据（确保包含至少5个交易日）
3. 取最后5个交易日数据，计算累计涨幅
4. 按5个交易日累计涨幅降序排序，取前N个热门概念
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from loguru import logger

from app.utils.supabase_client import get_supabase


class HotConceptsCollector:
    """热门概念板块数据采集器（基于同花顺5个交易日累计涨幅）"""

    def __init__(self):
        self.supabase = get_supabase()

    def get_all_concepts(self) -> pd.DataFrame:
        """
        获取所有概念板块列表（真实数据 - 同花顺）

        Returns:
            DataFrame with all concept boards
        """
        try:
            logger.info("获取所有概念板块列表（同花顺）...")

            df = ak.stock_board_concept_name_ths()

            if df is None or df.empty:
                logger.warning("概念板块列表为空")
                return pd.DataFrame()

            logger.info(f"成功获取概念板块列表，共 {len(df)} 个概念")
            return df

        except Exception as e:
            logger.error(f"获取概念板块列表失败: {str(e)}")
            return pd.DataFrame()

    def get_concept_index_data(self, concept_name: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取概念板块指数数据（真实数据 - 同花顺）

        Args:
            concept_name: 概念名称
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD

        Returns:
            DataFrame with concept index data
        """
        try:
            df = ak.stock_board_concept_index_ths(
                symbol=concept_name,
                start_date=start_date,
                end_date=end_date
            )

            if df is None or df.empty:
                return pd.DataFrame()

            return df

        except Exception as e:
            logger.debug(f"获取概念指数数据失败: {concept_name}, {str(e)}")
            return pd.DataFrame()

    def get_first_seen_date(self, concept_name: str) -> Optional[str]:
        """
        查询概念的首次出现日期

        Args:
            concept_name: 概念名称

        Returns:
            首次出现日期 YYYY-MM-DD，如果概念未曾出现过则返回 None
        """
        try:
            # 查询数据库中该概念的最早记录
            response = self.supabase.table("hot_concepts")\
                .select("first_seen_date")\
                .eq("concept_name", concept_name)\
                .not_.is_("first_seen_date", "null")\
                .order("first_seen_date")\
                .limit(1)\
                .execute()

            if response.data and len(response.data) > 0:
                return response.data[0]['first_seen_date']

            return None

        except Exception as e:
            logger.debug(f"查询首次出现日期失败: {concept_name}, {str(e)}")
            return None

    def collect_hot_concepts(self, trade_date: Optional[str] = None, top_n: int = 50) -> List[Dict]:
        """
        采集热门概念板块数据（按累计涨幅排序）

        逻辑说明:
        - 获取最近15个自然日的概念指数数据（确保包含至少5个交易日）
        - 对于有5个及以上交易日的概念：使用最后5个交易日数据
        - 对于新概念（不足5个交易日）：使用所有可用的交易日数据（最少2个）
        - 计算累计涨幅: (最新收盘价 - 第一个交易日收盘价) / 第一个交易日收盘价 × 100%
        - 按累计涨幅降序排序，取前N个概念
        - 新概念会在日志中标记 🆕

        新概念识别:
        - 历史数据不足5个交易日的概念会被标记为"新概念"
        - 新概念仍会参与排名，但使用实际可用的交易日数据计算涨幅
        - 避免错过刚出现的热门概念（通常新概念初期最活跃）

        Args:
            trade_date: 交易日期 YYYY-MM-DD（可选，默认今天）
            top_n: 返回前N个热门概念

        Returns:
            热门概念数据列表，每个概念包含:
            - trade_date: 实际交易日期
            - concept_name: 概念名称
            - change_pct: 累计涨幅（百分比，基于实际可用交易日数）
            - concept_strength: 概念强度（更精确的涨幅值）
            - rank: 排名
            - is_new_concept: 是否为新概念（历史数据不足5个交易日）
        """
        if not trade_date:
            trade_date = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"开始采集 {trade_date} 热门概念板块数据...")

        # 1. 获取所有概念列表
        concepts_list = self.get_all_concepts()

        if concepts_list.empty:
            logger.warning("概念板块列表为空")
            return []

        # 2. 准备日期参数（往前推15天，确保能获取到至少5个交易日）
        date_obj = datetime.strptime(trade_date, "%Y-%m-%d")
        end_date_str = date_obj.strftime("%Y%m%d")
        start_date_str = (date_obj - timedelta(days=15)).strftime("%Y%m%d")

        hot_concepts = []
        total_concepts = len(concepts_list)

        logger.info(f"开始处理 {total_concepts} 个概念板块...")

        for idx, row in concepts_list.iterrows():
            try:
                concept_name = str(row.get('name', ''))

                if not concept_name:
                    continue

                # 获取概念指数数据（最近15天，确保包含至少5个交易日）
                index_df = self.get_concept_index_data(concept_name, start_date_str, end_date_str)

                if index_df.empty:
                    continue

                # 取最后5个交易日的数据（如果不足5个，则取全部）
                last_5_days = index_df.tail(5) if len(index_df) >= 5 else index_df

                # 如果交易日数量不足2个，跳过该概念（至少需要2天才能计算涨幅）
                if len(last_5_days) < 2:
                    logger.debug(f"{concept_name} 交易日数量不足2个，跳过")
                    continue

                actual_trading_days = len(last_5_days)

                # 获取最新一天的数据
                latest_data = last_5_days.iloc[-1]

                # 提取真实的交易日期（从数据中获取，而不是使用参数）
                actual_trade_date = pd.to_datetime(latest_data['日期']).strftime("%Y-%m-%d")

                # 计算累计涨幅（使用实际可用的交易日数据）
                first_close = last_5_days.iloc[0]['收盘价']   # 第一个交易日的收盘价
                curr_close = latest_data['收盘价']             # 最新收盘价
                total_change_pct = ((curr_close - first_close) / first_close) * 100

                # 使用累计涨幅作为概念强度
                concept_strength = total_change_pct

                # 判断是否为新概念（基于首次出现日期）
                first_seen = self.get_first_seen_date(concept_name)

                if first_seen is None:
                    # 数据库中不存在 → 可能是新概念，也可能是首次建表
                    # 为了避免首次建表时把所有概念标记为"新"，使用历史数据长度判断
                    if len(last_5_days) < 5:
                        # 历史数据不足5天，可能是真正的新概念
                        is_new_concept = True
                        first_seen_date = actual_trade_date  # 今天是首次出现
                        logger.info(
                            f"🆕 发现全新概念: {concept_name} "
                            f"({actual_trading_days}个交易日数据，涨幅: {total_change_pct:.2f}%)"
                        )
                    else:
                        # 历史数据充足，是老概念，设置 first_seen_date 为30天前
                        is_new_concept = False
                        first_seen_date = (datetime.strptime(actual_trade_date, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")
                        logger.debug(f"老概念（首次录入）: {concept_name}，设置 first_seen_date 为 {first_seen_date}")
                else:
                    # 已存在，判断首次出现距今天数
                    first_seen_date = first_seen
                    days_since_first_seen = (datetime.strptime(actual_trade_date, "%Y-%m-%d") -
                                            datetime.strptime(first_seen, "%Y-%m-%d")).days

                    # 如果首次出现距今 ≤ 7天，仍然是新概念
                    is_new_concept = days_since_first_seen <= 7

                    if is_new_concept:
                        logger.info(
                            f"🆕 新概念: {concept_name} (出现第{days_since_first_seen + 1}天，涨幅: {total_change_pct:.2f}%)"
                        )

                concept_data = {
                    "trade_date": actual_trade_date,  # 使用实际交易日期
                    "concept_name": concept_name,
                    "change_pct": round(total_change_pct, 2),  # 累计涨幅（百分比）
                    "concept_strength": round(concept_strength, 4),  # 概念强度（更精确的涨幅值）
                    "rank": 0,  # 将在排序后更新
                    "is_new_concept": is_new_concept,  # 标记是否为新概念
                    "first_seen_date": first_seen_date,  # 首次出现日期
                }

                hot_concepts.append(concept_data)

                # 限制进度日志输出
                if (idx + 1) % 50 == 0:
                    logger.info(f"  已处理 {idx + 1}/{total_concepts} 个概念")

            except Exception as e:
                logger.debug(f"处理概念板块失败: {concept_name}, {str(e)}")
                continue

        # 按5天累计涨幅排序，取前 top_n
        hot_concepts.sort(key=lambda x: x['change_pct'], reverse=True)
        hot_concepts = hot_concepts[:top_n]

        # 更新排名
        for rank, concept in enumerate(hot_concepts, 1):
            concept['rank'] = rank

        # 获取实际交易日期（从第一个概念中提取）
        actual_date = hot_concepts[0]['trade_date'] if hot_concepts else trade_date

        # 统计新概念数量
        new_concepts_count = sum(1 for c in hot_concepts if c.get('is_new_concept', False))

        logger.info(f"成功采集 {len(hot_concepts)} 个热门概念板块（交易日: {actual_date}，按累计涨幅排序）")
        if new_concepts_count > 0:
            logger.info(f"🆕 其中包含 {new_concepts_count} 个新概念（历史数据不足5个交易日）")

        # 显示前5个概念
        for concept in hot_concepts[:5]:
            new_tag = " 🆕" if concept.get('is_new_concept', False) else ""
            logger.info(
                f"  [{concept['rank']}] {concept['concept_name']}: "
                f"涨幅 {concept['change_pct']}%{new_tag}"
            )

        return hot_concepts

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

            # 批量插入（使用 upsert）
            response = self.supabase.table("hot_concepts").upsert(
                concepts, on_conflict="trade_date,concept_name"
            ).execute()

            logger.info(f"成功保存 {len(concepts)} 个热门概念数据")
            return len(concepts)

        except Exception as e:
            logger.error(f"保存热门概念数据失败: {str(e)}")
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
