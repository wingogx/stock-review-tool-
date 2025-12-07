"""
股市复盘数据采集脚本
使用 AKShare 获取股票数据并存储到 Supabase
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client
import os
from typing import List, Dict

# Supabase 配置
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


class StockDataCollector:
    """股票数据采集类"""

    def __init__(self):
        self.today = datetime.now().strftime("%Y%m%d")

    def get_market_index_data(self) -> pd.DataFrame:
        """
        获取大盘指数数据（上证、深证、创业板）
        """
        print(f"📊 正在获取大盘指数数据...")

        indices = {
            "sh000001": "上证指数",
            "sz399001": "深证成指",
            "sz399006": "创业板指"
        }

        all_data = []

        for code, name in indices.items():
            try:
                # 获取指数历史数据
                df = ak.stock_zh_index_daily(symbol=code)
                latest = df.iloc[-1]

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
                    "change_pct": float(latest.get('change', 0))
                }
                all_data.append(data)
                print(f"✅ {name}: {latest['close']}")

            except Exception as e:
                print(f"❌ 获取 {name} 数据失败: {e}")

        return all_data

    def get_limit_stats_data(self) -> Dict:
        """
        获取涨跌停数据
        """
        print(f"📈 正在获取涨跌停数据...")

        try:
            # 获取涨停板数据
            limit_up_df = ak.stock_zt_pool_em(date=self.today)
            limit_up_count = len(limit_up_df)
            limit_up_stocks = limit_up_df['代码'].tolist()

            # 获取跌停板数据
            limit_down_df = ak.stock_dxsyl_em()  # 这里需要根据实际API调整
            limit_down_count = len(limit_down_df)
            limit_down_stocks = limit_down_df['代码'].tolist() if '代码' in limit_down_df.columns else []

            data = {
                "trade_date": self.today,
                "limit_up_count": limit_up_count,
                "limit_down_count": limit_down_count,
                "limit_up_stocks": limit_up_stocks,
                "limit_down_stocks": limit_down_stocks
            }

            print(f"✅ 涨停: {limit_up_count}只, 跌停: {limit_down_count}只")
            return data

        except Exception as e:
            print(f"❌ 获取涨跌停数据失败: {e}")
            return None

    def get_dragon_tiger_data(self) -> List[Dict]:
        """
        获取龙虎榜数据
        """
        print(f"🐉 正在获取龙虎榜数据...")

        try:
            # 获取龙虎榜每日明细
            df = ak.stock_lhb_detail_em(
                start_date=self.today,
                end_date=self.today
            )

            all_data = []
            for _, row in df.iterrows():
                data = {
                    "trade_date": row['上榜日'],
                    "stock_code": row['代码'],
                    "stock_name": row['名称'],
                    "close_price": float(row['收盘价']),
                    "change_pct": float(row['涨跌幅']),
                    "turnover_rate": float(row.get('换手率', 0)),
                    "total_amount": float(row.get('成交额', 0)),
                    "lhb_buy_amount": float(row.get('龙虎榜买入额', 0)),
                    "lhb_sell_amount": float(row.get('龙虎榜卖出额', 0)),
                    "lhb_net_amount": float(row.get('龙虎榜净买入额', 0)),
                    "reason": row.get('上榜原因', '')
                }
                all_data.append(data)

            print(f"✅ 获取到 {len(all_data)} 条龙虎榜数据")
            return all_data

        except Exception as e:
            print(f"❌ 获取龙虎榜数据失败: {e}")
            return []

    def get_dragon_tiger_seats(self, stock_code: str) -> List[Dict]:
        """
        获取龙虎榜席位明细
        """
        try:
            # 获取买入席位
            buy_df = ak.stock_lhb_stock_detail_em(
                symbol=stock_code,
                date=self.today,
                flag="买入"
            )

            # 获取卖出席位
            sell_df = ak.stock_lhb_stock_detail_em(
                symbol=stock_code,
                date=self.today,
                flag="卖出"
            )

            all_seats = []

            # 处理买入席位
            for _, row in buy_df.iterrows():
                all_seats.append({
                    "trade_date": self.today,
                    "stock_code": stock_code,
                    "seat_name": row['交易营业部名称'],
                    "buy_amount": float(row.get('买入金额', 0)),
                    "sell_amount": 0,
                    "net_amount": float(row.get('净额', 0)),
                    "seat_type": "买入"
                })

            # 处理卖出席位
            for _, row in sell_df.iterrows():
                all_seats.append({
                    "trade_date": self.today,
                    "stock_code": stock_code,
                    "seat_name": row['交易营业部名称'],
                    "buy_amount": 0,
                    "sell_amount": float(row.get('卖出金额', 0)),
                    "net_amount": float(row.get('净额', 0)),
                    "seat_type": "卖出"
                })

            return all_seats

        except Exception as e:
            print(f"❌ 获取 {stock_code} 席位明细失败: {e}")
            return []

    def get_hot_concepts_data(self) -> List[Dict]:
        """
        获取热门概念板块数据
        """
        print(f"🔥 正在获取热门概念板块数据...")

        try:
            # 获取概念板块数据
            df = ak.stock_board_concept_name_em()

            all_data = []
            for _, row in df.iterrows():
                data = {
                    "trade_date": self.today,
                    "concept_name": row['板块名称'],
                    "concept_code": row['板块代码'],
                    "change_pct": float(row.get('涨跌幅', 0)),
                    "leading_stock": row.get('龙头股票', ''),
                    "stock_count": int(row.get('股票数量', 0)),
                    "up_count": int(row.get('上涨数量', 0)),
                    "down_count": int(row.get('下跌数量', 0)),
                    "total_amount": float(row.get('总成交额', 0))
                }
                all_data.append(data)

            # 按涨跌幅排序，取前20
            all_data.sort(key=lambda x: x['change_pct'], reverse=True)
            top_data = all_data[:20]

            print(f"✅ 获取到 {len(top_data)} 个热门概念板块")
            return top_data

        except Exception as e:
            print(f"❌ 获取概念板块数据失败: {e}")
            return []

    def save_to_supabase(self, table_name: str, data: List[Dict] or Dict):
        """
        保存数据到 Supabase
        """
        try:
            if isinstance(data, dict):
                data = [data]

            if not data:
                print(f"⚠️  {table_name} 没有数据需要保存")
                return

            response = supabase.table(table_name).upsert(data).execute()
            print(f"✅ 成功保存 {len(data)} 条数据到 {table_name}")

        except Exception as e:
            print(f"❌ 保存到 {table_name} 失败: {e}")

    def collect_all_data(self):
        """
        执行完整的数据采集流程
        """
        print(f"\n{'='*60}")
        print(f"🚀 开始采集 {self.today} 的股市数据")
        print(f"{'='*60}\n")

        # 1. 采集大盘指数数据
        market_data = self.get_market_index_data()
        self.save_to_supabase("market_index", market_data)

        # 2. 采集涨跌停数据
        limit_data = self.get_limit_stats_data()
        if limit_data:
            self.save_to_supabase("limit_stats", limit_data)

        # 3. 采集龙虎榜数据
        dragon_tiger_data = self.get_dragon_tiger_data()
        self.save_to_supabase("dragon_tiger_board", dragon_tiger_data)

        # 4. 采集龙虎榜席位明细（针对每只上榜股票）
        for stock in dragon_tiger_data[:5]:  # 只采集前5只股票的明细
            seats_data = self.get_dragon_tiger_seats(stock['stock_code'])
            if seats_data:
                self.save_to_supabase("dragon_tiger_seats", seats_data)

        # 5. 采集热门概念板块数据
        concepts_data = self.get_hot_concepts_data()
        self.save_to_supabase("hot_concepts", concepts_data)

        print(f"\n{'='*60}")
        print(f"✅ 数据采集完成!")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    collector = StockDataCollector()
    collector.collect_all_data()
