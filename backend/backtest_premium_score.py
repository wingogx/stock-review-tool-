"""
明日溢价概率评分模型 - 历史数据回测脚本

功能：
1. 获取历史涨停股数据
2. 计算每只股票的溢价评分
3. 获取次日实际涨跌幅
4. 统计各评分档位的真实表现
5. 生成回测报告

使用方法：
python backtest_premium_score.py --start-date 2024-11-01 --end-date 2024-12-12
"""

import os
import sys
import argparse
import asyncio
import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger
from collections import defaultdict
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.premium_probability_service import PremiumProbabilityService
from app.utils.supabase_client import get_supabase
from app.utils.trading_date import get_latest_trading_date


class PremiumScoreBacktest:
    """溢价评分回测器"""

    def __init__(self):
        self.supabase = get_supabase()
        self.premium_service = PremiumProbabilityService()

        # 初始化Tushare（获取次日涨跌幅）
        token = os.getenv("TUSHARE_TOKEN")
        if token:
            http_url = os.getenv("TUSHARE_HTTP_URL")
            if http_url:
                # 使用自定义HTTP URL（高级账号）
                self.tushare_pro = ts.pro_api()
                self.tushare_pro._DataApi__token = token
                self.tushare_pro._DataApi__http_url = http_url
                logger.info(f"✅ Tushare Pro 初始化成功（自定义URL）: {http_url}")
            else:
                # 使用默认URL
                self.tushare_pro = ts.pro_api(token)
                logger.info("✅ Tushare Pro 初始化成功（默认URL）")
        else:
            logger.warning("未配置TUSHARE_TOKEN，无法获取次日涨跌幅数据")
            self.tushare_pro = None

    def get_trading_dates(self, start_date: str, end_date: str) -> list:
        """
        获取交易日列表

        Args:
            start_date: YYYY-MM-DD
            end_date: YYYY-MM-DD

        Returns:
            交易日列表
        """
        try:
            response = self.supabase.table("limit_stocks_detail")\
                .select("trade_date")\
                .gte("trade_date", start_date)\
                .lte("trade_date", end_date)\
                .execute()

            if response.data:
                # 去重并排序
                dates = sorted(list(set([item["trade_date"] for item in response.data])))
                logger.info(f"获取到 {len(dates)} 个交易日")
                return dates

            return []

        except Exception as e:
            logger.error(f"获取交易日失败: {e}")
            return []

    def get_limit_up_stocks(self, trade_date: str) -> list:
        """获取指定日期的涨停股列表"""
        try:
            response = self.supabase.table("limit_stocks_detail")\
                .select("stock_code, stock_name, continuous_days")\
                .eq("trade_date", trade_date)\
                .eq("limit_type", "limit_up")\
                .execute()

            if response.data:
                logger.info(f"{trade_date} 共 {len(response.data)} 只涨停股")
                return response.data

            return []

        except Exception as e:
            logger.error(f"获取涨停股失败: {e}")
            return []

    def get_next_day_change(self, stock_code: str, trade_date: str) -> float:
        """
        获取次日涨跌幅

        Args:
            stock_code: 股票代码（6位数字）
            trade_date: 当日日期 YYYY-MM-DD

        Returns:
            次日涨跌幅（%），若无数据返回None
        """
        if not self.tushare_pro:
            return None

        try:
            # 转换股票代码格式（添加交易所后缀）
            if stock_code.startswith("6"):
                ts_code = f"{stock_code}.SH"
            else:
                ts_code = f"{stock_code}.SZ"

            # 获取次日后5个交易日的数据（确保能拿到次日）
            current_date = datetime.strptime(trade_date, "%Y-%m-%d")
            end_date = (current_date + timedelta(days=10)).strftime("%Y%m%d")
            start_date = current_date.strftime("%Y%m%d")

            df = self.tushare_pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )

            if df is not None and len(df) >= 2:
                # 按日期排序，取第2个交易日（次日）
                df = df.sort_values("trade_date")
                next_day = df.iloc[1]
                return float(next_day["pct_chg"])

            return None

        except Exception as e:
            logger.debug(f"获取 {stock_code} 次日涨跌幅失败: {e}")
            return None

    async def run_backtest(self, start_date: str, end_date: str) -> dict:
        """
        运行回测

        Args:
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD

        Returns:
            回测结果统计
        """
        logger.info(f"=" * 60)
        logger.info(f"开始回测: {start_date} ~ {end_date}")
        logger.info(f"=" * 60)

        # 获取交易日
        trading_dates = self.get_trading_dates(start_date, end_date)
        if not trading_dates:
            logger.error("未找到交易日数据")
            return {}

        # 统计结果
        results = []
        score_distribution = defaultdict(int)  # 评分分布
        score_stats = defaultdict(lambda: {
            "count": 0,
            "next_day_changes": [],
            "positive_count": 0,
            "big_loss_count": 0  # 大面（跌>5%）
        })

        # 遍历每个交易日
        for idx, trade_date in enumerate(trading_dates):
            logger.info(f"\n[{idx+1}/{len(trading_dates)}] 处理 {trade_date}...")

            # 获取当日涨停股
            limit_stocks = self.get_limit_up_stocks(trade_date)
            if not limit_stocks:
                continue

            # 对每只股票计算评分
            for stock in limit_stocks:
                stock_code = stock["stock_code"]
                stock_name = stock["stock_name"]

                # 计算溢价评分
                score_result = await self.premium_service.calculate_premium_score(
                    stock_code, trade_date
                )

                if not score_result:
                    continue

                # 获取次日涨跌幅
                next_day_change = self.get_next_day_change(stock_code, trade_date)

                if next_day_change is None:
                    logger.debug(f"  {stock_name}({stock_code}) 无次日数据，跳过")
                    continue

                # 记录结果
                result_item = {
                    "trade_date": trade_date,
                    "stock_code": stock_code,
                    "stock_name": stock_name,
                    "total_score": score_result.total_score,
                    "premium_level": score_result.premium_level,
                    "next_day_change": next_day_change
                }
                results.append(result_item)

                # 统计
                score_distribution[score_result.premium_level] += 1
                score_stats[score_result.premium_level]["count"] += 1
                score_stats[score_result.premium_level]["next_day_changes"].append(next_day_change)

                if next_day_change > 0:
                    score_stats[score_result.premium_level]["positive_count"] += 1

                if next_day_change < -5:
                    score_stats[score_result.premium_level]["big_loss_count"] += 1

                logger.info(f"  {stock_name}({stock_code}): 评分{score_result.total_score:.2f}({score_result.premium_level}) → 次日{next_day_change:+.2f}%")

        # 生成统计报告
        logger.info(f"\n{'=' * 60}")
        logger.info(f"回测完成！共分析 {len(results)} 只股票")
        logger.info(f"{'=' * 60}\n")

        # 打印各档位统计
        self._print_statistics(score_stats)

        # 保存详细结果
        self._save_results(results, start_date, end_date)

        return {
            "total_samples": len(results),
            "score_distribution": dict(score_distribution),
            "score_stats": dict(score_stats)
        }

    def _print_statistics(self, score_stats: dict):
        """打印统计结果"""
        logger.info("各评分档位表现：\n")

        # 按档位顺序排列
        levels = ["极高", "高", "偏高", "中性", "偏低", "低"]

        print(f"{'档位':<8} {'样本数':<8} {'次日平均涨幅':<12} {'正溢价率':<12} {'大面率':<12}")
        print("-" * 60)

        for level in levels:
            if level not in score_stats:
                continue

            stats = score_stats[level]
            count = stats["count"]
            changes = stats["next_day_changes"]
            positive_count = stats["positive_count"]
            big_loss_count = stats["big_loss_count"]

            avg_change = sum(changes) / len(changes) if changes else 0
            positive_rate = (positive_count / count * 100) if count > 0 else 0
            big_loss_rate = (big_loss_count / count * 100) if count > 0 else 0

            print(f"{level:<8} {count:<8} {avg_change:+.2f}%{' '*6} {positive_rate:.1f}%{' '*6} {big_loss_rate:.1f}%")

        print("")

    def _save_results(self, results: list, start_date: str, end_date: str):
        """保存详细结果到CSV"""
        if not results:
            return

        df = pd.DataFrame(results)
        filename = f"backtest_results_{start_date}_to_{end_date}.csv"
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        logger.info(f"✅ 详细结果已保存: {filename}\n")


def main():
    parser = argparse.ArgumentParser(description="明日溢价概率评分模型回测")
    parser.add_argument("--start-date", type=str, required=True, help="开始日期 YYYY-MM-DD")
    parser.add_argument("--end-date", type=str, required=True, help="结束日期 YYYY-MM-DD")

    args = parser.parse_args()

    # 运行回测（使用 asyncio.run 执行异步函数）
    backtester = PremiumScoreBacktest()
    asyncio.run(backtester.run_backtest(args.start_date, args.end_date))


if __name__ == "__main__":
    main()
