"""
混合数据源采集器
Tushare (5000积分) + AKShare (免费) 双数据源方案
充分利用 Tushare 的高质量数据和 AKShare 的免费全面数据
"""

import tushare as ts
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()


class HybridDataCollector:
    """混合数据源采集器"""

    def __init__(self):
        # Tushare 配置
        self.ts_token = os.getenv("TUSHARE_TOKEN")
        if not self.ts_token:
            raise ValueError("请在 .env 文件中设置 TUSHARE_TOKEN")

        ts.set_token(self.ts_token)
        self.pro = ts.pro_api()

        # Supabase 配置
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        self.supabase: Client = create_client(supabase_url, supabase_key)

        # 日期
        self.today = datetime.now().strftime("%Y%m%d")
        self.today_dash = datetime.now().strftime("%Y-%m-%d")

    # ============================================
    # 1. 龙虎榜数据 - 使用 Tushare（5000积分优势）
    # ============================================

    def get_dragon_tiger_tushare(self):
        """
        使用 Tushare 获取龙虎榜数据
        优势：直接提供机构席位分类，无需解析营业部名称
        """
        logger.info("📊 使用 Tushare 获取龙虎榜数据...")

        try:
            # 1. 获取龙虎榜每日明细（2000积分）
            df_list = self.pro.top_list(
                trade_date=self.today,
                fields='trade_date,ts_code,name,close,pct_change,amount,l_sell,l_buy,l_amount,net_amount,net_rate,amount_rate,float_values,reason'
            )

            logger.info(f"   ✅ 龙虎榜明细: {len(df_list)} 条")

            # 2. 获取龙虎榜机构明细（5000积分 - 你的优势！）
            df_inst = self.pro.top_inst(
                trade_date=self.today,
                fields='trade_date,ts_code,exalter,buy,buy_rate,sell,sell_rate,net_buy'
            )

            logger.info(f"   ✅ 机构席位明细: {len(df_inst)} 条")

            # 保存到数据库
            if not df_list.empty:
                records = df_list.to_dict('records')
                for record in records:
                    self.supabase.table('dragon_tiger_board').upsert({
                        'trade_date': record['trade_date'],
                        'stock_code': record['ts_code'],
                        'stock_name': record['name'],
                        'close_price': float(record['close']),
                        'change_pct': float(record['pct_change']),
                        'turnover': float(record['amount']),
                        'total_buy': float(record['l_buy']),
                        'total_sell': float(record['l_sell']),
                        'net_amount': float(record['net_amount']),
                        'reason': record['reason']
                    }).execute()

            # 保存机构席位
            if not df_inst.empty:
                inst_records = df_inst.to_dict('records')
                for record in inst_records:
                    self.supabase.table('institutional_seats').upsert({
                        'trade_date': record['trade_date'],
                        'stock_code': record['ts_code'],
                        'exalter': record['exalter'],  # 营业部名称
                        'buy_amount': float(record['buy']),
                        'buy_rate': float(record['buy_rate']),
                        'sell_amount': float(record['sell']),
                        'sell_rate': float(record['sell_rate']),
                        'net_buy': float(record['net_buy'])
                    }).execute()

            return {
                "dragon_tiger_list": df_list,
                "institutional_seats": df_inst
            }

        except Exception as e:
            logger.error(f"   ❌ Tushare 龙虎榜获取失败: {e}")
            return None

    # ============================================
    # 2. 涨停池数据 - 使用 AKShare（更详细）
    # ============================================

    def get_limit_stocks_akshare(self):
        """
        使用 AKShare 获取涨停池数据
        优势：包含首次封板时间、最后封板时间、连板数、炸板次数等详细字段
        """
        logger.info("📊 使用 AKShare 获取涨停池数据...")

        try:
            # 涨停池（AKShare 比 Tushare 更详细）
            zt_df = ak.stock_zt_pool_em(date=self.today)

            logger.info(f"   ✅ 涨停池: {len(zt_df)} 只")

            # 炸板数据（Tushare 没有专门的炸板API）
            zbgc_df = ak.stock_zt_pool_zbgc_em(date=self.today)

            logger.info(f"   ✅ 炸板数据: {len(zbgc_df)} 只")

            # 保存到数据库
            if not zt_df.empty:
                records = zt_df.to_dict('records')
                for record in records:
                    # 解析封板时间
                    first_time = record.get('首次封板时间', None)
                    last_time = record.get('最后封板时间', None)

                    self.supabase.table('limit_stocks_detail').upsert({
                        'trade_date': self.today_dash,
                        'stock_code': record['代码'],
                        'stock_name': record['名称'],
                        'limit_type': 'limit_up',
                        'close_price': float(record['最新价']),
                        'change_pct': float(record['涨跌幅']),
                        'turnover': float(record['成交额']),
                        'turnover_rate': float(record['换手率']),
                        'first_limit_time': first_time,
                        'last_limit_time': last_time,
                        'continuous_days': int(record.get('连板数', 1)),
                        'opening_times': int(record.get('开板次数', 0)),
                        'industry': record.get('所属行业', '')
                    }).execute()

            return {
                "limit_up": zt_df,
                "exploded": zbgc_df
            }

        except Exception as e:
            logger.error(f"   ❌ AKShare 涨停池获取失败: {e}")
            return None

    # ============================================
    # 3. 概念板块 - 使用 AKShare（更全面）
    # ============================================

    def get_concepts_akshare(self):
        """
        使用 AKShare 获取概念板块数据
        原因：Tushare 概念数据需要 6000积分（你只有5000）
              AKShare 提供 374 个概念，免费且更全面
        """
        logger.info("📊 使用 AKShare 获取概念板块数据...")

        try:
            # 同花顺概念板块（374个）
            concepts_df = ak.stock_board_concept_name_ths()

            logger.info(f"   ✅ 概念板块: {len(concepts_df)} 个")

            # 获取涨幅TOP10的概念详情
            top_concepts = concepts_df.nlargest(10, '涨跌幅')

            for _, concept in top_concepts.iterrows():
                concept_name = concept['板块名称']

                # 获取概念成分股
                stocks_df = ak.stock_board_concept_cons_em(symbol=concept_name)

                if not stocks_df.empty:
                    # 识别龙头股
                    top_stocks = stocks_df.nlargest(3, '涨跌幅')

                    # 计算概念强度
                    up_count = len(stocks_df[stocks_df['涨跌幅'] > 0])
                    avg_change = stocks_df['涨跌幅'].mean()
                    strength = avg_change * up_count

                    # 保存概念数据
                    self.supabase.table('hot_concepts').upsert({
                        'trade_date': self.today_dash,
                        'concept_name': concept_name,
                        'change_pct': float(concept['涨跌幅']),
                        'avg_change': float(avg_change),
                        'up_count': int(up_count),
                        'down_count': int(len(stocks_df[stocks_df['涨跌幅'] < 0])),
                        'leading_stocks': top_stocks['名称'].tolist()[:3],
                        'strength_score': float(strength),
                        'total_stocks': int(len(stocks_df))
                    }).execute()

            return concepts_df

        except Exception as e:
            logger.error(f"   ❌ AKShare 概念板块获取失败: {e}")
            return None

    # ============================================
    # 4. 市场统计 - 使用 Tushare（官方权威）
    # ============================================

    def get_market_stats_tushare(self):
        """
        使用 Tushare 获取市场统计数据
        优势：官方权威数据，质量稳定
        """
        logger.info("📊 使用 Tushare 获取市场统计数据...")

        try:
            # 获取市场交易统计（2000积分）
            df = self.pro.daily_info(
                trade_date=self.today,
                fields='trade_date,ts_code,amount,vol,trans_count,pe,pb,total_share,float_share,free_share,total_mv,circ_mv'
            )

            logger.info(f"   ✅ 市场统计: {len(df)} 条")

            return df

        except Exception as e:
            logger.error(f"   ❌ Tushare 市场统计获取失败: {e}")
            return None

    # ============================================
    # 5. 市场情绪 - 使用 AKShare（补充独家数据）
    # ============================================

    def get_market_sentiment_akshare(self):
        """
        使用 AKShare 获取市场活跃度等独家数据
        优势：同花顺市场活跃度是独家数据
        """
        logger.info("📊 使用 AKShare 获取市场活跃度...")

        try:
            # 市场活跃度（同花顺独家）
            activity_df = ak.stock_market_activity_legu()

            activity_dict = dict(zip(activity_df['item'], activity_df['value']))

            # 获取全市场行情（用于统计涨跌）
            all_stocks = ak.stock_zh_a_spot_em()

            up_count = len(all_stocks[all_stocks['涨跌幅'] > 0])
            down_count = len(all_stocks[all_stocks['涨跌幅'] < 0])

            # 保存市场情绪
            self.supabase.table('market_sentiment').upsert({
                'trade_date': self.today_dash,
                'total_amount': float(all_stocks['成交额'].sum()),
                'up_count': int(up_count),
                'down_count': int(down_count),
                'up_down_ratio': float(up_count / down_count) if down_count > 0 else 0,
                'market_activity': float(str(activity_dict.get('活跃度', '0%')).replace('%', '')),
                'suspended_count': int(activity_dict.get('停牌', 0))
            }).execute()

            logger.info(f"   ✅ 市场活跃度: {activity_dict.get('活跃度', 'N/A')}")

            return activity_dict

        except Exception as e:
            logger.error(f"   ❌ AKShare 市场活跃度获取失败: {e}")
            return None

    # ============================================
    # 6. 主采集函数
    # ============================================

    def collect_all_data(self):
        """执行完整的数据采集流程"""
        logger.info(f"\\n{'='*80}")
        logger.info(f"  开始数据采集 - {self.today}")
        logger.info(f"  数据源: Tushare (5000积分) + AKShare (免费)")
        logger.info(f"{'='*80}\\n")

        results = {}

        # 1. 龙虎榜（Tushare - 利用5000积分优势）
        results['dragon_tiger'] = self.get_dragon_tiger_tushare()

        # 2. 涨停池（AKShare - 字段更详细）
        results['limit_stocks'] = self.get_limit_stocks_akshare()

        # 3. 概念板块（AKShare - 免费且更全面）
        results['concepts'] = self.get_concepts_akshare()

        # 4. 市场统计（Tushare - 官方权威）
        results['market_stats'] = self.get_market_stats_tushare()

        # 5. 市场活跃度（AKShare - 独家数据）
        results['market_sentiment'] = self.get_market_sentiment_akshare()

        logger.info(f"\\n{'='*80}")
        logger.info("  ✅ 数据采集完成!")
        logger.info(f"{'='*80}\\n")

        return results


# ============================================
# 使用示例
# ============================================

if __name__ == "__main__":
    print("="*80)
    print("  混合数据源采集器")
    print("  Tushare (5000积分) + AKShare (免费)")
    print("="*80)

    try:
        collector = HybridDataCollector()
        results = collector.collect_all_data()

        print("\\n✅ 采集完成!")
        print("\\n📊 数据统计:")

        if results.get('dragon_tiger'):
            print(f"   龙虎榜: {len(results['dragon_tiger']['dragon_tiger_list'])} 条")
            print(f"   机构席位: {len(results['dragon_tiger']['institutional_seats'])} 条")

        if results.get('limit_stocks'):
            print(f"   涨停池: {len(results['limit_stocks']['limit_up'])} 只")
            print(f"   炸板: {len(results['limit_stocks']['exploded'])} 只")

        if results.get('concepts') is not None:
            print(f"   概念板块: {len(results['concepts'])} 个")

    except Exception as e:
        print(f"\\n❌ 采集失败: {e}")
        import traceback
        traceback.print_exc()
