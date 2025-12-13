#!/usr/bin/env python3
"""
测试回测API功能
"""
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

# 加载环境变量
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from app.services.backtest_service import BacktestService

async def test_backtest():
    """测试回测功能"""

    print("=" * 70)
    print("🧪 回测功能测试")
    print("=" * 70)

    service = BacktestService()

    # 1. 检查表是否存在
    print("\n1️⃣ 检查数据库表...")
    try:
        response = service.supabase.table("premium_score_backtest")\
            .select("count", count="exact")\
            .limit(0)\
            .execute()

        print(f"✅ 表 premium_score_backtest 已存在")
        print(f"   当前记录数: {response.count if hasattr(response, 'count') else 0}")

    except Exception as e:
        print(f"❌ 表不存在: {e}")
        print("\n" + "=" * 70)
        print("⚠️  请先在 Supabase Dashboard > SQL Editor 中执行:")
        print("   database/create-backtest-table.sql")
        print("=" * 70)
        return

    # 2. 测试保存单个回测记录
    print("\n2️⃣ 测试保存回测记录...")
    test_stock_code = "300937"  # 再升科技
    test_date = "2024-12-11"
    next_date = "2024-12-12"

    print(f"   股票: {test_stock_code} ({test_date})")

    try:
        success = await service.save_backtest_record(
            stock_code=test_stock_code,
            trade_date=test_date,
            next_trade_date=next_date
        )

        if success:
            print("✅ 保存成功")
        else:
            print("❌ 保存失败（可能是数据不存在）")

    except Exception as e:
        print(f"❌ 保存出错: {e}")
        import traceback
        traceback.print_exc()

    # 3. 测试查询回测结果
    print("\n3️⃣ 测试查询回测结果...")
    try:
        results = service.query_backtest_results(
            start_date="2024-12-01",
            end_date="2024-12-31",
            limit=10
        )

        print(f"✅ 查询成功，找到 {len(results)} 条记录")
        if results:
            print("\n最近的回测记录:")
            for r in results[:3]:
                print(f"   {r['stock_code']} {r['stock_name']} ({r['trade_date']})")
                print(f"   评分: {r['total_score']:.2f} 等级: {r['premium_level']}")
                if r.get('next_day_change_pct') is not None:
                    print(f"   次日涨跌: {r['next_day_change_pct']:+.2f}%")
                print()

    except Exception as e:
        print(f"❌ 查询出错: {e}")

    # 4. 测试统计数据
    print("\n4️⃣ 测试统计数据...")
    try:
        stats = service.get_backtest_statistics()

        print(f"✅ 统计成功")
        print(f"   总记录数: {stats.get('total', 0)}")

        if stats.get('overall'):
            overall = stats['overall']
            print(f"   平均次日涨幅: {overall.get('avg_next_day_pct', 0):.2f}%")
            print(f"   盈利率: {overall.get('profitable_rate', 0):.2f}%")
            print(f"   预测准确率: {overall.get('prediction_accuracy', 0):.2f}%")

        if stats.get('by_level'):
            print("\n   各等级表现:")
            for level, data in stats['by_level'].items():
                print(f"   {level}: 平均涨幅 {data['avg_next_day_pct']:+.2f}% " +
                      f"盈利率 {data['profitable_rate']:.1f}% " +
                      f"准确率 {data['prediction_accuracy']:.1f}%")

    except Exception as e:
        print(f"❌ 统计出错: {e}")

    print("\n" + "=" * 70)
    print("✅ 测试完成")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_backtest())
