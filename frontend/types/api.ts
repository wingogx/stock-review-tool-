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
  amount_change_pct?: number;
}

export interface MarketIndexResponse {
  success: boolean;
  data: MarketIndexItem[];
  total: number;
}

export interface SentimentScoreDetail {
  up_ratio_score: number;
  amount_change_score: number;
  limit_up_score: number;
  limit_down_score: number;
  explosion_rate_score: number;
  total_score: number;
  sentiment_level: string;
  sentiment_color: string;
}

export interface MarketSentimentItem {
  trade_date: string;
  total_amount: number;
  total_amount_change?: number;
  total_amount_change_pct?: number;
  up_count: number;
  down_count: number;
  up_down_ratio: number;
  prev_up_count?: number;
  prev_down_count?: number;
  limit_up_count: number;
  limit_down_count: number;
  prev_limit_up_count?: number;
  prev_limit_down_count?: number;
  prev_explosion_rate?: number;
  continuous_limit_distribution?: Record<string, number>;
  prev_continuous_limit_distribution?: Record<string, number>;
  prev2_continuous_limit_distribution?: Record<string, number>;
  explosion_rate: number;
  market_status: string;
  sentiment_score?: SentimentScoreDetail;
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
  limit_stats?: string;
  industry?: string;
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

// ============================================
// 板块分析类型
// ============================================

export interface TrendSectorItem {
  concept_name: string;
  day_change_pct?: number;      // 当日涨幅
  change_pct?: number;          // 5日涨幅
  leader_stock_name?: string;   // 龙头股名称
  leader_stock_code?: string;   // 龙头股代码
  leader_continuous_days?: number;  // 龙头股连板数
}

export interface EmotionSectorItem {
  concept_name: string;
  day_change_pct?: number;      // 当日涨幅
  limit_up_count?: number;      // 涨停数
  leader_stock_name?: string;   // 龙头股名称
  leader_stock_code?: string;   // 龙头股代码
  leader_continuous_days?: number;  // 龙头股连板数
}

export interface MainSectorItem {
  concept_name: string;
  consecutive_main_days: number; // 连续主线天数
  first_main_date?: string;     // 上榜首日
  day_change_pct?: number;      // 当日涨幅
  change_pct?: number;          // 5日涨幅
  limit_up_count?: number;      // 涨停数
  leader_stock_name?: string;   // 龙头股名称
  leader_stock_code?: string;   // 龙头股代码
  leader_continuous_days?: number;  // 龙头股连板数
}

export interface AnomalySectorItem {
  concept_name: string;
  day_change_pct?: number;      // 当日涨幅
  limit_up_count?: number;      // 涨停数
  leader_stock_name?: string;   // 龙头股名称
  leader_stock_code?: string;   // 龙头股代码
  leader_continuous_days?: number;  // 龙头股连板数
  anomaly_type: string;         // 异动类型: limit_up / change_pct
}

export interface SectorAnalysisData {
  trend_sectors: TrendSectorItem[];     // 趋势板块（5日涨幅前5）
  emotion_sectors: EmotionSectorItem[]; // 情绪板块（涨停数>10）
  main_sectors: MainSectorItem[];       // 主线板块（趋势∩情绪）
  anomaly_sectors: AnomalySectorItem[]; // 异动板块
}

export interface SectorAnalysisResponse {
  success: boolean;
  trade_date: string;
  data: SectorAnalysisData;
}

// ============================================
// 情绪分析类型
// ============================================

// 晋级率详情
export interface PromotionDetail {
  from_days: number;           // 从N板
  to_days: number;             // 到N+1板
  yesterday_count: number;     // 昨日N板数量
  today_count: number;         // 今日N+1板数量
  rate: number;                // 晋级率(%)
}

// 昨日涨停溢价统计
export interface PremiumStats {
  avg_premium?: number;                    // 整体溢价率(%)
  avg_open_premium?: number;               // 开盘溢价率(%)
  first_board_premium?: number;            // 首板溢价率(%)
  high_board_premium?: number;             // 高位板溢价率(%)
  big_loss_rate?: number;                  // 大面率(%)
  high_board_big_loss_rate?: number;       // 高位大面率(%)
}

// v2.3 情绪阶段判断详情
export interface StageDetails {
  factor_scores?: Record<string, number>;  // 各因子得分
  total_score?: number;                    // 总分
  had_recent_peak?: boolean;               // 最近是否有高峰
  is_deteriorating?: boolean;              // 是否恶化中
  stage_raw?: string;                      // v2.3: 原始阶段（不带惯性）
  used_inertia?: boolean;                  // v2.3: 是否使用了惯性
  previous_stage?: string;                 // v2.3: 昨日阶段
}

// 情绪周期仪表盘
export interface EmotionDashboard {
  space_height: number;                    // 空间板高度
  space_height_change?: number;            // 空间板高度变化
  limit_up_count: number;                  // 涨停数
  limit_up_change?: number;                // 涨停数变化
  explosion_rate: number;                  // 炸板率(%)
  explosion_rate_change?: number;          // 炸板率变化
  overall_promotion_rate?: number;         // 整体晋级率(%)
  promotion_details: PromotionDetail[];    // 分层晋级率
  emotion_stage: string;                   // 情绪阶段
  emotion_stage_color: string;             // 阶段颜色
  premium_stats?: PremiumStats;            // 昨日涨停溢价统计
  stage_details?: StageDetails;            // v2.0 情绪阶段判断详情
}

// 大面个股
export interface BigLossStock {
  stock_code: string;
  stock_name: string;
  today_change_pct: number;                // 今日涨跌幅
  yesterday_continuous_days: number;       // 昨日连板数
  yesterday_opening_times?: number;        // 昨日炸板次数
  concepts: string[];                      // 所属概念
}

// 昨日涨停表现
export interface YesterdayPerformance {
  yesterday_limit_up_count: number;        // 昨日涨停数
  today_avg_change?: number;               // 今日平均涨幅
  up_count: number;                        // 上涨家数
  down_count: number;                      // 下跌家数
  big_loss_count: number;                  // 大面数量
  big_loss_rate: number;                   // 大面率(%)
  big_loss_stocks: BigLossStock[];         // 大面个股列表
}

// 梯队层级
export interface LadderItem {
  days: number;                            // 连板天数
  count: number;                           // 该层级股票数量
  stocks: string[];                        // 股票名称列表
}

// 概念梯队项
export interface ConceptLadderItem {
  concept_name: string;                    // 概念名称
  max_continuous_days: number;             // 最高连板数
  total_limit_up_count: number;            // 涨停总数
  concept_change_pct?: number;             // 板块涨幅
  ladder_status: string;                   // 梯队状态: complete/normal/alone
  is_main_line: boolean;                   // 是否主线板块
  ladder: LadderItem[];                    // 梯队分布
}

// 概念梯队分析
export interface ConceptLadder {
  available: boolean;                      // 是否可用
  concepts: ConceptLadderItem[];           // 概念梯队列表
}

// 技术面分析
export interface TechnicalAnalysis {
  first_limit_time?: string;               // 首次封板时间
  first_limit_time_level: string;          // 首封评级
  last_limit_time?: string;                // 最后封板时间
  opening_times: number;                   // 开板次数
  opening_times_level: string;             // 开板评级
  turnover_rate?: number;                  // 换手率
  turnover_rate_level: string;             // 换手评级
  amount?: number;                         // 成交额
}

// 资金面分析
export interface CapitalAnalysis {
  main_net_inflow?: number;                // 主力净流入
  main_net_inflow_level: string;           // 净流入评级
  main_net_inflow_pct?: number;            // 主力净流入占比
  sealed_amount?: number;                  // 封单金额
  sealed_ratio?: number;                   // 封单比
  sealed_ratio_level: string;              // 封单评级
}

// 股票所属概念梯队
export interface StockLadder {
  concept_name?: string;                   // 主概念名称
  status: string;                          // 梯队状态
  follower_count: number;                  // 跟风股数
  ladder_detail: LadderItem[];             // 梯队详情
}

// 龙头综合评估
export interface LeaderEvaluation {
  positive_factors: string[];              // 利好因素
  negative_factors: string[];              // 风险因素
  conclusion: string;                      // 结论: opportunity/neutral/risk
  conclusion_text: string;                 // 结论文本
}

// 龙头股分析项
export interface LeaderAnalysisItem {
  stock_code: string;
  stock_name: string;
  continuous_days: number;                 // 连板天数
  is_top: boolean;                         // 是否高标
  concepts: string[];                      // 所属概念
  industry?: string;                       // 所属行业
  technical: TechnicalAnalysis;            // 技术面分析
  capital: CapitalAnalysis;                // 资金面分析
  ladder: StockLadder;                     // 梯队情况
  evaluation: LeaderEvaluation;            // 综合评估
}

// 情绪分析数据
export interface SentimentAnalysisData {
  emotion_dashboard: EmotionDashboard;     // 情绪周期仪表盘
  yesterday_performance: YesterdayPerformance;  // 昨日涨停表现
  concept_ladder: ConceptLadder;           // 概念梯队分析
  leader_analysis: LeaderAnalysisItem[];   // 龙头股深度分析
}

// 情绪分析API响应
export interface SentimentAnalysisResponse {
  success: boolean;
  trade_date: string;
  data: SentimentAnalysisData;
}

// ============================================
// 个股分析类型
// ============================================

// 技术面评分详情
export interface TechnicalScoreDetail {
  first_limit_time?: string;       // 首次封板时间
  opening_times: number;            // 开板次数
  turnover_rate?: number;           // 换手率(%)
  is_one_word: boolean;             // 是否一字板
  time_score: number;               // 封板时间得分
  turnover_score: number;           // 换手率得分
  final_score: number;              // 技术面最终得分(-2 ~ +2)
}

// 资金面评分详情
export interface CapitalScoreDetail {
  sealed_amount?: number;           // 封单金额(万元)
  amount?: number;                  // 成交额(万元)
  sealed_ratio?: number;            // 封单比(封单/成交)
  main_net_inflow?: number;         // 主力净流入(万元)
  main_net_inflow_pct?: number;     // 主力净流入占比(%)
  sealed_score: number;             // 封单比得分
  inflow_score: number;             // 主力净流入得分
  final_score: number;              // 资金面最终得分(-2 ~ +2)
}

// 题材地位评分详情
export interface ThemeScoreDetail {
  main_concept?: string;            // 主概念名称
  is_in_top10: boolean;             // 是否在前十热门概念
  is_main_line: boolean;            // 是否主线板块
  ladder_status: string;            // 梯队状态: complete/normal/alone
  theme_hot_score: number;          // 题材热度得分
  ladder_score: number;             // 梯队状态得分
  final_score: number;              // 题材地位最终得分(-2 ~ +2)
}

// 位置风险评分详情
export interface PositionScoreDetail {
  continuous_days: number;          // 连板天数
  position_risk_level: string;      // 风险等级: 极高/高/中/低/极低
  final_score: number;              // 位置风险得分(-2 ~ +2)
}

// 市场环境评分详情
export interface MarketScoreDetail {
  emotion_stage: string;            // 情绪阶段
  emotion_stage_color: string;      // 阶段颜色
  final_score: number;              // 市场环境得分(-2 ~ +2)
}

// 溢价评分结果
export interface PremiumScoreResult {
  // 基础信息
  stock_code: string;
  stock_name: string;
  trade_date: string;

  // 总分和等级
  total_score: number;              // 总分(-9 ~ +9)
  premium_level: string;            // 溢价等级: 极高/高/偏高/中性/偏低/低
  premium_level_color: string;      // 等级颜色

  // 各维度得分
  technical_score: number;          // 技术面得分(-2 ~ +2)
  capital_score: number;            // 资金面得分(-2 ~ +2)
  theme_score: number;              // 题材地位得分(-2 ~ +2)
  position_score: number;           // 位置风险得分(-2 ~ +2)
  market_score: number;             // 市场环境得分(-1 ~ +1)

  // 详细评分信息
  technical_detail: TechnicalScoreDetail;   // 技术面详情
  capital_detail: CapitalScoreDetail;       // 资金面详情
  theme_detail: ThemeScoreDetail;           // 题材地位详情
  position_detail: PositionScoreDetail;     // 位置风险详情
  market_detail: MarketScoreDetail;         // 市场环境详情
}

// 溢价评分API响应
export interface PremiumScoreResponse {
  success: boolean;
  data: PremiumScoreResult;
}

// ============================================
// 回测分析类型
// ============================================

// 回测记录项
export interface BacktestRecord {
  id: number;
  stock_code: string;
  stock_name: string;
  trade_date: string;                // 评测日期（涨停日）

  // 评分数据
  continuous_days: number;           // 连板天数
  total_score: number;               // 总分（10分制）
  premium_level: string;             // 溢价等级

  // 各维度得分
  technical_score: number;
  capital_score: number;
  theme_score: number;
  position_score: number;
  market_score: number;

  // 次日实际表现
  next_trade_date?: string;          // 次日交易日期
  next_day_change_pct?: number;      // 次日涨跌幅(%)
  next_day_close_price?: number;     // 次日收盘价
  is_next_day_limit_up?: boolean;    // 次日是否涨停
  is_next_day_limit_down?: boolean;  // 次日是否跌停
  next_day_turnover_rate?: number;   // 次日换手率(%)

  // 预测准确性
  prediction_result?: string;        // 预测结果: correct/wrong/neutral
  is_profitable?: boolean;           // 是否盈利

  // 元数据
  created_at?: string;
  updated_at?: string;
}

// 回测结果查询响应
export interface BacktestResultsResponse {
  success: boolean;
  data: BacktestRecord[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// 回测统计按等级
export interface BacktestLevelStats {
  count: number;                     // 样本数
  avg_next_day_pct: number;          // 平均次日涨幅
  limit_up_count: number;            // 涨停数
  limit_up_rate: number;             // 涨停率(%)
  profitable_count: number;          // 盈利数
  profitable_rate: number;           // 盈利率(%)
  prediction_accuracy: number;       // 预测准确率(%)
}

// 回测整体统计
export interface BacktestOverallStats {
  avg_next_day_pct: number;
  limit_up_count: number;
  limit_up_rate: number;
  profitable_count: number;
  profitable_rate: number;
  correct_predictions: number;
  prediction_accuracy: number;
}

// 回测统计数据
export interface BacktestStatistics {
  total: number;                             // 总记录数
  by_level: Record<string, BacktestLevelStats>;  // 按等级统计
  overall: BacktestOverallStats;             // 整体统计
}

// 回测统计响应
export interface BacktestStatisticsResponse {
  success: boolean;
  data: BacktestStatistics;
}
