"""
热门概念板块数据采集服务
使用 AKShare 采集同花顺概念板块数据

数据来源:
- stock_board_concept_name_em: 获取所有概念板块列表
- stock_board_concept_hist_em: 获取概念板块历史数据
- stock_board_concept_cons_em: 获取概念成分股
"""

import akshare as ak
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict
from loguru import logger
import json

from app.utils.supabase_client import get_supabase


class HotConceptsCollector:
    """热门概念板块数据采集器"""

    def __init__(self):
        self.supabase = get_supabase()

    def get_all_concepts(self) -> pd.DataFrame:
        """
        获取所有概念板块列表（真实数据）

        Returns:
            DataFrame with all concept boards
        """
        try:
            logger.info("获取所有概念板块列表...")

            df = ak.stock_board_concept_name_em()

            if df is None or df.empty:
                logger.warning("概念板块列表为空")
                return pd.DataFrame()

            logger.info(f"成功获取概念板块列表，共 {len(df)} 个概念")
            return df

        except Exception as e:
            logger.error(f"获取概念板块列表失败: {str(e)}")
            return pd.DataFrame()

    def get_concept_realtime_data(self) -> pd.DataFrame:
        """
        获取概念板块实时行情数据（真实数据）

        Returns:
            DataFrame with concept boards realtime data
        """
        try:
            logger.info("获取概念板块实时行情...")

            # 使用东方财富概念板块实时行情接口
            df = ak.stock_board_concept_name_em()

            if df is None or df.empty:
                logger.warning("概念板块实时行情为空")
                return pd.DataFrame()

            logger.info(f"成功获取概念板块实时行情，共 {len(df)} 个概念")
            logger.debug(f"概念板块列名: {df.columns.tolist()}")

            return df

        except Exception as e:
            logger.error(f"获取概念板块实时行情失败: {str(e)}")
            return pd.DataFrame()

    def get_concept_constituents(self, concept_name: str) -> pd.DataFrame:
        """
        获取概念成分股（真实数据）

        Args:
            concept_name: 概念名称

        Returns:
            DataFrame with constituent stocks
        """
        try:
            logger.debug(f"获取概念 {concept_name} 的成分股...")

            df = ak.stock_board_concept_cons_em(symbol=concept_name)

            if df is None or df.empty:
                logger.debug(f"概念 {concept_name} 没有成分股数据")
                return pd.DataFrame()

            return df

        except Exception as e:
            logger.debug(f"获取概念成分股失败: {concept_name}, {str(e)}")
            return pd.DataFrame()

    def get_leading_stocks(self, concept_df: pd.DataFrame, limit: int = 3) -> List[Dict]:
        """
        从成分股中提取龙头股（涨幅最高的前N只）

        Args:
            concept_df: 概念成分股 DataFrame
            limit: 返回前N只龙头股

        Returns:
            龙头股列表
        """
        if concept_df.empty:
            return []

        try:
            # 按涨跌幅排序
            if '涨跌幅' not in concept_df.columns:
                return []

            # 过滤掉 ST 股票（可选）
            sorted_df = concept_df.sort_values('涨跌幅', ascending=False).head(limit)

            leading_stocks = []
            for _, row in sorted_df.iterrows():
                stock = {
                    "code": str(row.get('代码', '')),
                    "name": str(row.get('名称', '')),
                    "change_pct": float(row.get('涨跌幅', 0))
                }
                leading_stocks.append(stock)

            return leading_stocks

        except Exception as e:
            logger.warning(f"提取龙头股失败: {str(e)}")
            return []

    def collect_hot_concepts(self, trade_date: Optional[str] = None, top_n: int = 50) -> List[Dict]:
        """
        采集热门概念板块数据

        Args:
            trade_date: 交易日期 YYYY-MM-DD
            top_n: 返回前N个热门概念

        Returns:
            热门概念数据列表
        """
        if not trade_date:
            trade_date = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"开始采集 {trade_date} 热门概念板块数据...")

        # 获取概念板块实时行情
        concepts_df = self.get_concept_realtime_data()

        if concepts_df.empty:
            logger.warning("概念板块数据为空")
            return []

        # 按涨跌幅排序，取前 top_n
        if '涨跌幅' in concepts_df.columns:
            concepts_df = concepts_df.sort_values('涨跌幅', ascending=False).head(top_n)

        hot_concepts = []

        for idx, row in concepts_df.iterrows():
            try:
                concept_name = str(row.get('板块名称', row.get('名称', '')))

                if not concept_name:
                    continue

                # 获取成分股
                constituents_df = self.get_concept_constituents(concept_name)

                # 统计成分股数据
                total_count = len(constituents_df)
                up_count = 0
                down_count = 0
                limit_up_count = 0

                if not constituents_df.empty and '涨跌幅' in constituents_df.columns:
                    up_count = (constituents_df['涨跌幅'] > 0).sum()
                    down_count = (constituents_df['涨跌幅'] < 0).sum()
                    limit_up_count = (constituents_df['涨跌幅'] >= 9.9).sum()

                # 提取龙头股
                leading_stocks = self.get_leading_stocks(constituents_df, limit=3)

                # 计算概念强度评分（涨幅 × 上涨家数）
                change_pct = float(row.get('涨跌幅', 0))
                strength_score = change_pct * up_count if up_count > 0 else 0

                concept_data = {
                    "trade_date": trade_date,
                    "concept_name": concept_name,
                    "change_pct": change_pct,
                    "total_count": total_count,
                    "up_count": int(up_count),
                    "down_count": int(down_count),
                    "limit_up_count": int(limit_up_count),
                    "leading_stocks": leading_stocks,
                    "strength_score": round(strength_score, 4),
                    "rank": int(idx) + 1,
                }

                hot_concepts.append(concept_data)

                # 限制日志输出
                if idx < 5:
                    logger.debug(f"  [{idx+1}] {concept_name}: 涨幅{change_pct}%, 成分股{total_count}只, 龙头{len(leading_stocks)}只")

            except Exception as e:
                logger.warning(f"处理概念板块失败: {concept_name}, {str(e)}")
                continue

        logger.info(f"成功采集 {len(hot_concepts)} 个热门概念板块")
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

            # 转换 leading_stocks 为 JSON
            records = []
            for concept in concepts:
                record = concept.copy()
                record["leading_stocks"] = json.dumps(record["leading_stocks"], ensure_ascii=False)
                records.append(record)

            # 批量插入（使用 upsert）
            response = self.supabase.table("hot_concepts").upsert(
                records, on_conflict="trade_date,concept_name"
            ).execute()

            logger.info(f"成功保存 {len(records)} 个热门概念数据")
            return len(records)

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
