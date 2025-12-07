"""
交易日期工具模块
提供获取最近交易日的函数，避免使用系统当前时间导致的日期错误
"""

import akshare as ak
import pandas as pd
from datetime import datetime
from typing import Optional
from loguru import logger


def get_latest_trading_date() -> str:
    """
    获取最近的交易日期（从AKShare API）

    逻辑:
    1. 使用上证指数历史数据获取最近交易日
    2. 取最后一条记录的日期作为最近交易日
    3. 如果失败，回退到系统当前日期

    Returns:
        最近交易日期 YYYY-MM-DD

    使用场景:
    - 在非交易日（周末/节假日）运行采集器时，自动获取上一个交易日的日期
    - 确保数据库中保存的是实际的交易日期，而不是系统当前日期
    """
    try:
        # 使用上证指数获取最近交易日
        # 只获取最近几天的数据即可
        df = ak.stock_zh_index_daily(symbol="sh000001")

        if df is not None and not df.empty:
            # 取最后一条记录的日期
            latest_date = pd.to_datetime(df['date'].iloc[-1]).strftime("%Y-%m-%d")
            logger.debug(f"从上证指数获取最近交易日: {latest_date}")
            return latest_date

    except Exception as e:
        logger.warning(f"获取最近交易日失败: {e}，使用系统当前日期")

    # 回退方案：使用系统当前日期
    fallback_date = datetime.now().strftime("%Y-%m-%d")
    logger.debug(f"使用系统当前日期作为交易日: {fallback_date}")
    return fallback_date


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
