"""
同花顺概念成分股采集器

从 Tushare 的同花顺概念指数接口获取概念成分股数据，
用于补全涨停股的概念板块信息。

数据来源:
- ths_index: 同花顺概念指数列表
- ths_member: 同花顺概念成分股
"""

import os
import time
import tushare as ts
from typing import List, Dict, Optional
from loguru import logger

from app.utils.supabase_client import get_supabase


class ThsConceptCollector:
    """同花顺概念成分股采集器"""

    def __init__(self):
        self.supabase = get_supabase()
        self._tushare_pro = None

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
                        logger.info("✅ Tushare Pro API 初始化成功（高级账号）")
                    else:
                        self._tushare_pro = ts.pro_api(token)
                        logger.info("✅ Tushare Pro API 初始化成功（标准账号）")
                except Exception as e:
                    logger.warning(f"Tushare Pro 初始化失败: {e}")
        return self._tushare_pro

    def get_all_concepts(self) -> List[Dict]:
        """
        获取所有同花顺概念指数列表

        Returns:
            概念列表 [{"ts_code": "886078.TI", "name": "商业航天"}, ...]
        """
        if not self.tushare_pro:
            logger.error("Tushare Pro API 未初始化")
            return []

        try:
            # type='N' 表示概念指数
            df = self.tushare_pro.ths_index(exchange='A', type='N')

            if df is None or df.empty:
                logger.warning("同花顺概念指数列表为空")
                return []

            concepts = df[['ts_code', 'name']].to_dict('records')
            logger.info(f"✅ 获取到 {len(concepts)} 个同花顺概念")
            return concepts

        except Exception as e:
            logger.error(f"❌ 获取同花顺概念列表失败: {e}")
            return []

    def get_concept_members(self, concept_code: str) -> List[Dict]:
        """
        获取某个概念的成分股

        Args:
            concept_code: 概念代码，如 886078.TI

        Returns:
            成分股列表 [{"stock_code": "603601", "stock_name": "再升科技"}, ...]
        """
        if not self.tushare_pro:
            return []

        try:
            time.sleep(0.15)  # 避免频率限制
            df = self.tushare_pro.ths_member(ts_code=concept_code)

            if df is None or df.empty:
                return []

            members = []
            for _, row in df.iterrows():
                # 提取6位股票代码（去掉 .SH/.SZ 后缀）
                con_code = row.get('con_code', '')
                stock_code = con_code.split('.')[0] if con_code else ''

                if stock_code:
                    members.append({
                        "stock_code": stock_code,
                        "stock_name": row.get('con_name', '')
                    })

            return members

        except Exception as e:
            logger.warning(f"获取概念 {concept_code} 成分股失败: {e}")
            return []

    def collect_all_concept_members(self) -> int:
        """
        采集所有同花顺概念的成分股

        Returns:
            采集的记录数
        """
        logger.info("开始采集同花顺概念成分股...")

        # 1. 获取所有概念
        concepts = self.get_all_concepts()
        if not concepts:
            logger.error("无法获取概念列表")
            return 0

        # 2. 清空旧数据
        try:
            self.supabase.table("ths_concept_members").delete().neq("id", 0).execute()
            logger.info("✅ 已清空旧的概念成分股数据")
        except Exception as e:
            logger.warning(f"清空旧数据失败: {e}")

        # 3. 遍历每个概念，获取成分股
        total_records = 0
        batch_records = []
        batch_size = 500  # 批量插入大小

        for i, concept in enumerate(concepts):
            concept_code = concept['ts_code']
            concept_name = concept['name']

            members = self.get_concept_members(concept_code)

            for member in members:
                batch_records.append({
                    "concept_code": concept_code,
                    "concept_name": concept_name,
                    "stock_code": member["stock_code"],
                    "stock_name": member["stock_name"]
                })

            # 批量插入
            if len(batch_records) >= batch_size:
                try:
                    self.supabase.table("ths_concept_members").insert(batch_records).execute()
                    total_records += len(batch_records)
                    logger.debug(f"   已插入 {total_records} 条记录")
                    batch_records = []
                except Exception as e:
                    logger.error(f"批量插入失败: {e}")
                    batch_records = []

            # 进度日志
            if (i + 1) % 50 == 0:
                logger.info(f"   进度: {i + 1}/{len(concepts)} 概念, {total_records} 条记录")

        # 插入剩余记录
        if batch_records:
            try:
                self.supabase.table("ths_concept_members").insert(batch_records).execute()
                total_records += len(batch_records)
            except Exception as e:
                logger.error(f"插入剩余记录失败: {e}")

        logger.info(f"✅ 同花顺概念成分股采集完成，共 {total_records} 条记录")
        return total_records

    def get_stock_concepts(self, stock_code: str) -> List[str]:
        """
        从本地表查询某只股票所属的概念

        Args:
            stock_code: 股票代码（6位）

        Returns:
            概念名称列表
        """
        try:
            result = self.supabase.table("ths_concept_members")\
                .select("concept_name")\
                .eq("stock_code", stock_code)\
                .execute()

            if result.data:
                return [r["concept_name"] for r in result.data]
            return []

        except Exception as e:
            logger.warning(f"查询股票 {stock_code} 概念失败: {e}")
            return []

    def get_stocks_concepts_batch(self, stock_codes: List[str]) -> Dict[str, List[str]]:
        """
        批量查询多只股票所属的概念

        Args:
            stock_codes: 股票代码列表（6位）

        Returns:
            {stock_code: [概念1, 概念2, ...], ...}
        """
        if not stock_codes:
            return {}

        try:
            result = self.supabase.table("ths_concept_members")\
                .select("stock_code, concept_name")\
                .in_("stock_code", stock_codes)\
                .execute()

            # 按股票分组
            stock_concepts: Dict[str, List[str]] = {code: [] for code in stock_codes}
            if result.data:
                for r in result.data:
                    code = r["stock_code"]
                    if code in stock_concepts:
                        stock_concepts[code].append(r["concept_name"])

            return stock_concepts

        except Exception as e:
            logger.warning(f"批量查询股票概念失败: {e}")
            return {code: [] for code in stock_codes}


# 命令行执行入口
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    collector = ThsConceptCollector()

    # 采集所有概念成分股
    count = collector.collect_all_concept_members()
    print(f"采集完成，共 {count} 条记录")

    # 测试查询
    concepts = collector.get_stock_concepts("603601")
    print(f"再升科技所属概念: {concepts}")
