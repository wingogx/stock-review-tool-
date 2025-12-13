"""
交易日期工具模块
提供获取最近交易日的函数，避免使用系统当前时间导致的日期错误
使用2025年交易日日历确保准确性
"""

from datetime import datetime
from typing import Optional
from loguru import logger


def get_latest_trading_date() -> str:
    """
    获取最近的交易日期（使用2025年交易日日历）

    逻辑:
    1. 优先使用2025年交易日日历计算最近交易日
    2. 从数据库获取已有数据的最新日期作为辅助验证
    3. 如果日历不可用，回退到数据库日期
    4. 最后回退到系统当前日期

    Returns:
        最近交易日期 YYYY-MM-DD

    使用场景:
    - 在非交易日（周末/节假日）运行采集器时，自动获取上一个交易日的日期
    - 确保数据库中保存的是实际的交易日期，而不是系统当前日期
    """
    # 方法1: 使用2025年交易日日历（最准确）
    try:
        import sys
        import os
        # 添加backend目录到path
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)

        from trading_calendar_2025 import get_calendar
        calendar = get_calendar()

        current_date = datetime.now().strftime("%Y-%m-%d")
        latest_trading_day = calendar.get_latest_trading_day(current_date)

        if latest_trading_day:
            logger.debug(f"从交易日日历获取最近交易日: {latest_trading_day}")
            return latest_trading_day

    except Exception as e:
        logger.debug(f"交易日日历获取失败: {e}")

    # 方法2: 从数据库获取最新日期（备用）
    latest_dates = []
    try:
        from app.utils.supabase_client import get_supabase
        supabase = get_supabase()

        # 检查多个表的最新日期
        tables_to_check = ['hot_concepts', 'market_sentiment', 'limit_stocks_detail', 'market_index']
        for table in tables_to_check:
            try:
                result = supabase.table(table).select('trade_date').order('trade_date', desc=True).limit(1).execute()
                if result.data:
                    db_date = result.data[0]['trade_date']
                    latest_dates.append(db_date)
                    logger.debug(f"从 {table} 表获取最新日期: {db_date}")
            except Exception as e:
                logger.debug(f"从 {table} 表获取日期失败: {e}")

        if latest_dates:
            latest_date = max(latest_dates)
            logger.debug(f"从数据库获取最近交易日: {latest_date}")
            return latest_date

    except Exception as e:
        logger.debug(f"数据库查询失败: {e}")

    # 回退方案：使用系统当前日期
    fallback_date = datetime.now().strftime("%Y-%m-%d")
    logger.warning(f"所有数据源都失败，使用系统当前日期: {fallback_date}")
    return fallback_date


def get_previous_trading_date(current_date: str) -> Optional[str]:
    """
    获取指定日期的前一个交易日

    Args:
        current_date: 当前日期 YYYY-MM-DD

    Returns:
        前一个交易日期 YYYY-MM-DD，失败返回 None
    """
    # 方法1: 使用交易日日历
    try:
        import sys
        import os
        # 添加backend目录到path
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)

        from trading_calendar_2025 import get_calendar
        calendar = get_calendar()

        previous_day = calendar.get_previous_trading_day(current_date)
        if previous_day:
            logger.debug(f"从交易日日历获取前一交易日: {current_date} -> {previous_day}")
            return previous_day

    except Exception as e:
        logger.debug(f"交易日日历获取失败: {e}")

    # 方法2: 从数据库查询前一个交易日
    try:
        from app.utils.supabase_client import get_supabase
        supabase = get_supabase()

        # 从limit_stocks_detail表查询小于当前日期的最大日期
        result = supabase.table('limit_stocks_detail')\
            .select('trade_date')\
            .lt('trade_date', current_date)\
            .order('trade_date', desc=True)\
            .limit(1)\
            .execute()

        if result.data and len(result.data) > 0:
            previous_date = result.data[0]['trade_date']
            logger.debug(f"从数据库获取前一交易日: {current_date} -> {previous_date}")
            return previous_date

    except Exception as e:
        logger.debug(f"数据库查询前一交易日失败: {e}")

    logger.warning(f"无法获取 {current_date} 的前一交易日")
    return None


def format_date_for_akshare(date_str: str) -> str:
    """
    将日期格式化为AKShare API所需的格式（YYYYMMDD）

    Args:
        date_str: 日期字符串 YYYY-MM-DD

    Returns:
        格式化后的日期 YYYYMMDD
    """
    return date_str.replace("-", "")


def format_date_from_akshare(date_str: str) -> str:
    """
    将AKShare API返回的日期格式化为标准格式（YYYY-MM-DD）

    Args:
        date_str: AKShare日期字符串 YYYYMMDD

    Returns:
        标准日期格式 YYYY-MM-DD
    """
    if len(date_str) == 8:
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    return date_str
