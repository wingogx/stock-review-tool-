/**
 * 涨停池 API
 */

import { apiClient } from '../api-client';
import type {
  LimitStocksResponse,
  LimitStatsResponse,
  LimitStockItem,
} from '@/types/api';

export interface GetLimitStocksParams {
  trade_date?: string;
  limit_type?: 'limit_up' | 'limit_down';
  min_continuous_days?: number;
  continuous_days?: number;
  filter_st?: boolean;
  order_by?: 'continuous_days' | 'change_pct' | 'amount';
  page?: number;
  page_size?: number;
}

/**
 * 获取涨停/跌停股票列表
 */
export async function getLimitStocks(params?: GetLimitStocksParams): Promise<LimitStocksResponse> {
  const response = await apiClient.get<LimitStocksResponse>('/api/limit/stocks', { params });
  return response.data;
}

/**
 * 获取涨停统计数据
 */
export async function getLimitStats(tradeDate?: string): Promise<LimitStatsResponse> {
  const params = tradeDate ? { trade_date: tradeDate } : {};
  const response = await apiClient.get<LimitStatsResponse>('/api/limit/stats', { params });
  return response.data;
}

/**
 * 获取个股涨停详情
 */
export async function getStockLimitDetail(
  stockCode: string,
  tradeDate?: string
): Promise<LimitStockItem> {
  const params = tradeDate ? { trade_date: tradeDate } : {};
  const response = await apiClient.get<LimitStockItem>(`/api/limit/stock/${stockCode}`, { params });
  return response.data;
}
