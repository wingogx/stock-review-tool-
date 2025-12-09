/**
 * 市场数据 API
 */

import { apiClient } from '../api-client';
import type {
  MarketIndexResponse,
  MarketSentimentResponse,
  MarketStatsResponse,
} from '@/types/api';

/**
 * 获取大盘指数数据
 */
export async function getMarketIndex(tradeDate?: string): Promise<MarketIndexResponse> {
  const params = tradeDate ? { trade_date: tradeDate } : {};
  const response = await apiClient.get<MarketIndexResponse>('/api/market/index', { params });
  return response.data;
}

/**
 * 获取市场情绪数据
 */
export async function getMarketSentiment(tradeDate?: string): Promise<MarketSentimentResponse> {
  const params = tradeDate ? { trade_date: tradeDate } : {};
  const response = await apiClient.get<MarketSentimentResponse>('/api/market/sentiment', { params });
  return response.data;
}

/**
 * 获取市场统计数据
 */
export async function getMarketStats(tradeDate?: string): Promise<MarketStatsResponse> {
  const params = tradeDate ? { trade_date: tradeDate } : {};
  const response = await apiClient.get<MarketStatsResponse>('/api/market/stats', { params });
  return response.data;
}
