"""
2025年A股交易日日历

根据2025年中国股市休市安排生成完整的交易日日历
"""

from datetime import datetime, timedelta
from typing import List, Set

# 2025年法定节假日休市安排
HOLIDAYS_2025 = {
    # 元旦: 1月1日(星期三)休市, 1月2日(星期四)起照常开市
    "2025-01-01": "元旦",

    # 春节: 1月28日(星期二)至2月4日(星期二)休市, 2月5日(星期三)起照常开市
    # 另外, 1月26日(星期日)、2月8日(星期六)为周末休市
    "2025-01-28": "春节",
    "2025-01-29": "春节",
    "2025-01-30": "春节",
    "2025-01-31": "春节",
    "2025-02-01": "春节",
    "2025-02-02": "春节",
    "2025-02-03": "春节",
    "2025-02-04": "春节",

    # 清明节: 4月4日(星期五)至4月6日(星期日)休市, 4月7日(星期一)起照常开市
    "2025-04-04": "清明节",
    "2025-04-05": "清明节",
    "2025-04-06": "清明节",

    # 劳动节: 5月1日(星期四)至5月5日(星期一)休市, 5月6日(星期二)起照常开市
    # 另外, 4月27日(星期日)为周末休市
    "2025-05-01": "劳动节",
    "2025-05-02": "劳动节",
    "2025-05-03": "劳动节",
    "2025-05-04": "劳动节",
    "2025-05-05": "劳动节",

    # 端午节: 5月31日(星期六)至6月2日(星期一)休市, 6月3日(星期二)起照常开市
    "2025-05-31": "端午节",
    "2025-06-01": "端午节",
    "2025-06-02": "端午节",

    # 国庆节、中秋节: 10月1日(星期三)至10月8日(星期三)休市, 10月9日(星期四)起照常开市
    # 另外, 9月28日(星期日)、10月11日(星期六)为周末休市
    "2025-10-01": "国庆节",
    "2025-10-02": "国庆节",
    "2025-10-03": "国庆节",
    "2025-10-04": "国庆节",
    "2025-10-05": "国庆节",
    "2025-10-06": "国庆节",
    "2025-10-07": "国庆节",
    "2025-10-08": "国庆节",
}


class TradingCalendar2025:
    """2025年股票交易日日历"""

    def __init__(self):
        self.holidays = HOLIDAYS_2025
        self.trading_days = self._generate_trading_days()

    def _generate_trading_days(self) -> Set[str]:
        """生成2025年所有交易日"""
        trading_days = set()

        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 12, 31)

        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")

            # 排除周末
            if current_date.weekday() >= 5:  # 5=周六, 6=周日
                current_date += timedelta(days=1)
                continue

            # 排除法定节假日
            if date_str in self.holidays:
                current_date += timedelta(days=1)
                continue

            # 是交易日
            trading_days.add(date_str)
            current_date += timedelta(days=1)

        return trading_days

    def is_trading_day(self, date: str) -> bool:
        """
        判断指定日期是否为交易日

        Args:
            date: 日期字符串, 格式 YYYY-MM-DD

        Returns:
            True: 是交易日
            False: 不是交易日(周末或节假日)
        """
        return date in self.trading_days

    def get_trading_days(self, start_date: str = None, end_date: str = None) -> List[str]:
        """
        获取指定日期范围内的所有交易日

        Args:
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD

        Returns:
            交易日列表(升序)
        """
        if not start_date:
            start_date = "2025-01-01"
        if not end_date:
            end_date = "2025-12-31"

        result = [
            date for date in self.trading_days
            if start_date <= date <= end_date
        ]

        return sorted(result)

    def get_previous_trading_day(self, date: str) -> str:
        """
        获取指定日期的前一个交易日

        Args:
            date: 日期字符串 YYYY-MM-DD

        Returns:
            前一个交易日, 如果没有则返回None
        """
        all_days = sorted(self.trading_days)

        try:
            idx = all_days.index(date)
            if idx > 0:
                return all_days[idx - 1]
        except ValueError:
            # 如果date不是交易日,找到最近的前一个交易日
            earlier_days = [d for d in all_days if d < date]
            if earlier_days:
                return earlier_days[-1]

        return None

    def get_next_trading_day(self, date: str) -> str:
        """
        获取指定日期的下一个交易日

        Args:
            date: 日期字符串 YYYY-MM-DD

        Returns:
            下一个交易日, 如果没有则返回None
        """
        all_days = sorted(self.trading_days)

        try:
            idx = all_days.index(date)
            if idx < len(all_days) - 1:
                return all_days[idx + 1]
        except ValueError:
            # 如果date不是交易日,找到最近的下一个交易日
            later_days = [d for d in all_days if d > date]
            if later_days:
                return later_days[0]

        return None

    def get_latest_trading_day(self, before_date: str = None) -> str:
        """
        获取最近的交易日(默认为今天或之前最近的交易日)

        Args:
            before_date: 基准日期 YYYY-MM-DD, 默认为今天

        Returns:
            最近的交易日
        """
        if not before_date:
            before_date = datetime.now().strftime("%Y-%m-%d")

        # 如果基准日期本身是交易日,直接返回
        if before_date in self.trading_days:
            return before_date

        # 否则找最近的前一个交易日
        earlier_days = [d for d in self.trading_days if d < before_date]
        if earlier_days:
            return sorted(earlier_days)[-1]

        return None

    def get_day_info(self, date: str) -> dict:
        """
        获取指定日期的详细信息

        Args:
            date: 日期字符串 YYYY-MM-DD

        Returns:
            日期信息字典
        """
        dt = datetime.strptime(date, "%Y-%m-%d")
        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        info = {
            "date": date,
            "weekday": weekday_names[dt.weekday()],
            "is_weekend": dt.weekday() >= 5,
            "is_holiday": date in self.holidays,
            "holiday_name": self.holidays.get(date),
            "is_trading_day": date in self.trading_days,
        }

        return info


# 全局单例
_calendar = None

def get_calendar() -> TradingCalendar2025:
    """获取交易日日历单例"""
    global _calendar
    if _calendar is None:
        _calendar = TradingCalendar2025()
    return _calendar


if __name__ == "__main__":
    # 测试代码
    calendar = get_calendar()

    print("=== 2025年A股交易日日历 ===\n")

    # 1. 统计信息
    all_trading_days = calendar.get_trading_days()
    print(f"1. 全年交易日统计:")
    print(f"   总交易日: {len(all_trading_days)}天")
    print(f"   首个交易日: {all_trading_days[0]}")
    print(f"   最后交易日: {all_trading_days[-1]}")

    # 2. 节假日信息
    print(f"\n2. 节假日休市安排:")
    holidays_by_name = {}
    for date, name in HOLIDAYS_2025.items():
        if name not in holidays_by_name:
            holidays_by_name[name] = []
        holidays_by_name[name].append(date)

    for name, dates in sorted(holidays_by_name.items()):
        dates_sorted = sorted(dates)
        print(f"   {name}: {dates_sorted[0]} ~ {dates_sorted[-1]} ({len(dates)}天)")

    # 3. 测试一些特殊日期
    print(f"\n3. 特殊日期测试:")
    test_dates = [
        "2025-01-01",  # 元旦
        "2025-01-02",  # 元旦后首个交易日
        "2025-10-01",  # 国庆节第一天
        "2025-10-08",  # 国庆节最后一天
        "2025-10-09",  # 国庆后首个交易日
        "2025-12-31",  # 年末
    ]

    for date in test_dates:
        info = calendar.get_day_info(date)
        status = "✅ 交易日" if info["is_trading_day"] else f"❌ 休市({info.get('holiday_name') or '周末'})"
        print(f"   {date} ({info['weekday']}): {status}")

    # 4. 测试前后交易日查询
    print(f"\n4. 交易日查询测试:")
    test_date = "2025-10-08"
    prev_day = calendar.get_previous_trading_day(test_date)
    next_day = calendar.get_next_trading_day(test_date)
    print(f"   {test_date} 的前一个交易日: {prev_day}")
    print(f"   {test_date} 的后一个交易日: {next_day}")

    # 5. 获取近60个交易日
    print(f"\n5. 近60个交易日测试:")
    latest = calendar.get_latest_trading_day("2025-12-11")
    print(f"   基准日期: 2025-12-11")
    print(f"   最近交易日: {latest}")

    # 从最近交易日往前数60个交易日
    all_days = sorted(calendar.get_trading_days())
    latest_idx = all_days.index(latest)
    start_idx = max(0, latest_idx - 59)  # 包含当天共60天
    recent_60 = all_days[start_idx:latest_idx + 1]
    print(f"   近60个交易日: {recent_60[0]} ~ {recent_60[-1]} (共{len(recent_60)}天)")

    print("\n✅ 测试完成!")
