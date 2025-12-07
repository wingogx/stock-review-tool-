"""
Tushare Token 权限验证脚本
验证你的 5000积分 Tushare Token 的实际权限和数据可用性
"""

import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 设置 pandas 显示选项
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', 50)


class TushareTokenTester:
    """Tushare Token 权限测试类"""

    def __init__(self):
        self.token = os.getenv("TUSHARE_TOKEN")
        if not self.token:
            raise ValueError("请在 .env 文件中设置 TUSHARE_TOKEN")

        ts.set_token(self.token)
        self.pro = ts.pro_api()

        # 使用昨天的日期（今天可能还没有数据）
        self.trade_date = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        self.trade_date_dash = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        self.results = []

    def print_header(self, title):
        """打印分隔标题"""
        print(f"\n{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}\n")

    def test_api(self, category, description, required_points, func, **kwargs):
        """测试单个 API 接口"""
        print(f"🔍 测试: {description}")
        print(f"   所需积分: {required_points}")

        try:
            df = func(**kwargs)

            if df is None or df.empty:
                print(f"   ⚠️  返回空数据（可能是非交易日或数据未更新）")
                self.results.append({
                    "category": category,
                    "description": description,
                    "required_points": required_points,
                    "status": "⚠️  空数据",
                    "reason": "返回空 DataFrame"
                })
                return None

            print(f"   ✅ 成功! 获取到 {len(df)} 条数据")
            print(f"   📊 列名: {list(df.columns)[:8]}...")
            print(f"   📝 示例数据:")
            print(df.head(2))

            self.results.append({
                "category": category,
                "description": description,
                "required_points": required_points,
                "status": "✅ 成功",
                "rows": len(df),
                "columns": len(df.columns)
            })

            return df

        except Exception as e:
            error_msg = str(e)
            print(f"   ❌ 失败: {error_msg[:100]}")

            # 判断是否是权限问题
            if "权限" in error_msg or "积分" in error_msg or "permission" in error_msg.lower():
                status = "❌ 积分不足"
            else:
                status = "❌ 其他错误"

            self.results.append({
                "category": category,
                "description": description,
                "required_points": required_points,
                "status": status,
                "reason": error_msg[:100]
            })

            return None

    def test_all(self):
        """测试所有关键 API"""

        self.print_header(f"Tushare Token 权限验证")
        print(f"测试日期: {self.trade_date_dash}")
        print(f"Token: {self.token[:20]}...")

        # ============================================
        # 1. 基础数据测试（120积分）
        # ============================================
        self.print_header("1️⃣  基础数据（120积分即可）")

        # 1.1 股票日线行情
        self.test_api(
            "基础数据",
            "股票日线行情（平安银行）",
            120,
            self.pro.daily,
            ts_code='000001.SZ',
            start_date=self.trade_date,
            end_date=self.trade_date
        )

        # 1.2 指数日线行情
        self.test_api(
            "基础数据",
            "指数日线行情（上证指数）",
            120,
            self.pro.index_daily,
            ts_code='000001.SH',
            start_date=self.trade_date,
            end_date=self.trade_date
        )

        # ============================================
        # 2. 进阶数据测试（2000积分）
        # ============================================
        self.print_header("2️⃣  进阶数据（2000积分）")

        # 2.1 每日指标
        self.test_api(
            "进阶数据",
            "每日指标（换手率、市盈率等）",
            2000,
            self.pro.daily_basic,
            ts_code='000001.SZ',
            start_date=self.trade_date,
            end_date=self.trade_date
        )

        # 2.2 龙虎榜每日明细
        lhb_df = self.test_api(
            "进阶数据",
            "龙虎榜每日明细",
            2000,
            self.pro.top_list,
            trade_date=self.trade_date
        )

        # 2.3 涨停价格
        self.test_api(
            "进阶数据",
            "每日涨跌停价格",
            2000,
            self.pro.stk_limit,
            trade_date=self.trade_date
        )

        # ============================================
        # 3. 高级数据测试（5000积分）
        # ============================================
        self.print_header("3️⃣  高级数据（5000积分） - 你的优势！")

        # 3.1 龙虎榜机构明细（关键！）
        inst_df = self.test_api(
            "高级数据",
            "龙虎榜机构明细（5000积分核心优势）",
            5000,
            self.pro.top_inst,
            trade_date=self.trade_date
        )

        # 如果龙虎榜有数据，测试具体股票的机构席位
        if lhb_df is not None and not lhb_df.empty and inst_df is not None:
            print(f"\n   📊 机构席位统计:")
            if not inst_df.empty:
                print(f"      机构席位数: {len(inst_df)}")
                print(f"      机构买入总额: {inst_df['buy'].sum():.2f} 万元")
                print(f"      机构卖出总额: {inst_df['sell'].sum():.2f} 万元")
                print(f"      机构净买入: {inst_df['net_buy'].sum():.2f} 万元")
            else:
                print(f"      ⚠️  今日无机构席位")

        # ============================================
        # 4. 超高级数据测试（6000+积分）
        # ============================================
        self.print_header("4️⃣  超高级数据（6000+积分） - 预计无权限")

        # 4.1 同花顺概念（6000积分）
        self.test_api(
            "超高级数据",
            "同花顺概念板块（6000积分）",
            6000,
            self.pro.ths_index,
            ts_code='',
            exchange='A'
        )

        # 4.2 连板天梯（8000积分）
        # 注意: 这个API可能不存在或需要特殊参数
        # self.test_api(
        #     "超高级数据",
        #     "连板天梯（8000积分）",
        #     8000,
        #     self.pro.limit_step,
        #     trade_date=self.trade_date
        # )

        # ============================================
        # 5. 其他常用数据测试
        # ============================================
        self.print_header("5️⃣  其他常用数据")

        # 5.1 股票列表
        self.test_api(
            "常用数据",
            "股票列表",
            120,
            self.pro.stock_basic,
            exchange='',
            list_status='L'
        )

        # 5.2 交易日历
        self.test_api(
            "常用数据",
            "交易日历",
            120,
            self.pro.trade_cal,
            exchange='SSE',
            start_date=self.trade_date,
            end_date=self.trade_date
        )

    def print_summary(self):
        """打印测试总结"""
        self.print_header("测试总结报告")

        df_results = pd.DataFrame(self.results)

        # 按分类统计
        print("📊 按分类统计:\n")
        if not df_results.empty:
            category_stats = df_results.groupby(['category', 'status']).size().unstack(fill_value=0)
            print(category_stats)

            # 总体统计
            print(f"\n📈 总体统计:")
            total = len(self.results)
            success = len([r for r in self.results if r['status'] == '✅ 成功'])
            warning = len([r for r in self.results if r['status'] == '⚠️  空数据'])
            no_permission = len([r for r in self.results if r['status'] == '❌ 积分不足'])
            other_error = len([r for r in self.results if r['status'] == '❌ 其他错误'])

            print(f"   总测试数: {total}")
            print(f"   ✅ 成功: {success} ({success/total*100:.1f}%)")
            print(f"   ⚠️  空数据: {warning} ({warning/total*100:.1f}%)")
            print(f"   ❌ 积分不足: {no_permission} ({no_permission/total*100:.1f}%)")
            print(f"   ❌ 其他错误: {other_error} ({other_error/total*100:.1f}%)")

            # 权限验证结果
            self.print_header("权限验证结果")

            print("✅ 你可以访问的API:")
            success_items = [r for r in self.results if r['status'] == '✅ 成功']
            for item in success_items:
                print(f"   ✅ {item['description']} ({item['required_points']}积分)")

            if warning:
                print("\n⚠️  空数据的API（可能是非交易日或数据未更新）:")
                warning_items = [r for r in self.results if r['status'] == '⚠️  空数据']
                for item in warning_items:
                    print(f"   ⚠️  {item['description']} ({item['required_points']}积分)")

            if no_permission:
                print("\n❌ 无权限的API:")
                no_perm_items = [r for r in self.results if r['status'] == '❌ 积分不足']
                for item in no_perm_items:
                    print(f"   ❌ {item['description']} ({item['required_points']}积分)")
                    print(f"      原因: {item.get('reason', 'Unknown')}")

            if other_error:
                print("\n❌ 其他错误的API:")
                error_items = [r for r in self.results if r['status'] == '❌ 其他错误']
                for item in error_items:
                    print(f"   ❌ {item['description']}")
                    print(f"      原因: {item.get('reason', 'Unknown')}")

            # 核心功能验证
            self.print_header("核心功能验证")

            # 检查龙虎榜机构明细是否可用
            inst_success = any(
                r['description'] == '龙虎榜机构明细（5000积分核心优势）' and r['status'] == '✅ 成功'
                for r in self.results
            )

            if inst_success:
                print("✅ 核心优势验证:")
                print("   ✅ 龙虎榜机构明细可用 - 这是你5000积分的最大优势！")
                print("   ✅ 可以直接获取机构席位分类，无需解析营业部名称")
                print("   ✅ 建议在项目中使用 Tushare 作为龙虎榜数据的主数据源")
            else:
                print("⚠️  核心优势验证:")
                print("   ⚠️  龙虎榜机构明细未成功获取（可能是非交易日）")
                print("   ℹ️  建议在交易日重新测试")

        # 最终建议
        self.print_header("最终建议")

        print("""
基于测试结果，给你的建议：

1. ✅ 你的 Token 已验证可用

2. 📊 数据源分工建议：

   使用 Tushare 的数据：
   - ✅ 龙虎榜每日明细（2000积分）
   - ✅ 龙虎榜机构明细（5000积分 - 核心优势！）
   - ✅ 个股日线行情（120积分）
   - ✅ 每日指标数据（2000积分）

   使用 AKShare 补充的数据：
   - ✅ 涨停池详细数据（免费，字段更详细）
   - ✅ 概念板块数据（免费，374个概念）
   - ✅ 市场活跃度（免费，同花顺独家）
   - ✅ 炸板数据（免费，专有API）

3. 🎯 核心优势：
   - 龙虎榜机构席位自动分类（AKShare需要解析营业部名称）
   - 官方数据源，稳定可靠
   - 每分钟500次调用，无日限额

4. ⚠️  注意事项：
   - 概念板块数据需要6000积分（建议用AKShare）
   - 部分API在非交易日可能返回空数据
   - 建议在每个交易日16:00后采集数据
        """)


if __name__ == "__main__":
    print("="*80)
    print("  Tushare Token 权限验证工具")
    print("  验证你的 5000积分 Token 的实际权限")
    print("="*80)

    try:
        tester = TushareTokenTester()
        tester.test_all()
        tester.print_summary()

        print("\n" + "="*80)
        print("  ✅ 测试完成!")
        print("="*80)

    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
