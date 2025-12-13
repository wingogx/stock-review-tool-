'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { Card } from '@/components/ui/card';
import {
  SectorAnalysisResponse,
  TrendSectorItem,
  EmotionSectorItem,
  MainSectorItem,
  AnomalySectorItem,
} from '@/types/api';

// 格式化涨幅百分比
const formatChangePct = (value?: number) => {
  if (value === undefined || value === null) return '-';
  const prefix = value >= 0 ? '+' : '';
  return `${prefix}${value.toFixed(2)}%`;
};

// 涨幅颜色
const getChangePctColor = (value?: number) => {
  if (value === undefined || value === null) return 'text-gray-500';
  return value >= 0 ? 'text-red-600' : 'text-green-600';
};

// 趋势板块
function TrendSectorCard({ sectors }: { sectors: TrendSectorItem[] }) {
  return (
    <Card title="趋势板块" subtitle="5日涨幅排名前6">
      <div className="overflow-x-auto">
        {sectors.length === 0 ? (
          <div className="text-center py-8 text-gray-500">暂无数据</div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">
                  板块名称
                </th>
                <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">
                  当日
                </th>
                <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">
                  5日
                </th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">
                  龙头股
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sectors.map((sector) => (
                <tr key={sector.concept_name} className="hover:bg-gray-50">
                  <td className="px-3 py-2 whitespace-nowrap text-sm font-medium text-gray-900">
                    {sector.concept_name}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap text-right">
                    <span className={`text-sm ${getChangePctColor(sector.day_change_pct)}`}>
                      {formatChangePct(sector.day_change_pct)}
                    </span>
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap text-right">
                    <span className={`text-sm font-medium ${getChangePctColor(sector.change_pct)}`}>
                      {formatChangePct(sector.change_pct)}
                    </span>
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-600">
                    {sector.leader_stock_name ? (
                      <div className="flex items-center gap-1">
                        <span>{sector.leader_stock_name}</span>
                        {sector.leader_continuous_days && sector.leader_continuous_days > 1 && (
                          <span className="px-1 py-0.5 text-[10px] bg-red-100 text-red-600 rounded">
                            {sector.leader_continuous_days}连板
                          </span>
                        )}
                      </div>
                    ) : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Card>
  );
}

// 情绪板块
function EmotionSectorCard({ sectors }: { sectors: EmotionSectorItem[] }) {
  return (
    <Card title="情绪板块" subtitle="涨停数≥8的板块">
      <div className="overflow-x-auto">
        {sectors.length === 0 ? (
          <div className="text-center py-8 text-gray-500">没有涨停潮板块</div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">
                  板块名称
                </th>
                <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">
                  当日
                </th>
                <th className="px-3 py-2 text-center text-xs font-medium text-gray-500">
                  涨停
                </th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">
                  龙头股
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sectors.map((sector) => (
                <tr key={sector.concept_name} className="hover:bg-gray-50">
                  <td className="px-3 py-2 whitespace-nowrap text-sm font-medium text-gray-900">
                    {sector.concept_name}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap text-right">
                    <span className={`text-sm ${getChangePctColor(sector.day_change_pct)}`}>
                      {formatChangePct(sector.day_change_pct)}
                    </span>
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap text-center">
                    <span className="text-sm text-red-600 font-medium">
                      {sector.limit_up_count || 0}
                    </span>
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-600">
                    {sector.leader_stock_name ? (
                      <div className="flex items-center gap-1">
                        <span>{sector.leader_stock_name}</span>
                        {sector.leader_continuous_days && sector.leader_continuous_days > 1 && (
                          <span className="px-1 py-0.5 text-[10px] bg-red-100 text-red-600 rounded">
                            {sector.leader_continuous_days}连板
                          </span>
                        )}
                      </div>
                    ) : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Card>
  );
}

// 主线板块
function MainSectorCard({ sectors }: { sectors: MainSectorItem[] }) {
  return (
    <Card title="主线板块" subtitle="趋势与情绪的交集（热门TOP10 且 涨停数≥8）">
      <div className="overflow-x-auto">
        {sectors.length === 0 ? (
          <div className="text-center py-8 text-gray-500">当前无主线题材</div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  连续主线
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  上榜首日
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  板块名称
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  当日涨幅
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  5日涨幅
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  涨停数
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  龙头股
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sectors.map((sector) => (
                <tr key={sector.concept_name} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className="font-medium text-red-600">{sector.consecutive_main_days}</span>
                    <span className="text-gray-400 text-xs ml-1">天</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {sector.first_main_date ? sector.first_main_date.substring(5) : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    <div className="flex items-center gap-1">
                      {sector.concept_name}
                      {sector.consecutive_main_days <= 3 && (
                        <span className="px-1 py-0.5 text-[10px] bg-orange-100 text-orange-600 rounded">
                          新
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`text-sm font-medium ${getChangePctColor(sector.day_change_pct)}`}>
                      {formatChangePct(sector.day_change_pct)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`text-sm font-medium ${getChangePctColor(sector.change_pct)}`}>
                      {formatChangePct(sector.change_pct)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                    <span className="text-red-600 font-medium">
                      {sector.limit_up_count || 0}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {sector.leader_stock_name ? (
                      <div className="flex items-center gap-2">
                        <span className="text-gray-900">{sector.leader_stock_name}</span>
                        {sector.leader_continuous_days && sector.leader_continuous_days > 1 && (
                          <span className="px-1.5 py-0.5 text-xs bg-red-100 text-red-600 rounded">
                            {sector.leader_continuous_days}连板
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Card>
  );
}

// 异动板块
function AnomalySectorCard({ sectors }: { sectors: AnomalySectorItem[] }) {
  return (
    <Card title="异动板块" subtitle="TOP10外涨停/涨幅异动">
      <div className="overflow-x-auto">
        {sectors.length === 0 ? (
          <div className="text-center py-8 text-gray-500">当日无异动</div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">
                  板块名称
                </th>
                <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">
                  当日
                </th>
                <th className="px-3 py-2 text-center text-xs font-medium text-gray-500">
                  涨停
                </th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">
                  龙头股
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sectors.map((sector) => (
                <tr key={sector.concept_name} className="hover:bg-gray-50">
                  <td className="px-3 py-2 whitespace-nowrap">
                    <div className="flex items-center gap-1">
                      <span className="text-sm font-medium text-gray-900">
                        {sector.concept_name}
                      </span>
                      <span className={`px-1 py-0.5 text-[10px] rounded ${
                        sector.anomaly_type === 'limit_up'
                          ? 'bg-red-100 text-red-600'
                          : 'bg-orange-100 text-orange-600'
                      }`}>
                        {sector.anomaly_type === 'limit_up' ? '停' : '幅'}
                      </span>
                    </div>
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap text-right">
                    <span className={`text-sm ${getChangePctColor(sector.day_change_pct)}`}>
                      {formatChangePct(sector.day_change_pct)}
                    </span>
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap text-center">
                    <span className="text-sm text-red-600 font-medium">
                      {sector.limit_up_count || 0}
                    </span>
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-600">
                    {sector.leader_stock_name ? (
                      <div className="flex items-center gap-1">
                        <span>{sector.leader_stock_name}</span>
                        {sector.leader_continuous_days && sector.leader_continuous_days > 1 && (
                          <span className="px-1 py-0.5 text-[10px] bg-red-100 text-red-600 rounded">
                            {sector.leader_continuous_days}连板
                          </span>
                        )}
                      </div>
                    ) : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Card>
  );
}

export default function SectorPage() {
  // 获取板块分析数据
  const { data, isLoading, error } = useQuery<SectorAnalysisResponse>({
    queryKey: ['sectorAnalysis'],
    queryFn: async () => {
      const response = await apiClient.get('/api/sector/analysis');
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
            {/* 主线板块（最重要，放在最上面） */}
            <MainSectorCard sectors={data.data.main_sectors} />

            {/* 趋势板块 | 情绪板块 | 异动板块 - 三列并排 */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <TrendSectorCard sectors={data.data.trend_sectors} />
              <EmotionSectorCard sectors={data.data.emotion_sectors} />
              <AnomalySectorCard sectors={data.data.anomaly_sectors} />
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
