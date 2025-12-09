'use client';

/**
 * 仪表盘主页面
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card } from '@/components/ui/card';
import { getMarketIndex, getMarketSentiment, getHotConcepts, getLimitStocks } from '@/lib/api';
import { format } from 'date-fns';

export default function Dashboard() {
  // 当前选中的连板数（默认显示2板）
  const [selectedContinuousDays, setSelectedContinuousDays] = useState<number | null>(2);

  // 获取大盘指数
  const { data: marketIndex, isLoading: indexLoading } = useQuery({
    queryKey: ['marketIndex'],
    queryFn: () => getMarketIndex(),
  });

  // 获取市场情绪
  const { data: marketSentiment, isLoading: sentimentLoading } = useQuery({
    queryKey: ['marketSentiment'],
    queryFn: () => getMarketSentiment(),
  });

  // 获取热门概念
  const { data: hotConcepts, isLoading: conceptsLoading } = useQuery({
    queryKey: ['hotConcepts'],
    queryFn: () => getHotConcepts({ top_n: 10 }),
  });

  // 获取选中连板数的股票列表
  const { data: limitStocks, isLoading: limitStocksLoading } = useQuery({
    queryKey: ['limitStocks', selectedContinuousDays],
    queryFn: () => getLimitStocks({
      limit_type: 'limit_up',
      continuous_days: selectedContinuousDays!,
      page_size: 50,
    }),
    enabled: selectedContinuousDays !== null,
  });

  const isLoading = indexLoading || sentimentLoading || conceptsLoading;

  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* 页面标题 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">股票短线复盘</h1>
          <p className="text-gray-600 mt-2">
            交易日期: {marketIndex?.data[0]?.trade_date || format(new Date(), 'yyyy-MM-dd')}
          </p>
        </div>

        {isLoading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            <p className="mt-4 text-gray-600">加载数据中...</p>
          </div>
        )}

        {!isLoading && (
          <div className="space-y-6">
            {/* 大盘指数 */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {marketIndex?.data.map((index) => (
                <Card key={index.index_code} title={index.index_name}>
                  <div className="space-y-2">
                    {/* 收盘点位 */}
                    <div className="text-3xl font-bold text-gray-900">
                      {index.close?.toFixed(2) || '-'}
                    </div>
                    {/* 涨跌幅 */}
                    <div
                      className={`text-2xl font-semibold ${
                        (index.change_pct ?? 0) >= 0 ? 'text-red-600' : 'text-green-600'
                      }`}
                    >
                      {(index.change_pct ?? 0) >= 0 ? '+' : ''}
                      {index.change_pct?.toFixed(2)}%
                    </div>
                    <div className="text-sm text-gray-500 grid grid-cols-2 gap-2 mt-4">
                      <div>
                        成交量:{' '}
                        <span className="font-medium">
                          {index.volume ? `${(index.volume / 100000000).toFixed(0)}亿` : '-'}
                        </span>
                      </div>
                      <div>
                        成交额:{' '}
                        <span className="font-medium">
                          {index.amount ? `${(index.amount / 100000000).toFixed(0)}亿` : '-'}
                        </span>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>

            {/* 市场情绪 */}
            <Card title="市场情绪" subtitle="涨跌分布与市场状态">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div>
                  <div className="text-sm text-gray-500">上涨股票占比</div>
                  <div
                    className={`text-2xl font-bold mt-1 ${
                      (() => {
                        const upCount = marketSentiment?.data.up_count ?? 0;
                        const downCount = marketSentiment?.data.down_count ?? 0;
                        const total = upCount + downCount;
                        const upPct = total > 0 ? (upCount / total) * 100 : 0;
                        return upPct >= 60 ? 'text-red-600' : 'text-green-600';
                      })()
                    }`}
                  >
                    {(() => {
                      const upCount = marketSentiment?.data.up_count ?? 0;
                      const downCount = marketSentiment?.data.down_count ?? 0;
                      const total = upCount + downCount;
                      return total > 0 ? ((upCount / total) * 100).toFixed(2) : '0.00';
                    })()}%
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    涨{marketSentiment?.data.up_count} / 跌{marketSentiment?.data.down_count}
                  </div>
                  <div className="mt-4">
                    <div className="text-sm text-gray-500 mb-1">总成交额</div>
                    <div className="flex items-baseline gap-2">
                      <span
                        className={`text-lg font-semibold ${
                          marketSentiment?.data.total_amount_change !== undefined &&
                          marketSentiment?.data.total_amount_change !== null
                            ? marketSentiment.data.total_amount_change >= 0
                              ? 'text-red-600'
                              : 'text-green-600'
                            : 'text-gray-900'
                        }`}
                      >
                        {marketSentiment?.data.total_amount
                          ? `${(marketSentiment.data.total_amount / 100000000).toFixed(0)}亿`
                          : '-'}
                      </span>
                      {marketSentiment?.data.total_amount_change_pct !== undefined &&
                        marketSentiment?.data.total_amount_change_pct !== null && (
                          <span
                            className={`text-xs ${
                              marketSentiment.data.total_amount_change_pct >= 0
                                ? 'text-red-500'
                                : 'text-green-500'
                            }`}
                          >
                            {marketSentiment.data.total_amount_change_pct >= 0 ? '+' : ''}
                            {marketSentiment.data.total_amount_change_pct.toFixed(1)}%
                          </span>
                        )}
                    </div>
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">涨停数</div>
                  <div className="text-2xl font-bold text-red-600 mt-1">
                    {marketSentiment?.data.limit_up_count ?? '-'}
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    {marketSentiment?.data.prev_limit_up_count !== undefined &&
                    marketSentiment?.data.prev_limit_up_count !== null
                      ? `昨日: ${marketSentiment.data.prev_limit_up_count}`
                      : ''}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">跌停数</div>
                  <div className="text-2xl font-bold text-green-600 mt-1">
                    {marketSentiment?.data.limit_down_count ?? '-'}
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    {marketSentiment?.data.prev_limit_down_count !== undefined &&
                    marketSentiment?.data.prev_limit_down_count !== null
                      ? `昨日: ${marketSentiment.data.prev_limit_down_count}`
                      : ''}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">炸板率</div>
                  <div
                    className={`text-2xl font-bold mt-1 ${
                      (marketSentiment?.data.explosion_rate ?? 0) > 30
                        ? 'text-red-600'
                        : 'text-green-600'
                    }`}
                  >
                    {marketSentiment?.data.explosion_rate?.toFixed(1) ?? '-'}%
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    {(marketSentiment?.data.explosion_rate ?? 0) > 30 ? '情绪较差' : '情绪正常'}
                  </div>
                </div>
              </div>
              {/* 市场状态标签 */}
              <div className="mt-4 pt-4 border-t border-gray-100">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-500">市场状态:</span>
                  <span
                    className={`px-3 py-1 rounded-full text-sm font-medium ${
                      marketSentiment?.data.market_status === '强势'
                        ? 'bg-red-100 text-red-700'
                        : marketSentiment?.data.market_status === '弱势'
                        ? 'bg-green-100 text-green-700'
                        : 'bg-yellow-100 text-yellow-700'
                    }`}
                  >
                    {marketSentiment?.data.market_status ?? '震荡'}
                  </span>
                </div>
              </div>
            </Card>

            {/* 热门概念表格 */}
            <Card title="热门概念板块" subtitle="按5日涨幅排名">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        排名
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        概念名称
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
                      <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        上榜次数
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {hotConcepts?.data.map((concept, index) => (
                      <tr key={concept.concept_name} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {index + 1}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-gray-900">
                              {concept.concept_name}
                            </span>
                            {concept.is_new_concept && (
                              <span className="px-1.5 py-0.5 text-xs bg-red-100 text-red-600 rounded">
                                新
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`text-sm font-medium ${
                              (concept.day_change_pct ?? 0) >= 0
                                ? 'text-red-600'
                                : 'text-green-600'
                            }`}
                          >
                            {(concept.day_change_pct ?? 0) >= 0 ? '+' : ''}
                            {concept.day_change_pct?.toFixed(2) ?? '-'}%
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`text-sm font-medium ${
                              concept.change_pct >= 0 ? 'text-red-600' : 'text-green-600'
                            }`}
                          >
                            {concept.change_pct >= 0 ? '+' : ''}
                            {concept.change_pct.toFixed(2)}%
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                          {concept.limit_up_count !== undefined && concept.limit_up_count !== null ? (
                            <span className="text-red-600 font-medium">
                              {concept.limit_up_count}
                            </span>
                          ) : (
                            '-'
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          {concept.leader_stock_name ? (
                            <div className="flex items-center gap-2">
                              <span className="text-gray-900">{concept.leader_stock_name}</span>
                              {concept.leader_continuous_days && concept.leader_continuous_days > 1 && (
                                <span className="px-1.5 py-0.5 text-xs bg-red-100 text-red-600 rounded">
                                  {concept.leader_continuous_days}连板
                                </span>
                              )}
                            </div>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-center">
                          {concept.consecutive_days ?? '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>

            {/* 连板分布 */}
            <Card title="连板分布" subtitle="点击查看对应连板股票详情">
              <div className="flex flex-wrap gap-4">
                {(() => {
                  const distribution = marketSentiment?.data.continuous_limit_distribution || {};
                  const prev1Distribution = marketSentiment?.data.prev_continuous_limit_distribution || {};

                  // 动态获取所有板数（从2板开始）
                  const allKeys = Object.keys(distribution)
                    .map(Number)
                    .filter((n) => n >= 2)
                    .sort((a, b) => a - b);

                  // 如果没有数据，显示默认的2-5板
                  const keys = allKeys.length > 0 ? allKeys : [2, 3, 4, 5];

                  return keys.map((key) => {
                    const count = distribution[String(key)] || 0;
                    const prevCount = prev1Distribution[String(key - 1)] || 0;
                    const rate = prevCount > 0 ? ((count / prevCount) * 100).toFixed(1) : '-';
                    const isSelected = selectedContinuousDays === key;

                    return (
                      <button
                        key={key}
                        onClick={() => setSelectedContinuousDays(isSelected ? null : key)}
                        className={`text-center p-3 rounded-lg flex-1 min-w-[100px] transition-all cursor-pointer ${
                          isSelected
                            ? 'bg-red-100 ring-2 ring-red-500'
                            : 'bg-gray-50 hover:bg-gray-100'
                        }`}
                      >
                        <div className="text-sm text-gray-500 mb-1">{key}板</div>
                        <div className={`text-2xl font-bold ${isSelected ? 'text-red-700' : 'text-red-600'}`}>
                          {count}
                        </div>
                        <div className="text-xs text-gray-400 mt-1">
                          晋级率: {rate === '-' ? '-' : `${rate}%`}
                        </div>
                      </button>
                    );
                  });
                })()}
              </div>

              {/* 连板股票列表 */}
              {selectedContinuousDays !== null && (
                <div className="mt-6 border-t pt-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {selectedContinuousDays}连板股票
                    </h3>
                    <button
                      onClick={() => setSelectedContinuousDays(null)}
                      className="text-sm text-gray-500 hover:text-gray-700"
                    >
                      关闭
                    </button>
                  </div>

                  {limitStocksLoading ? (
                    <div className="text-center py-8">
                      <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-red-500"></div>
                      <p className="mt-2 text-gray-500">加载中...</p>
                    </div>
                  ) : limitStocks?.data && limitStocks.data.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-3 py-2 text-center text-xs font-medium text-gray-500">序号</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">代码</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">名称</th>
                            <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">涨跌幅</th>
                            <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">最新价</th>
                            <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">流通市值</th>
                            <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">换手率</th>
                            <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">封板资金</th>
                            <th className="px-3 py-2 text-center text-xs font-medium text-gray-500">首次封板时间</th>
                            <th className="px-3 py-2 text-center text-xs font-medium text-gray-500">炸板次数</th>
                            <th className="px-3 py-2 text-center text-xs font-medium text-gray-500">涨停统计</th>
                            <th className="px-3 py-2 text-center text-xs font-medium text-gray-500">封板类型</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">所属行业</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {limitStocks.data.map((stock, index) => (
                            <tr key={stock.stock_code} className="hover:bg-gray-50">
                              <td className="px-3 py-3 text-sm text-center text-gray-500">{index + 1}</td>
                              <td className="px-3 py-3 text-sm text-gray-600">{stock.stock_code}</td>
                              <td className="px-3 py-3 text-sm font-medium text-gray-900">{stock.stock_name}</td>
                              <td className="px-3 py-3 text-sm text-right text-red-600 font-medium">
                                +{stock.change_pct?.toFixed(2)}%
                              </td>
                              <td className="px-3 py-3 text-sm text-right text-gray-900">
                                {stock.close_price?.toFixed(2)}
                              </td>
                              <td className="px-3 py-3 text-sm text-right text-gray-600">
                                {stock.circulation_market_cap ? `${(stock.circulation_market_cap / 100000000).toFixed(1)}亿` : '-'}
                              </td>
                              <td className="px-3 py-3 text-sm text-right text-gray-600">
                                {stock.turnover_rate?.toFixed(2)}%
                              </td>
                              <td className="px-3 py-3 text-sm text-right text-gray-600">
                                {stock.sealed_amount ? `${(stock.sealed_amount / 100000000).toFixed(2)}亿` : '-'}
                              </td>
                              <td className="px-3 py-3 text-sm text-center text-gray-600">
                                {stock.first_limit_time || '-'}
                              </td>
                              <td className="px-3 py-3 text-sm text-center">
                                {stock.opening_times !== undefined && stock.opening_times !== null ? (
                                  <span className={stock.opening_times > 0 ? 'text-orange-600 font-medium' : 'text-gray-600'}>
                                    {stock.opening_times}
                                  </span>
                                ) : '-'}
                              </td>
                              <td className="px-3 py-3 text-sm text-center text-gray-600">
                                {stock.limit_stats || '-'}
                              </td>
                              <td className="px-3 py-3 text-sm text-center">
                                {stock.is_strong_limit ? (
                                  <span className="px-2 py-0.5 text-xs bg-red-100 text-red-600 rounded font-medium">
                                    一字板
                                  </span>
                                ) : (
                                  <span className="px-2 py-0.5 text-xs bg-yellow-100 text-yellow-700 rounded font-medium">
                                    换手板
                                  </span>
                                )}
                              </td>
                              <td className="px-3 py-3 text-sm text-gray-600">
                                {stock.industry || '-'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      暂无 {selectedContinuousDays}连板 股票数据
                    </div>
                  )}
                </div>
              )}
            </Card>
          </div>
        )}
      </div>
    </main>
  );
}
