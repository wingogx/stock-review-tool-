'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { Card } from '@/components/ui/card';
import {
  SentimentAnalysisResponse,
  EmotionDashboard,
  YesterdayPerformance,
  ConceptLadder,
  LeaderAnalysisItem,
  PromotionDetail,
  BigLossStock,
  ConceptLadderItem,
  LadderItem,
  PremiumStats,
  StageDetails,
} from '@/types/api';

// ========== 工具函数 ==========

// 格式化金额（亿）
const formatAmount = (value?: number) => {
  if (value === undefined || value === null) return '-';
  const yi = value / 100000000;
  return yi >= 1 ? `${yi.toFixed(1)}亿` : `${(value / 10000).toFixed(0)}万`;
};

// 格式化涨幅百分比
const formatChangePct = (value?: number) => {
  if (value === undefined || value === null) return '-';
  const prefix = value >= 0 ? '+' : '';
  return `${prefix}${value.toFixed(2)}%`;
};

// 情绪阶段颜色
const getStageColor = (color: string) => {
  const colorMap: Record<string, string> = {
    blue: 'bg-blue-100 text-blue-700 border-blue-300',
    yellow: 'bg-yellow-100 text-yellow-700 border-yellow-300',
    orange: 'bg-orange-100 text-orange-700 border-orange-300',
    red: 'bg-red-100 text-red-700 border-red-300',
    green: 'bg-green-100 text-green-700 border-green-300',
  };
  return colorMap[color] || colorMap.blue;
};

// 评级颜色
const getLevelColor = (level: string) => {
  if (level === 'strong') return 'text-red-600';
  if (level === 'weak') return 'text-green-600';
  return 'text-gray-600';
};

// ========== 模块1：情绪周期仪表盘 ==========

function EmotionDashboardCard({ data }: { data: EmotionDashboard }) {
  return (
    <Card title="情绪周期仪表盘" subtitle="空间板高度、晋级率、情绪阶段">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
        {/* 空间板高度 */}
        <div className="text-center p-4 bg-gray-50 rounded-lg">
          <div className="text-4xl font-bold text-red-600">
            {data.space_height}
            {data.space_height_change !== undefined && data.space_height_change !== null && (
              <span className={`text-lg ml-1 ${data.space_height_change >= 0 ? 'text-red-500' : 'text-green-500'}`}>
                {data.space_height_change >= 0 ? '+' : ''}{data.space_height_change}
              </span>
            )}
          </div>
          <div className="text-sm text-gray-500 mt-1">空间板高度</div>
        </div>

        {/* 涨停数 */}
        <div className="text-center p-4 bg-gray-50 rounded-lg">
          <div className="text-4xl font-bold text-gray-800">
            {data.limit_up_count}
            {data.limit_up_change !== undefined && data.limit_up_change !== null && (
              <span className={`text-lg ml-1 ${data.limit_up_change >= 0 ? 'text-red-500' : 'text-green-500'}`}>
                {data.limit_up_change >= 0 ? '+' : ''}{data.limit_up_change}
              </span>
            )}
          </div>
          <div className="text-sm text-gray-500 mt-1">涨停数</div>
        </div>

        {/* 炸板率 */}
        <div className="text-center p-4 bg-gray-50 rounded-lg">
          <div className={`text-4xl font-bold ${data.explosion_rate > 30 ? 'text-green-600' : 'text-gray-800'}`}>
            {data.explosion_rate.toFixed(1)}%
            {data.explosion_rate_change !== undefined && data.explosion_rate_change !== null && (
              <span className={`text-lg ml-1 ${data.explosion_rate_change <= 0 ? 'text-red-500' : 'text-green-500'}`}>
                {data.explosion_rate_change >= 0 ? '+' : ''}{data.explosion_rate_change.toFixed(1)}%
              </span>
            )}
          </div>
          <div className="text-sm text-gray-500 mt-1">炸板率</div>
        </div>

        {/* 情绪阶段 */}
        <div className="text-center p-4 bg-gray-50 rounded-lg">
          <div className={`inline-block px-4 py-2 rounded-full text-xl font-bold border ${getStageColor(data.emotion_stage_color)}`}>
            {data.emotion_stage}
          </div>
          {data.stage_details?.total_score !== undefined && (
            <div className="text-xs text-gray-400 mt-1">
              综合得分: {data.stage_details.total_score >= 0 ? '+' : ''}{data.stage_details.total_score}
            </div>
          )}
          <div className="text-sm text-gray-500 mt-1">情绪阶段</div>
        </div>
      </div>

      {/* 调试信息链接（悬停显示） */}
      <div className="mt-4 flex gap-4">
        {/* 溢价统计 */}
        {data.premium_stats && (
          <div className="relative group">
            <span className="text-sm text-blue-600 cursor-pointer hover:underline">溢价统计</span>
            <div className="absolute left-0 top-6 z-50 hidden group-hover:block bg-white border border-gray-200 rounded-lg shadow-lg p-3 min-w-[400px]">
              <div className="text-xs font-medium text-gray-700 mb-2">昨日涨停溢价统计</div>
              <div className="grid grid-cols-3 gap-2">
                <div className="text-center p-1 bg-gray-50 rounded">
                  <div className={`text-sm font-bold ${(data.premium_stats.avg_premium ?? 0) >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {data.premium_stats.avg_premium !== undefined ? `${data.premium_stats.avg_premium >= 0 ? '+' : ''}${data.premium_stats.avg_premium.toFixed(2)}%` : '-'}
                  </div>
                  <div className="text-xs text-gray-500">整体溢价</div>
                </div>
                <div className="text-center p-1 bg-gray-50 rounded">
                  <div className={`text-sm font-bold ${(data.premium_stats.avg_open_premium ?? 0) >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {data.premium_stats.avg_open_premium !== undefined ? `${data.premium_stats.avg_open_premium >= 0 ? '+' : ''}${data.premium_stats.avg_open_premium.toFixed(2)}%` : '-'}
                  </div>
                  <div className="text-xs text-gray-500">开盘溢价</div>
                </div>
                <div className="text-center p-1 bg-gray-50 rounded">
                  <div className={`text-sm font-bold ${(data.premium_stats.first_board_premium ?? 0) >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {data.premium_stats.first_board_premium !== undefined ? `${data.premium_stats.first_board_premium >= 0 ? '+' : ''}${data.premium_stats.first_board_premium.toFixed(2)}%` : '-'}
                  </div>
                  <div className="text-xs text-gray-500">首板溢价</div>
                </div>
                <div className="text-center p-1 bg-gray-50 rounded">
                  <div className={`text-sm font-bold ${(data.premium_stats.high_board_premium ?? 0) >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {data.premium_stats.high_board_premium !== undefined ? `${data.premium_stats.high_board_premium >= 0 ? '+' : ''}${data.premium_stats.high_board_premium.toFixed(2)}%` : '-'}
                  </div>
                  <div className="text-xs text-gray-500">高位板溢价</div>
                </div>
                <div className="text-center p-1 bg-gray-50 rounded">
                  <div className={`text-sm font-bold ${(data.premium_stats.big_loss_rate ?? 0) > 30 ? 'text-green-600' : 'text-gray-800'}`}>
                    {data.premium_stats.big_loss_rate !== undefined ? `${data.premium_stats.big_loss_rate.toFixed(1)}%` : '-'}
                  </div>
                  <div className="text-xs text-gray-500">大面率</div>
                </div>
                <div className="text-center p-1 bg-gray-50 rounded">
                  <div className={`text-sm font-bold ${(data.premium_stats.high_board_big_loss_rate ?? 0) > 30 ? 'text-green-600' : 'text-gray-800'}`}>
                    {data.premium_stats.high_board_big_loss_rate !== undefined ? `${data.premium_stats.high_board_big_loss_rate.toFixed(1)}%` : '-'}
                  </div>
                  <div className="text-xs text-gray-500">高位大面率</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 因子得分 */}
        {data.stage_details?.factor_scores && (
          <div className="relative group">
            <span className="text-sm text-blue-600 cursor-pointer hover:underline">因子得分</span>
            <div className="absolute left-0 top-6 z-50 hidden group-hover:block bg-white border border-gray-200 rounded-lg shadow-lg p-3 min-w-[350px]">
              <div className="text-xs font-medium text-gray-700 mb-2">因子得分明细 (总分: {data.stage_details.total_score})</div>
              <div className="grid grid-cols-4 gap-2">
                {Object.entries(data.stage_details.factor_scores).map(([factor, score]) => (
                  <div key={factor} className="text-center p-1 bg-gray-50 rounded">
                    <div className={`text-sm font-bold ${score > 0 ? 'text-red-600' : score < 0 ? 'text-green-600' : 'text-gray-400'}`}>
                      {score > 0 ? '+' : ''}{score}
                    </div>
                    <div className="text-xs text-gray-500">{factor}</div>
                  </div>
                ))}
              </div>
              {data.stage_details.used_inertia && (
                <div className="mt-2 text-xs text-orange-600">惯性生效: 昨日{data.stage_details.previous_stage}</div>
              )}
            </div>
          </div>
        )}

        {/* 晋级率 */}
        {data.promotion_details.length > 0 && (
          <div className="relative group">
            <span className="text-sm text-blue-600 cursor-pointer hover:underline">晋级率</span>
            <div className="absolute left-0 top-6 z-50 hidden group-hover:block bg-white border border-gray-200 rounded-lg shadow-lg p-3 min-w-[300px]">
              <div className="text-xs font-medium text-gray-700 mb-2">分层晋级率</div>
              <div className="flex flex-wrap gap-2">
                {data.promotion_details.map((item: PromotionDetail) => (
                  <div
                    key={`${item.from_days}-${item.to_days}`}
                    className="px-2 py-1 bg-gray-100 rounded text-xs"
                  >
                    <span className="text-gray-600">{item.from_days}→{item.to_days}板:</span>
                    <span className={`ml-1 font-medium ${item.rate >= 50 ? 'text-red-600' : item.rate >= 30 ? 'text-orange-600' : 'text-green-600'}`}>
                      {item.rate.toFixed(1)}%
                    </span>
                    <span className="text-gray-400 ml-1">({item.yesterday_count}→{item.today_count})</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}

// ========== 模块2：昨日涨停表现 ==========

function YesterdayPerformanceCard({ data }: { data: YesterdayPerformance }) {
  return (
    <Card title="昨日涨停表现" subtitle="昨日涨停股今日表现、大面情况">
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-4">
        {/* 昨日涨停数 */}
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <div className="text-2xl font-bold text-gray-800">{data.yesterday_limit_up_count}</div>
          <div className="text-xs text-gray-500">昨日涨停</div>
        </div>

        {/* 今日平均涨幅（新增） */}
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <div className={`text-2xl font-bold ${(data.today_avg_change ?? 0) >= 0 ? 'text-red-600' : 'text-green-600'}`}>
            {data.today_avg_change !== undefined && data.today_avg_change !== null
              ? `${data.today_avg_change >= 0 ? '+' : ''}${data.today_avg_change.toFixed(2)}%`
              : '-'}
          </div>
          <div className="text-xs text-gray-500">平均涨幅</div>
        </div>

        {/* 今日上涨/下跌 */}
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <div className="text-lg">
            <span className="text-red-600 font-bold">{data.up_count}</span>
            <span className="text-gray-400 mx-1">/</span>
            <span className="text-green-600 font-bold">{data.down_count}</span>
          </div>
          <div className="text-xs text-gray-500">涨/跌</div>
        </div>

        {/* 大面数量 */}
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <div className={`text-2xl font-bold ${data.big_loss_count > 5 ? 'text-green-600' : 'text-gray-800'}`}>
            {data.big_loss_count}
          </div>
          <div className="text-xs text-gray-500">大面数</div>
        </div>

        {/* 大面率 */}
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <div className={`text-2xl font-bold ${data.big_loss_rate > 15 ? 'text-green-600' : 'text-gray-800'}`}>
            {data.big_loss_rate.toFixed(1)}%
          </div>
          <div className="text-xs text-gray-500">大面率</div>
        </div>
      </div>

      {/* 大面个股列表 */}
      {data.big_loss_stocks.length > 0 && (
        <div className="mt-4">
          <div className="text-sm font-medium text-gray-700 mb-2">大面个股（跌幅&gt;5%）</div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">股票</th>
                  <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">涨跌幅</th>
                  <th className="px-3 py-2 text-center text-xs font-medium text-gray-500">昨日板数</th>
                  <th className="px-3 py-2 text-center text-xs font-medium text-gray-500">昨日炸板</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.big_loss_stocks.map((stock: BigLossStock) => (
                  <tr key={stock.stock_code} className="hover:bg-gray-50">
                    <td className="px-3 py-2 whitespace-nowrap text-sm">
                      <span className="font-medium text-gray-900">{stock.stock_name}</span>
                      <span className="text-gray-400 text-xs ml-1">{stock.stock_code}</span>
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-right">
                      <span className="text-sm text-green-600 font-medium">
                        {formatChangePct(stock.today_change_pct)}
                      </span>
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-center text-sm text-gray-600">
                      {stock.yesterday_continuous_days}板
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-center text-sm text-gray-600">
                      {stock.yesterday_opening_times !== undefined && stock.yesterday_opening_times !== null
                        ? `${stock.yesterday_opening_times}次`
                        : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {data.big_loss_stocks.length === 0 && (
        <div className="text-center py-4 text-gray-500">今日无大面个股（跌幅&gt;5%）</div>
      )}
    </Card>
  );
}

// ========== 模块3：概念梯队分析 ==========

function ConceptLadderCard({ data }: { data: ConceptLadder }) {
  if (!data.available) {
    return (
      <Card title="高标梯队分析" subtitle="空间板>=4板时展示">
        <div className="text-center py-8">
          <div className="text-gray-500">当前为冰点期（空间板&lt;4板）</div>
          <div className="text-gray-400 text-sm mt-1">梯队分析在加速/高潮期更有参考价值</div>
        </div>
      </Card>
    );
  }

  if (data.concepts.length === 0) {
    return (
      <Card title="高标梯队分析" subtitle="空间板>=4板时展示">
        <div className="text-center py-8">
          <div className="text-gray-500">无梯队板块</div>
          <div className="text-gray-400 text-sm mt-1">暂无符合条件的概念梯队（需梯队层级≥3）</div>
        </div>
      </Card>
    );
  }

  return (
    <Card title="高标梯队分析" subtitle="4板+概念的梯队分布">
      <div className="space-y-4">
        {data.concepts.map((concept: ConceptLadderItem) => (
          <div key={concept.concept_name} className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="font-medium text-gray-900">{concept.concept_name}</span>
                {concept.is_main_line && (
                  <span className="px-1.5 py-0.5 text-xs bg-red-100 text-red-600 rounded">主线</span>
                )}
              </div>
              <div className="text-sm text-gray-500">
                最高{concept.max_continuous_days}板 · {concept.total_limit_up_count}只涨停
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              {concept.ladder.map((level: LadderItem) => (
                <div
                  key={level.days}
                  className={`px-2 py-1 rounded text-sm ${
                    level.days >= 5 ? 'bg-red-100' :
                    level.days >= 4 ? 'bg-orange-100' :
                    'bg-white'
                  }`}
                >
                  <span className="font-medium">{level.days}板</span>
                  <span className="text-gray-500 mx-1">·</span>
                  <span className="text-gray-600">{level.stocks.slice(0, 3).join('、')}</span>
                  {level.count > 3 && <span className="text-gray-400">等{level.count}只</span>}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

// ========== 模块4：龙头股深度分析 ==========

function LeaderAnalysisCard({ data }: { data: LeaderAnalysisItem[] }) {
  if (data.length === 0) {
    return (
      <Card title="龙头股深度分析" subtitle="4板+龙头的多维度分析">
        <div className="text-center py-8 text-gray-500">当前无4板+龙头股</div>
      </Card>
    );
  }

  const getConclusionStyle = (conclusion: string) => {
    if (conclusion === 'opportunity') return 'bg-red-50 border-red-200 text-red-700';
    if (conclusion === 'risk') return 'bg-green-50 border-green-200 text-green-700';
    return 'bg-gray-50 border-gray-200 text-gray-700';
  };

  return (
    <Card title="龙头股深度分析" subtitle="4板+龙头的技术面、资金面、梯队、综合评估">
      <div className="space-y-6">
        {data.map((leader: LeaderAnalysisItem) => (
          <div key={leader.stock_code} className="bg-gray-50 rounded-lg p-4">
            {/* 头部：股票信息 */}
            <div className="flex items-center justify-between mb-4 pb-3 border-b">
              <div className="flex items-center gap-3">
                <span className="text-xl font-bold text-gray-900">{leader.stock_name}</span>
                <span className="px-2 py-1 text-sm bg-red-100 text-red-600 rounded font-medium">
                  {leader.continuous_days}连板
                </span>
                {leader.is_top && (
                  <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded">高标</span>
                )}
              </div>
              <div className="text-sm text-gray-500">
                {leader.concepts.slice(0, 2).join(' · ')}
              </div>
            </div>

            {/* 四维分析 */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* 技术面 */}
              <div className="bg-gray-50 rounded p-3">
                <div className="text-sm font-medium text-gray-700 mb-2">技术面</div>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">首封时间</span>
                    <span className={getLevelColor(leader.technical.first_limit_time_level)}>
                      {leader.technical.first_limit_time || '-'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">开板次数</span>
                    <span className={getLevelColor(leader.technical.opening_times_level)}>
                      {leader.technical.opening_times}次
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">换手率</span>
                    <span className={getLevelColor(leader.technical.turnover_rate_level)}>
                      {leader.technical.turnover_rate?.toFixed(1) || '-'}%
                    </span>
                  </div>
                </div>
              </div>

              {/* 资金面 */}
              <div className="bg-gray-50 rounded p-3">
                <div className="text-sm font-medium text-gray-700 mb-2">资金面</div>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">主力净流入</span>
                    <span className={getLevelColor(leader.capital.main_net_inflow_level)}>
                      {formatAmount(leader.capital.main_net_inflow)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">净流入占比</span>
                    <span className="text-gray-600">
                      {leader.capital.main_net_inflow_pct?.toFixed(1) || '-'}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">封单比</span>
                    <span className={getLevelColor(leader.capital.sealed_ratio_level)}>
                      {leader.capital.sealed_ratio?.toFixed(0) || '-'}%
                    </span>
                  </div>
                </div>
              </div>

              {/* 梯队情况 */}
              <div className="bg-gray-50 rounded p-3">
                <div className="text-sm font-medium text-gray-700 mb-2">梯队情况</div>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">主概念</span>
                    <span className="text-gray-800">{leader.ladder.concept_name || '-'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">跟风股</span>
                    <span className={leader.ladder.status === 'alone' ? 'text-yellow-600' : 'text-gray-800'}>
                      {leader.ladder.follower_count}只
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">梯队状态</span>
                    <span className={
                      leader.ladder.status === 'complete' ? 'text-red-600' :
                      leader.ladder.status === 'alone' ? 'text-yellow-600' : 'text-gray-600'
                    }>
                      {leader.ladder.status === 'complete' ? '完整' :
                       leader.ladder.status === 'alone' ? '独苗' : '一般'}
                    </span>
                  </div>
                </div>
              </div>

              {/* 综合评估 */}
              <div className={`rounded p-3 border ${getConclusionStyle(leader.evaluation.conclusion)}`}>
                <div className="text-sm font-medium mb-2">综合评估</div>
                <div className="text-lg font-bold mb-2">{leader.evaluation.conclusion_text}</div>
                <div className="text-xs space-y-0.5">
                  {leader.evaluation.positive_factors.slice(0, 2).map((f, i) => (
                    <div key={i} className="text-red-600">+ {f}</div>
                  ))}
                  {leader.evaluation.negative_factors.slice(0, 2).map((f, i) => (
                    <div key={i} className="text-green-600">- {f}</div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

// ========== 主页面 ==========

export default function SentimentPage() {
  const { data, isLoading, error } = useQuery<SentimentAnalysisResponse>({
    queryKey: ['sentimentAnalysis'],
    queryFn: async () => {
      const response = await apiClient.get('/api/sentiment/analysis');
      return response.data;
    },
    refetchInterval: 60000,
  });

  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* 加载状态 */}
        {isLoading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            <p className="mt-4 text-gray-600">加载数据中...</p>
          </div>
        )}

        {/* 错误状态 */}
        {error && (
          <div className="text-center py-12">
            <p className="text-red-500">加载失败: {(error as Error).message}</p>
          </div>
        )}

        {/* 数据展示 */}
        {!isLoading && data && (
          <div className="space-y-6">
            {/* 模块1：情绪周期仪表盘 */}
            <EmotionDashboardCard data={data.data.emotion_dashboard} />

            {/* 模块2 + 模块3：昨日涨停表现 | 概念梯队分析 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <YesterdayPerformanceCard data={data.data.yesterday_performance} />
              <ConceptLadderCard data={data.data.concept_ladder} />
            </div>

            {/* 模块4：龙头股深度分析 */}
            <LeaderAnalysisCard data={data.data.leader_analysis} />
          </div>
        )}
      </div>
    </main>
  );
}
