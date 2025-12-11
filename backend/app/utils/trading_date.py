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
    获取最近的交易日期（综合多数据源）

    逻辑:
    1. 从数据库获取已有数据的最新日期（最可靠）
    2. 从AKShare上证指数获取最近交易日
    3. 取两者中最新的日期
    4. 如果都失败，回退到系统当前日期

    Returns:
        最近交易日期 YYYY-MM-DD

    使用场景:
    - 在非交易日（周末/节假日）运行采集器时，自动获取上一个交易日的日期
    - 确保数据库中保存的是实际的交易日期，而不是系统当前日期
    """
    latest_dates = []

    # 方法1: 从数据库获取最新日期（优先）
    try:
        from app.utils.supabase_client import get_supabase
        supabase = get_supabase()

        # 检查多个表的最新日期
        tables_to_check = ['hot_concepts', 'market_sentiment', 'limit_stocks_detail']
        for table in tables_to_check:
            try:
                result = supabase.table(table).select('trade_date').order('trade_date', desc=True).limit(1).execute()
                if result.data:
                    db_date = result.data[0]['trade_date']
                    latest_dates.append(db_date)
                    logger.debug(f"从 {table} 表获取最新日期: {db_date}")
            except Exception as e:
                logger.debug(f"从 {table} 表获取日期失败: {e}")

    except Exception as e:
        logger.debug(f"数据库查询失败: {e}")

    # 方法2: 从AKShare获取最近交易日
    try:
        df = ak.stock_zh_index_daily(symbol="sh000001")

        if df is not None and not df.empty:
            akshare_date = pd.to_datetime(df['date'].iloc[-1]).strftime("%Y-%m-%d")
            latest_dates.append(akshare_date)
            logger.debug(f"从上证指数获取最近交易日: {akshare_date}")

    except Exception as e:
        logger.debug(f"AKShare获取交易日失败: {e}")

    # 取所有来源中最新的日期
    if latest_dates:
        latest_date = max(latest_dates)
        logger.debug(f"最终确定最近交易日: {latest_date}")
        return latest_date

    # 回退方案：使用系统当前日期
    fallback_date = datetime.now().strftime("%Y-%m-%d")
    logger.warning(f"所有数据源都失败，使用系统当前日期: {fallback_date}")
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
