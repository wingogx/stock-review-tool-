"""
回测12月11日涨停股票评分与次日表现
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import requests
import json

# 加载环境变量
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

sys.path.insert(0, str(Path(__file__).parent))

from app.utils.supabase_client import get_supabase

def main():
    supabase = get_supabase()

    print("=" * 80)
    print("回测分析：2025-12-11涨停股票评分 vs 2025-12-12实际表现")
    print("=" * 80)
    print()

    # 1. 查询12月11日涨停股票
    print("📊 获取2025-12-11涨停股票...")
    response = supabase.table("limit_stocks_detail")\
        .select("stock_code, stock_name, continuous_days")\
        .eq("trade_date", "2025-12-11")\
        .eq("limit_type", "limit_up")\
        .order("continuous_days", desc=True)\
        .execute()

    stocks_1211 = response.data
    print(f"   找到 {len(stocks_1211)} 只涨停股票")

    # 2. 查询12月12日涨跌幅
    print("📊 获取2025-12-12涨跌幅数据...")
    stock_codes = [s['stock_code'] for s in stocks_1211]

    response_1212 = supabase.table("limit_stocks_detail")\
        .select("stock_code, change_pct, limit_type")\
        .eq("trade_date", "2025-12-12")\
        .in_("stock_code", stock_codes)\
        .execute()

    stocks_1212_map = {s['stock_code']: s for s in response_1212.data}
    print(f"   12日有数据: {len(stocks_1212_map)} 只")
    print()

    # 3. 计算评分
    print("🔢 计算溢价评分...")
    print()
    results = []
    API_BASE = "http://localhost:8000"

    # 只处理前30只
    for i, stock in enumerate(stocks_1211[:30], 1):
        code = stock['stock_code']
        name = stock['stock_name']
        days = stock['continuous_days']

        try:
            # 调用评分API
            url = f"{API_BASE}/api/stock/premium-score?stock_code={code}&trade_date=2025-12-11"
            resp = requests.get(url, timeout=10)

            if not resp.ok:
                print(f"   [{i:2}/30] {name:10} - API失败")
                continue

            data = resp.json()['data']
            score = data['total_score']
            level = data['premium_level']

            # 获取次日涨跌幅
            s1212 = stocks_1212_map.get(code)
            next_pct = s1212['change_pct'] if s1212 else None
            is_limit_up = s1212.get('limit_type') == 'limit_up' if s1212 else False

            results.append({
                'code': code,
                'name': name,
                'days': days,
                'score': score,
                'level': level,
                'next_pct': next_pct,
                'is_limit_up': is_limit_up
            })

            # 显示进度
            pct_str = f"{next_pct:+6.2f}%" if next_pct is not None else "  N/A  "
            mark = "🔥涨停" if is_limit_up else ""
            print(f"   [{i:2}/30] {name:10} {days}板 | 评分 {score:5.2f} ({level:4}) | 次日 {pct_str} {mark}")

        except Exception as e:
            print(f"   [{i:2}/30] {name:10} - 错误: {str(e)[:40]}")

    print()
    print(f"✓ 完成 {len(results)} 只股票")
    print()

    # 4. 保存结果
    output_file = '/tmp/backtest_1211.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"结果已保存到: {output_file}")

    # 5. 统计分析
    print()
    print("=" * 80)
    print("统计分析")
    print("=" * 80)
    print()

    # 按评分分组
    score_groups = {
        '极高(≥8分)': [],
        '高(7~8分)': [],
        '偏高(6~7分)': [],
        '中性(5~6分)': [],
        '偏低(4~5分)': [],
        '低(<4分)': []
    }

    for r in results:
        if r['next_pct'] is None:
            continue

        score = r['score']
        if score >= 8:
            score_groups['极高(≥8分)'].append(r)
        elif score >= 7:
            score_groups['高(7~8分)'].append(r)
        elif score >= 6:
            score_groups['偏高(6~7分)'].append(r)
        elif score >= 5:
            score_groups['中性(5~6分)'].append(r)
        elif score >= 4:
            score_groups['偏低(4~5分)'].append(r)
        else:
            score_groups['低(<4分)'].append(r)

    # 打印统计
    print(f"{'评分等级':<15} | {'数量':>4} | {'平均涨幅':>8} | {'涨停个数':>8} | {'涨停率':>8}")
    print("-" * 80)

    for group_name, stocks in score_groups.items():
        if len(stocks) == 0:
            continue

        avg_pct = sum(s['next_pct'] for s in stocks) / len(stocks)
        limit_up_count = sum(1 for s in stocks if s['is_limit_up'])
        limit_up_rate = limit_up_count / len(stocks) * 100 if len(stocks) > 0 else 0

        print(f"{group_name:<15} | {len(stocks):4} | {avg_pct:+7.2f}% | {limit_up_count:8} | {limit_up_rate:7.1f}%")

    print()

if __name__ == "__main__":
    main()
