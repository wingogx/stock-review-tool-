#!/usr/bin/env python3
"""
使用真实数据测试回测功能
"""
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta

# 加载环境变量
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from app.services.backtest_service import BacktestService
from app.utils.supabase_client import get_supabase

async def main():
    """主函数"""
    print("=" * 70)
    print("🧪 使用真实数据测试回测功能")
    print("=" * 70)

    supabase = get_supabase()
    service = BacktestService()

    # 1. 查询最近的涨停股日期
    print("\n1️⃣ 查询最近的涨停股数据...")
    response = supabase.table("limit_stocks_detail")\
        .select("trade_date")\
        .eq("limit_type", "limit_up")\
        .order("trade_date", desc=True)\
        .limit(10)\
        .execute()

    if not response.data:
        print("❌ 没有找到涨停股数据")
        return

    # 获取所有不同的日期
    dates = sorted(set(r['trade_date'] for r in response.data), reverse=True)
    print(f"✅ 找到 {len(dates)} 个交易日:")
    for date in dates[:5]:
        # 统计每天的涨停股数量
        count_resp = supabase.table("limit_stocks_detail")\
            .select("count", count="exact")\
            .eq("trade_date", date)\
            .eq("limit_type", "limit_up")\
            .execute()
        count = count_resp.count if hasattr(count_resp, 'count') else len(count_resp.data)
        print(f"   {date}: {count} 只涨停股")

    # 2. 选择一个日期进行测试
    test_date = dates[0] if dates else None
    if not test_date:
        print("❌ 没有可用的测试日期")
        return

    print(f"\n2️⃣ 使用日期 {test_date} 进行测试...")

    # 获取这一天的前3只涨停股
    stocks_resp = supabase.table("limit_stocks_detail")\
        .select("stock_code, stock_name, continuous_days")\
        .eq("trade_date", test_date)\
        .eq("limit_type", "limit_up")\
        .order("continuous_days", desc=True)\
        .limit(3)\
        .execute()

    stocks = stocks_resp.data
    print(f"✅ 选择前3只股票进行测试:")
    for stock in stocks:
        print(f"   {stock['stock_code']} {stock['stock_name']} ({stock['continuous_days']}板)")

    # 3. 计算次日日期（简单+1天，实际应该查交易日历）
    from datetime import datetime, timedelta
    test_dt = datetime.strptime(test_date, "%Y-%m-%d")
    next_dt = test_dt + timedelta(days=1)
    next_date = next_dt.strftime("%Y-%m-%d")

    print(f"\n3️⃣ 保存回测记录（次日: {next_date}）...")

    success_count = 0
    for stock in stocks:
        try:
            success = await service.save_backtest_record(
                stock_code=stock['stock_code'],
                trade_date=test_date,
                next_trade_date=next_date
            )

            if success:
                success_count += 1
                print(f"✅ {stock['stock_code']} {stock['stock_name']} 保存成功")
            else:
                print(f"⚠️  {stock['stock_code']} {stock['stock_name']} 保存失败")

        except Exception as e:
            print(f"❌ {stock['stock_code']} {stock['stock_name']} 出错: {e}")

    print(f"\n成功保存 {success_count}/{len(stocks)} 条记录")

    # 4. 查询保存的记录
    print(f"\n4️⃣ 查询回测结果...")
    results = service.query_backtest_results(
        start_date=test_date,
        end_date=test_date,
        limit=10
    )

    if results:
        print(f"✅ 找到 {len(results)} 条记录:\n")
        for r in results:
            print(f"📊 {r['stock_code']} {r['stock_name']} ({r['continuous_days']}板)")
            print(f"   评分: {r['total_score']:.2f} 等级: {r['premium_level']}")
            print(f"   技术: {r['technical_score']:.2f} | 资金: {r['capital_score']:.2f} | " +
                  f"题材: {r['theme_score']:.2f} | 位置: {r['position_score']:.2f} | " +
                  f"市场: {r['market_score']:.2f}")

            if r.get('next_day_change_pct') is not None:
                pct = r['next_day_change_pct']
                emoji = "🔴" if pct > 0 else "🟢" if pct < 0 else "⚪"
                print(f"   次日表现: {emoji} {pct:+.2f}% " +
                      f"({'涨停' if r.get('is_next_day_limit_up') else ''})" +
                      f"({'跌停' if r.get('is_next_day_limit_down') else ''})")
                print(f"   预测结果: {r.get('prediction_result', 'unknown')}")
            else:
                print(f"   次日表现: 暂无数据")
            print()

    # 5. 获取统计数据
    print(f"\n5️⃣ 统计分析...")
    stats = service.get_backtest_statistics(trade_date=test_date)

    if stats.get('total', 0) > 0:
        print(f"✅ 统计数据:")
        print(f"   总记录数: {stats['total']}")

        if stats.get('overall'):
            overall = stats['overall']
            print(f"\n   整体表现:")
            print(f"   - 平均次日涨幅: {overall.get('avg_next_day_pct', 0):+.2f}%")
            print(f"   - 盈利率: {overall.get('profitable_rate', 0):.2f}%")
            print(f"   - 涨停数: {overall.get('limit_up_count', 0)} ({overall.get('limit_up_rate', 0):.2f}%)")
            print(f"   - 预测准确率: {overall.get('prediction_accuracy', 0):.2f}%")

        if stats.get('by_level'):
            print(f"\n   各等级表现:")
            for level, data in sorted(stats['by_level'].items()):
                print(f"   {level} ({data['count']}只):")
                print(f"     平均涨幅: {data['avg_next_day_pct']:+.2f}% | " +
                      f"盈利率: {data['profitable_rate']:.1f}% | " +
                      f"准确率: {data['prediction_accuracy']:.1f}%")

    print("\n" + "=" * 70)
    print("✅ 测试完成")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
