/**
 * 概念板块 API
 */

import { apiClient } from '../api-client';
import type {
  HotConceptsResponse,
  ConceptStocksResponse,
  ConceptDetailResponse,
} from '@/types/api';

export interface GetHotConceptsParams {
  trade_date?: string;
  top_n?: number;
  order_by?: 'change_pct' | 'concept_strength' | 'rank';
}

/**
 * 获取热门概念板块
 */
export async function getHotConcepts(params?: GetHotConceptsParams): Promise<HotConceptsResponse> {
  const response = await apiClient.get<HotConceptsResponse>('/api/concepts/hot', { params });
  return response.data;
}

/**
 * 获取概念成分股
 */
export async function getConceptStocks(
  conceptName: string,
  tradeDate?: string,
  limit?: number
): Promise<ConceptStocksResponse> {
  const params: any = {};
  if (tradeDate) params.trade_date = tradeDate;
  if (limit) params.limit = limit;

  const response = await apiClient.get<ConceptStocksResponse>(
    `/api/concepts/stocks/${encodeURIComponent(conceptName)}`,
    { params }
  );
  return response.data;
}

/**
 * 获取概念详情
 */
export async function getConceptDetail(
  conceptName: string,
  tradeDate?: string
): Promise<ConceptDetailResponse> {
  const params = tradeDate ? { trade_date: tradeDate } : {};
  const response = await apiClient.get<ConceptDetailResponse>(
    `/api/concepts/detail/${encodeURIComponent(conceptName)}`,
    { params }
  );
  return response.data;
}

/**
 * 搜索概念板块
 */
export async function searchConcepts(
  query: string,
  tradeDate?: string,
  limit?: number
): Promise<HotConceptsResponse> {
  const params: any = { q: query };
  if (tradeDate) params.trade_date = tradeDate;
  if (limit) params.limit = limit;

  const response = await apiClient.get<HotConceptsResponse>('/api/concepts/search', { params });
  return response.data;
}
