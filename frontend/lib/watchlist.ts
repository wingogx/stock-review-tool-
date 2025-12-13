/**
 * 自选池数据管理工具
 * 使用 localStorage 存储用户选择的股票
 */

export interface WatchlistStock {
  stock_code: string;
  stock_name: string;
  continuous_days: number;
  change_pct?: number;
  close_price?: number;
  circulation_market_cap?: number;
  turnover_rate?: number;
  sealed_amount?: number;
  main_net_inflow?: number;
  first_limit_time?: string;
  opening_times?: number;
  limit_stats?: string;
  is_strong_limit?: boolean;
  trade_date: string;
  added_at: string; // 添加到自选池的时间
}

const STORAGE_KEY = 'stock_watchlist';

/**
 * 获取自选池列表
 */
export function getWatchlist(): WatchlistStock[] {
  if (typeof window === 'undefined') return [];

  try {
    const data = localStorage.getItem(STORAGE_KEY);
    return data ? JSON.parse(data) : [];
  } catch (error) {
    console.error('读取自选池失败:', error);
    return [];
  }
}

/**
 * 添加股票到自选池
 */
export function addToWatchlist(stock: Omit<WatchlistStock, 'added_at'>): boolean {
  try {
    const watchlist = getWatchlist();

    // 检查是否已存在（相同股票代码和交易日期）
    const exists = watchlist.some(
      (s) => s.stock_code === stock.stock_code && s.trade_date === stock.trade_date
    );

    if (exists) {
      return false; // 已存在，不重复添加
    }

    // 添加到列表开头
    const newStock: WatchlistStock = {
      ...stock,
      added_at: new Date().toISOString(),
    };

    watchlist.unshift(newStock);

    // 限制最多存储100只股票
    if (watchlist.length > 100) {
      watchlist.length = 100;
    }

    localStorage.setItem(STORAGE_KEY, JSON.stringify(watchlist));
    return true;
  } catch (error) {
    console.error('添加到自选池失败:', error);
    return false;
  }
}

/**
 * 从自选池移除股票
 */
export function removeFromWatchlist(stockCode: string, tradeDate: string): boolean {
  try {
    const watchlist = getWatchlist();
    const filtered = watchlist.filter(
      (s) => !(s.stock_code === stockCode && s.trade_date === tradeDate)
    );

    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
    return true;
  } catch (error) {
    console.error('从自选池移除失败:', error);
    return false;
  }
}

/**
 * 清空自选池
 */
export function clearWatchlist(): boolean {
  try {
    localStorage.removeItem(STORAGE_KEY);
    return true;
  } catch (error) {
    console.error('清空自选池失败:', error);
    return false;
  }
}

/**
 * 检查股票是否在自选池中
 */
export function isInWatchlist(stockCode: string, tradeDate: string): boolean {
  const watchlist = getWatchlist();
  return watchlist.some(
    (s) => s.stock_code === stockCode && s.trade_date === tradeDate
  );
}
