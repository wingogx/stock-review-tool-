"""
股市短线复盘数据采集脚本 - 增强版
基于专业短线交易者需求设计
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client
import os
from typing import List, Dict, Optional
import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Supabase 配置
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


class EnhancedStockDataCollector:
    """增强版股票数据采集类"""

    def __init__(self):
        self.today = datetime.now().strftime("%Y%m%d")
        logger.info(f"初始化数据采集器，交易日期: {self.today}")

    def safe_api_call(self, func, *args, **kwargs):
        """安全的API调用，带重试机制"""
        max_retries = 3
        for i in range(max_retries):
            try:
                time.sleep(1)  # 避免频繁调用
                return func(*args, **kwargs)
            except Exception as e:
                if i < max_retries - 1:
                    logger.warning(f"API调用失败，重试 {i+1}/{max_retries}: {e}")
                    time.sleep(3)
                else:
                    logger.error(f"API调用最终失败: {e}")
                    return None

    # ==========================================
    # 模块1: 大盘指数（增强版）
    # ==========================================

    def get_market_index_enhanced(self) -> List[Dict]:
        """获取大盘指数数据（含振幅）"""
        logger.info("📊 正在获取大盘指数数据...")

        indices = {
            "sh000001": "上证指数",
            "sz399001": "深证成指",
            "sz399006": "创业板指"
        }

        all_data = []

        for code, name in indices.items():
            try:
                df = self.safe_api_call(ak.stock_zh_index_daily, symbol=code)
                if df is None or df.empty:
                    continue

                latest = df.iloc[-1]
                yesterday = df.iloc[-2] if len(df) > 1 else latest

                # 计算振幅 = (最高 - 最低) / 昨收 * 100
                amplitude = ((float(latest['high']) - float(latest['low'])) /
                            float(yesterday['close']) * 100)

                data = {
                    "trade_date": latest['date'],
                    "index_code": code,
                    "index_name": name,
                    "open_price": float(latest['open']),
                    "high_price": float(latest['high']),
                    "low_price": float(latest['low']),
                    "close_price": float(latest['close']),
                    "volume": int(latest['volume']),
                    "amount": float(latest.get('amount', 0)),
                    "change_pct": float(latest.get('change', 0)),
                    "amplitude": round(amplitude, 2)
                }
                all_data.append(data)
                logger.info(f"✅ {name}: {latest['close']} ({latest.get('change', 0)}%)")

            except Exception as e:
                logger.error(f"❌ 获取 {name} 数据失败: {e}")

        return all_data

    # ==========================================
    # 模块2: 市场情绪分析
    # ==========================================

    def get_market_sentiment(self) -> Optional[Dict]:
        """获取市场情绪数据"""
        logger.info("💡 正在分析市场情绪...")

        try:
            # 1. 获取全市场实时行情
            all_stocks = self.safe_api_call(ak.stock_zh_a_spot_em)
            if all_stocks is None:
                return None

            # 2. 统计涨跌家数
            up_count = len(all_stocks[all_stocks['涨跌幅'] > 0])
            down_count = len(all_stocks[all_stocks['涨跌幅'] < 0])
            flat_count = len(all_stocks[all_stocks['涨跌幅'] == 0])

            # 3. 计算总成交额
            total_amount = all_stocks['成交额'].sum()

            # 沪深分别统计（简化版，实际需要更精确的市场划分）
            sh_stocks = all_stocks[all_stocks['代码'].str.startswith(('600', '601', '603', '688'))]
            sz_stocks = all_stocks[all_stocks['代码'].str.startswith(('000', '001', '002', '003', '300'))]

            sh_amount = sh_stocks['成交额'].sum()
            sz_amount = sz_stocks['成交额'].sum()

            # 4. 获取涨停池
            zt_pool = self.safe_api_call(ak.stock_zt_pool_em, date=self.today)
            limit_up_count = len(zt_pool) if zt_pool is not None else 0

            # 5. 获取跌停池
            dt_pool = self.safe_api_call(ak.stock_dt_pool_em, date=self.today)
            limit_down_count = len(dt_pool) if dt_pool is not None else 0

            # 6. 计算连板分布
            continuous_distribution = {}
            if zt_pool is not None and not zt_pool.empty:
                # 检查是否有'连板数'列
                if '连板数' in zt_pool.columns:
                    for i in range(2, 11):
                        count = len(zt_pool[zt_pool['连板数'] == i])
                        if count > 0:
                            continuous_distribution[f"{i}连板"] = count

                    # 统计5连板以上
                    over_5 = len(zt_pool[zt_pool['连板数'] > 5])
                    if over_5 > 0:
                        continuous_distribution["5连板以上"] = over_5

            # 7. 获取炸板数据（涨停过但未封住）
            try:
                exploded = self.safe_api_call(ak.stock_zt_pool_zbgc_em, date=self.today)
                exploded_count = len(exploded) if exploded is not None else 0
            except:
                exploded_count = 0

            explosion_rate = (exploded_count / limit_up_count * 100) if limit_up_count > 0 else 0

            # 8. 统计强势涨停（一字板 = 开板次数为0）
            strong_limit_up = 0
            weak_limit_up = 0
            if zt_pool is not None and '开板次数' in zt_pool.columns:
                strong_limit_up = len(zt_pool[zt_pool['开板次数'] == 0])
                weak_limit_up = limit_up_count - strong_limit_up

            sentiment_data = {
                "trade_date": self.today,
                "total_amount": float(total_amount),
                "sh_amount": float(sh_amount),
                "sz_amount": float(sz_amount),
                "up_count": int(up_count),
                "down_count": int(down_count),
                "flat_count": int(flat_count),
                "up_down_ratio": round(up_count / down_count, 2) if down_count > 0 else 0,
                "limit_up_count": int(limit_up_count),
                "limit_down_count": int(limit_down_count),
                "continuous_limit_distribution": continuous_distribution,
                "exploded_count": int(exploded_count),
                "explosion_rate": round(explosion_rate, 2),
                "strong_limit_up_count": int(strong_limit_up),
                "weak_limit_up_count": int(weak_limit_up)
            }

            logger.info(f"✅ 涨跌比: {sentiment_data['up_down_ratio']}, "
                       f"涨停: {limit_up_count}, 跌停: {limit_down_count}, "
                       f"炸板率: {explosion_rate:.1f}%")

            return sentiment_data

        except Exception as e:
            logger.error(f"❌ 获取市场情绪数据失败: {e}")
            return None

    # ==========================================
    # 模块3: 涨跌停个股详细
    # ==========================================

    def get_limit_stocks_detail(self) -> List[Dict]:
        """获取涨跌停个股详细数据"""
        logger.info("📈 正在获取涨跌停个股详情...")

        all_limit_stocks = []

        # 1. 涨停池数据
        try:
            zt_df = self.safe_api_call(ak.stock_zt_pool_em, date=self.today)

            if zt_df is not None and not zt_df.empty:
                for _, row in zt_df.iterrows():
                    stock_data = {
                        "trade_date": self.today,
                        "stock_code": row['代码'],
                        "stock_name": row['名称'],
                        "limit_type": "limit_up",
                        "change_pct": float(row.get('涨跌幅', 0)),
                        "close_price": float(row.get('最新价', 0)),
                        "turnover_rate": float(row.get('换手率', 0)),
                        "amount": float(row.get('成交额', 0)),
                        "first_limit_time": str(row.get('首次封板时间', '')) if pd.notna(row.get('首次封板时间')) else None,
                        "last_limit_time": str(row.get('最后封板时间', '')) if pd.notna(row.get('最后封板时间')) else None,
                        "continuous_days": int(row.get('连板数', 1)),
                        "opening_times": int(row.get('开板次数', 0)),
                        "sealed_amount": float(row.get('封单金额', 0)) if '封单金额' in row else 0,
                        "is_st": 'ST' in row['名称'] or '*' in row['名称'],
                        "is_new_stock": row.get('是否新股', '否') == '是',
                        "is_strong_limit": int(row.get('开板次数', 1)) == 0,
                        "concepts": row.get('所属行业', '').split(',') if pd.notna(row.get('所属行业')) else [],
                        "market_cap": float(row.get('总市值', 0)) if '总市值' in row else 0,
                        "circulation_market_cap": float(row.get('流通市值', 0)) if '流通市值' in row else 0
                    }
                    all_limit_stocks.append(stock_data)

                logger.info(f"✅ 获取到 {len(all_limit_stocks)} 只涨停股票")

        except Exception as e:
            logger.error(f"❌ 获取涨停数据失败: {e}")

        # 2. 跌停池数据
        try:
            dt_df = self.safe_api_call(ak.stock_dt_pool_em, date=self.today)

            if dt_df is not None and not dt_df.empty:
                limit_down_count = 0
                for _, row in dt_df.iterrows():
                    stock_data = {
                        "trade_date": self.today,
                        "stock_code": row['代码'],
                        "stock_name": row['名称'],
                        "limit_type": "limit_down",
                        "change_pct": float(row.get('涨跌幅', 0)),
                        "close_price": float(row.get('最新价', 0)),
                        "turnover_rate": float(row.get('换手率', 0)),
                        "amount": float(row.get('成交额', 0)),
                        "is_st": 'ST' in row['名称'] or '*' in row['名称'],
                        "concepts": row.get('所属行业', '').split(',') if pd.notna(row.get('所属行业')) else []
                    }
                    all_limit_stocks.append(stock_data)
                    limit_down_count += 1

                logger.info(f"✅ 获取到 {limit_down_count} 只跌停股票")

        except Exception as e:
            logger.error(f"❌ 获取跌停数据失败: {e}")

        return all_limit_stocks

    # ==========================================
    # 模块4: 龙虎榜数据（保留原有）
    # ==========================================

    def get_dragon_tiger_data(self) -> List[Dict]:
        """获取龙虎榜数据"""
        logger.info("🐉 正在获取龙虎榜数据...")

        try:
            df = self.safe_api_call(
                ak.stock_lhb_detail_em,
                start_date=self.today,
                end_date=self.today
            )

            if df is None or df.empty:
                logger.warning("⚠️  今日无龙虎榜数据")
                return []

            all_data = []
            for _, row in df.iterrows():
                data = {
                    "trade_date": row['上榜日'],
                    "stock_code": row['代码'],
                    "stock_name": row['名称'],
                    "close_price": float(row.get('收盘价', 0)),
                    "change_pct": float(row.get('涨跌幅', 0)),
                    "turnover_rate": float(row.get('换手率', 0)),
                    "total_amount": float(row.get('成交额', 0)),
                    "lhb_buy_amount": float(row.get('龙虎榜买入额', 0)),
                    "lhb_sell_amount": float(row.get('龙虎榜卖出额', 0)),
                    "lhb_net_amount": float(row.get('龙虎榜净买额', 0)),
                    "reason": row.get('上榜原因', '')
                }
                all_data.append(data)

            logger.info(f"✅ 获取到 {len(all_data)} 条龙虎榜数据")
            return all_data

        except Exception as e:
            logger.error(f"❌ 获取龙虎榜数据失败: {e}")
            return []

    # ==========================================
    # 模块5: 机构/游资席位分析
    # ==========================================

    def analyze_dragon_tiger_seats(self, lhb_stocks: List[Dict]) -> tuple:
        """分析龙虎榜席位（机构/游资）"""
        logger.info("🏦 正在分析机构和游资席位...")

        institutional_data = []
        hot_money_stats = {}

        for stock in lhb_stocks[:10]:  # 限制分析前10只股票
            code = stock['stock_code']

            try:
                # 获取买入席位
                buy_seats = self.safe_api_call(
                    ak.stock_lhb_stock_detail_em,
                    symbol=code,
                    date=self.today,
                    flag="买入"
                )

                # 获取卖出席位
                sell_seats = self.safe_api_call(
                    ak.stock_lhb_stock_detail_em,
                    symbol=code,
                    date=self.today,
                    flag="卖出"
                )

                # 统计机构席位
                inst_buy_count = 0
                inst_buy_amount = 0
                inst_sell_count = 0
                inst_sell_amount = 0

                if buy_seats is not None and not buy_seats.empty:
                    institutional_buy = buy_seats[
                        buy_seats['交易营业部名称'].str.contains('机构专用|机构席位', na=False)
                    ]
                    inst_buy_count = len(institutional_buy)
                    inst_buy_amount = float(institutional_buy['买入金额'].sum())

                    # 统计游资
                    hot_money = buy_seats[
                        ~buy_seats['交易营业部名称'].str.contains('机构专用|机构席位', na=False)
                    ]
                    for _, seat in hot_money.iterrows():
                        seat_name = seat['交易营业部名称']
                        if seat_name not in hot_money_stats:
                            hot_money_stats[seat_name] = {
                                "appearance_count": 0,
                                "total_buy_amount": 0,
                                "total_sell_amount": 0
                            }
                        hot_money_stats[seat_name]["appearance_count"] += 1
                        hot_money_stats[seat_name]["total_buy_amount"] += float(seat.get('买入金额', 0))

                if sell_seats is not None and not sell_seats.empty:
                    institutional_sell = sell_seats[
                        sell_seats['交易营业部名称'].str.contains('机构专用|机构席位', na=False)
                    ]
                    inst_sell_count = len(institutional_sell)
                    inst_sell_amount = float(institutional_sell['卖出金额'].sum())

                # 保存机构席位数据
                institutional_data.append({
                    "trade_date": self.today,
                    "stock_code": code,
                    "stock_name": stock['stock_name'],
                    "institutional_buy_count": inst_buy_count,
                    "institutional_buy_amount": inst_buy_amount,
                    "institutional_sell_count": inst_sell_count,
                    "institutional_sell_amount": inst_sell_amount,
                    "institutional_net_amount": inst_buy_amount - inst_sell_amount
                })

            except Exception as e:
                logger.error(f"❌ 分析 {code} 席位失败: {e}")
                continue

        # 转换游资统计数据
        hot_money_ranking = []
        for seat_name, stats in hot_money_stats.items():
            hot_money_ranking.append({
                "trade_date": self.today,
                "seat_name": seat_name,
                "appearance_count": stats["appearance_count"],
                "total_buy_amount": stats["total_buy_amount"],
                "total_sell_amount": stats["total_sell_amount"],
                "net_amount": stats["total_buy_amount"] - stats["total_sell_amount"]
            })

        # 按上榜次数排序
        hot_money_ranking.sort(key=lambda x: x['appearance_count'], reverse=True)

        logger.info(f"✅ 机构席位: {len(institutional_data)} 条, 活跃游资: {len(hot_money_ranking)} 个")

        return institutional_data, hot_money_ranking[:20]  # 只保留前20个活跃游资

    # ==========================================
    # 模块6: 热门概念深度分析
    # ==========================================

    def get_hot_concepts_enhanced(self) -> List[Dict]:
        """获取热门概念深度数据"""
        logger.info("🔥 正在分析热门概念板块...")

        try:
            # 1. 获取所有概念板块
            concepts_df = self.safe_api_call(ak.stock_board_concept_name_em)

            if concepts_df is None or concepts_df.empty:
                return []

            enhanced_data = []

            # 只分析涨幅前10的概念
            top_concepts = concepts_df.nlargest(10, '涨跌幅')

            for idx, (_, concept) in enumerate(top_concepts.iterrows(), 1):
                concept_name = concept['板块名称']

                try:
                    # 2. 获取概念成分股
                    time.sleep(2)  # 避免请求过快
                    stocks_df = self.safe_api_call(
                        ak.stock_board_concept_cons_em,
                        symbol=concept_name
                    )

                    if stocks_df is None or stocks_df.empty:
                        continue

                    # 3. 识别龙头股（涨幅最高的前3只）
                    top_stocks = stocks_df.nlargest(3, '涨跌幅')
                    leading_stocks = [f"{row['名称']}({row['涨跌幅']:.2f}%)"
                                    for _, row in top_stocks.iterrows()]

                    # 4. 统计涨停股
                    limit_up_count = len(stocks_df[stocks_df['涨跌幅'] >= 9.5])

                    # 5. 计算概念强度 = 平均涨幅 * 上涨家数
                    avg_change = stocks_df['涨跌幅'].mean()
                    up_count = len(stocks_df[stocks_df['涨跌幅'] > 0])
                    down_count = len(stocks_df[stocks_df['涨跌幅'] < 0])
                    strength = avg_change * up_count

                    enhanced_data.append({
                        "trade_date": self.today,
                        "concept_name": concept_name,
                        "concept_code": concept.get('板块代码', ''),
                        "change_pct": float(concept['涨跌幅']),
                        "avg_change_pct": round(avg_change, 2),
                        "leading_stocks": leading_stocks,
                        "stock_count": int(concept.get('成分股数量', len(stocks_df))),
                        "up_count": up_count,
                        "down_count": down_count,
                        "limit_up_count": limit_up_count,
                        "total_amount": float(concept.get('总成交额', 0)),
                        "concept_strength": round(strength, 2),
                        "rank": idx
                    })

                    logger.info(f"  {idx}. {concept_name}: {concept['涨跌幅']:.2f}% (龙头: {leading_stocks[0] if leading_stocks else 'N/A'})")

                except Exception as e:
                    logger.error(f"❌ 分析概念 {concept_name} 失败: {e}")
                    continue

            logger.info(f"✅ 获取到 {len(enhanced_data)} 个热门概念")
            return enhanced_data

        except Exception as e:
            logger.error(f"❌ 获取概念数据失败: {e}")
            return []

    # ==========================================
    # 保存数据到 Supabase
    # ==========================================

    def save_to_supabase(self, table_name: str, data):
        """保存数据到 Supabase"""
        try:
            if isinstance(data, dict):
                data = [data]

            if not data or len(data) == 0:
                logger.warning(f"⚠️  {table_name} 没有数据需要保存")
                return

            # Supabase upsert（如果存在则更新，不存在则插入）
            response = supabase.table(table_name).upsert(data).execute()
            logger.info(f"✅ 成功保存 {len(data)} 条数据到 {table_name}")

        except Exception as e:
            logger.error(f"❌ 保存到 {table_name} 失败: {e}")

    # ==========================================
    # 主采集流程
    # ==========================================

    def collect_all_data(self):
        """执行完整的增强版数据采集流程"""
        logger.info(f"\n{'='*70}")
        logger.info(f"🚀 开始采集 {self.today} 的股市短线复盘数据（增强版）")
        logger.info(f"{'='*70}\n")

        start_time = time.time()

        # 1. 采集大盘指数数据
        market_data = self.get_market_index_enhanced()
        self.save_to_supabase("market_index", market_data)

        # 2. 采集市场情绪数据
        sentiment_data = self.get_market_sentiment()
        if sentiment_data:
            self.save_to_supabase("market_sentiment", sentiment_data)

        # 3. 采集涨跌停个股详细数据
        limit_stocks = self.get_limit_stocks_detail()
        self.save_to_supabase("limit_stocks_detail", limit_stocks)

        # 4. 采集龙虎榜数据
        dragon_tiger_data = self.get_dragon_tiger_data()
        self.save_to_supabase("dragon_tiger_board", dragon_tiger_data)

        # 5. 分析机��和游资席位
        if dragon_tiger_data:
            institutional_data, hot_money_data = self.analyze_dragon_tiger_seats(dragon_tiger_data)
            self.save_to_supabase("institutional_seats", institutional_data)
            self.save_to_supabase("hot_money_ranking", hot_money_data)

        # 6. 采集热门概念深度数据
        concepts_data = self.get_hot_concepts_enhanced()
        self.save_to_supabase("hot_concepts", concepts_data)

        elapsed_time = time.time() - start_time

        logger.info(f"\n{'='*70}")
        logger.info(f"✅ 数据采集完成! 耗时: {elapsed_time:.1f} 秒")
        logger.info(f"{'='*70}\n")


if __name__ == "__main__":
    collector = EnhancedStockDataCollector()
    collector.collect_all_data()
