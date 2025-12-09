/**
 * API 响应类型定义
 * 对应后端 Pydantic Schemas
 */

// ============================================
// 市场数据类型
// ============================================

export interface MarketIndexItem {
  index_code: string;
  index_name: string;
  trade_date: string;
  open?: number;
  high?: number;
  low?: number;
  close?: number;
  change_pct?: number;
  volume?: number;
  amount?: number;
}

export interface MarketIndexResponse {
  success: boolean;
  data: MarketIndexItem[];
  total: number;
}

export interface MarketSentimentItem {
  trade_date: string;
  total_amount: number;
  total_amount_change?: number;
  total_amount_change_pct?: number;
  up_count: number;
  down_count: number;
  up_down_ratio: number;
  limit_up_count: number;
  limit_down_count: number;
  prev_limit_up_count?: number;
  prev_limit_down_count?: number;
  continuous_limit_distribution?: Record<string, number>;
  prev_continuous_limit_distribution?: Record<string, number>;
  prev2_continuous_limit_distribution?: Record<string, number>;
  explosion_rate: number;
  market_status: string;
}

export interface MarketSentimentResponse {
  success: boolean;
  data: MarketSentimentItem;
}

export interface MarketStatsItem {
  trade_date: string;
  total_amount: number;
  avg_turnover_rate: number;
  up_count: number;
  down_count: number;
  limit_up_count: number;
  limit_down_count: number;
}

export interface MarketStatsResponse {
  success: boolean;
  data: MarketStatsItem;
}

// ============================================
// 涨停池类型
// ============================================

export interface LimitStockItem {
  stock_code: string;
  stock_name: string;
  trade_date: string;
  limit_type: 'limit_up' | 'limit_down';
  change_pct: number;
  close_price: number;
  continuous_days: number;
  is_strong_limit: boolean;
  first_limit_time?: string;
  last_limit_time?: string;
  opening_times?: number;
  turnover_rate?: number;
  amount?: number;
  market_cap?: number;
  circulation_market_cap?: number;
  concepts?: string[];
  limit_reason?: string;
}

export interface LimitStocksResponse {
  success: boolean;
  data: LimitStockItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface LimitStatsItem {
  trade_date: string;
  limit_up_count: number;
  limit_down_count: number;
  continuous_distribution?: Record<string, number>;
  strong_limit_count: number;
  exploded_count: number;
  explosion_rate: number;
}

export interface LimitStatsResponse {
  success: boolean;
  data: LimitStatsItem;
}

// ============================================
// 概念板块类型
// ============================================

export interface HotConceptItem {
  concept_name: string;
  trade_date: string;
  day_change_pct?: number;
  change_pct: number;
  consecutive_days?: number;
  concept_strength?: number;
  rank?: number;
  is_new_concept?: boolean;
  first_seen_date?: string;
  limit_up_count?: number;
  total_count?: number;
  leader_stock_code?: string;
  leader_stock_name?: string;
  leader_continuous_days?: number;
  leader_change_pct?: number;
}

export interface HotConceptsResponse {
  success: boolean;
  data: HotConceptItem[];
  total: number;
}

export interface ConceptStockItem {
  stock_code: string;
  stock_name: string;
  change_pct: number;
  close_price?: number;
  turnover_rate?: number;
  amount?: number;
  is_limit_up: boolean;
  is_leader: boolean;
}

export interface ConceptStocksResponse {
  success: boolean;
  concept_name: string;
  data: ConceptStockItem[];
  total: number;
}

export interface ConceptDetailResponse {
  success: boolean;
  concept_name: string;
  trade_date: string;
  change_pct: number;
  concept_strength?: number;
  rank?: number;
  top_stocks: ConceptStockItem[];
}
