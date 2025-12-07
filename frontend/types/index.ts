/**
 * 全局类型定义
 */

// 市场指数
export interface MarketIndex {
  trade_date: string;
  index_code: string;
  index_name: string;
  close_price: number;
  change_pct: number;
  volume?: number;
  amount?: number;
}

// 市场情绪
export interface MarketSentiment {
  trade_date: string;
  total_amount: number;
  up_count: number;
  down_count: number;
  up_down_ratio: number;
  limit_up_count: number;
  limit_down_count: number;
  explosion_rate?: number;
  continuous_limit_distribution?: Record<string, number>;
}

// 涨停股票
export interface LimitStock {
  stock_code: string;
  stock_name: string;
  limit_type: 'limit_up' | 'limit_down';
  change_pct: number;
  close_price: number;
  continuous_days?: number;
  opening_times?: number;
  first_limit_time?: string;
  concepts?: string[];
}

// 热门概念
export interface HotConcept {
  concept_name: string;
  change_pct: number;
  limit_up_count: number;
  up_count: number;
  total_count: number;
  leading_stocks?: Array<{
    code: string;
    name: string;
    change_pct: number;
  }>;
  rank?: number;
}
