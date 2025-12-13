'use client';

/**
 * 仪表盘主页面
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card } from '@/components/ui/card';
import { getMarketIndex, getMarketSentiment, getHotConcepts, getLimitStocks } from '@/lib/api';
import { format } from 'date-fns';
import { addToWatchlist, isInWatchlist } from '@/lib/watchlist';

export default function Dashboard() {
  // 当前选中的连板数（默认显示2板）
  const [selectedContinuousDays, setSelectedContinuousDays] = useState<number | null>(2);

  // Toast消息状态
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // 显示Toast消息
  const showToast = (message: string) => {
    setToastMessage(message);
    setTimeout(() => setToastMessage(null), 2000);
  };

  // 添加股票到自选池
  const handleAddToWatchlist = (stock: any, tradeDate: string) => {
    const success = addToWatchlist({
      stock_code: stock.stock_code,
      stock_name: stock.stock_name,
      continuous_days: stock.continuous_days,
      change_pct: stock.change_pct,
      close_price: stock.close_price,
      circulation_market_cap: stock.circulation_market_cap,
      turnover_rate: stock.turnover_rate,
      sealed_amount: stock.sealed_amount,
      main_net_inflow: stock.main_net_inflow,
      first_limit_time: stock.first_limit_time,
      opening_times: stock.opening_times,
      limit_stats: stock.limit_stats,
      is_strong_limit: stock.is_strong_limit,
      trade_date: tradeDate,
    });

    if (success) {
      showToast(`${stock.stock_name} 已添加到自选池`);
    } else {
      showToast(`${stock.stock_name} 已在自选池中`);
    }
  };

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
                        成交额:{' '}
                        <span className="font-medium">
                          {index.amount ? `${(index.amount / 100000000).toFixed(0)}亿` : '-'}
                        </span>
                      </div>
                      <div>
                        较昨日:{' '}
                        <span className={`font-medium ${
                          index.amount_change_pct !== undefined && index.amount_change_pct !== null
                            ? index.amount_change_pct >= 0 ? 'text-red-600' : 'text-green-600'
                            : ''
                        }`}>
                          {index.amount_change_pct !== undefined && index.amount_change_pct !== null
                            ? `${index.amount_change_pct >= 0 ? '+' : ''}${index.amount_change_pct.toFixed(1)}%`
                            : '-'}
                        </span>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>

            {/* 市场情绪 */}
            <Card
              title="市场情绪"
              subtitle={`涨跌分布与市场状态 - ${marketSentiment?.data.market_status || '加载中...'}`}
            >
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                {/* 第1列: 上涨占比 + 总成交额 */}
                <div>
                  <div className="text-sm text-gray-500">上涨股票占比</div>
                  <div className="flex items-baseline gap-2 mt-1">
                    <span
                      className={`text-2xl font-bold ${
                        (() => {
                          const upCount = marketSentiment?.data.up_count ?? 0;
                          const downCount = marketSentiment?.data.down_count ?? 0;
                          const total = upCount + downCount;
                          const upPct = total > 0 ? (upCount / total) * 100 : 0;
                          return upPct > 50 ? 'text-red-600' : 'text-green-600';
                        })()
                      }`}
                    >
                      {(() => {
                        const upCount = marketSentiment?.data.up_count ?? 0;
                        const downCount = marketSentiment?.data.down_count ?? 0;
                        const total = upCount + downCount;
                        return total > 0 ? ((upCount / total) * 100).toFixed(2) : '0.00';
                      })()}%
                    </span>
                    {(() => {
                      const upCount = marketSentiment?.data.up_count ?? 0;
                      const downCount = marketSentiment?.data.down_count ?? 0;
                      const prevUpCount = marketSentiment?.data.prev_up_count;
                      const prevDownCount = marketSentiment?.data.prev_down_count;

                      if (prevUpCount !== undefined && prevUpCount !== null &&
                          prevDownCount !== undefined && prevDownCount !== null) {
                        const total = upCount + downCount;
                        const prevTotal = prevUpCount + prevDownCount;
                        const currentPct = total > 0 ? (upCount / total) * 100 : 0;
                        const prevPct = prevTotal > 0 ? (prevUpCount / prevTotal) * 100 : 0;
                        const changePct = currentPct - prevPct;

                        return (
                          <span className={`text-xs ${changePct >= 0 ? 'text-red-500' : 'text-green-500'}`}>
                            {changePct >= 0 ? '+' : ''}{changePct.toFixed(1)}%
                          </span>
                        );
                      }
                      return null;
                    })()}
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
                {/* 第2-4列: 涨停/跌停/炸板率/情绪状态 + 情绪评分条 (上下布局) */}
                <div className="col-span-1 md:col-span-3">
                  {/* 上方: 涨停数、跌停数、炸板率、情绪状态 - 平铺展开 */}
                  <div className="grid grid-cols-4 gap-6 mb-4">
                    {/* 涨停数 */}
                    <div className="text-center">
                      <div className="text-sm text-gray-500">涨停数</div>
                      <div className="flex items-center justify-center gap-1 mt-1">
                        <span className="text-2xl font-bold text-red-600">
                          {marketSentiment?.data.limit_up_count ?? '-'}
                        </span>
                        {marketSentiment?.data.prev_limit_up_count !== undefined &&
                          marketSentiment?.data.prev_limit_up_count !== null &&
                          marketSentiment?.data.limit_up_count !== undefined && (
                            <span className={`text-lg ${
                              marketSentiment.data.limit_up_count > marketSentiment.data.prev_limit_up_count
                                ? 'text-red-500'
                                : marketSentiment.data.limit_up_count < marketSentiment.data.prev_limit_up_count
                                ? 'text-green-500'
                                : 'text-gray-400'
                            }`}>
                              {marketSentiment.data.limit_up_count > marketSentiment.data.prev_limit_up_count
                                ? '↑'
                                : marketSentiment.data.limit_up_count < marketSentiment.data.prev_limit_up_count
                                ? '↓'
                                : ''}
                            </span>
                          )}
                      </div>
                      <div className="text-xs text-gray-400">
                        {marketSentiment?.data.prev_limit_up_count !== undefined &&
                        marketSentiment?.data.prev_limit_up_count !== null
                          ? `昨日: ${marketSentiment.data.prev_limit_up_count}`
                          : ''}
                      </div>
                    </div>
                    {/* 跌停数 */}
                    <div className="text-center">
                      <div className="text-sm text-gray-500">跌停数</div>
                      <div className="flex items-center justify-center gap-1 mt-1">
                        <span className="text-2xl font-bold text-green-600">
                          {marketSentiment?.data.limit_down_count ?? '-'}
                        </span>
                        {marketSentiment?.data.prev_limit_down_count !== undefined &&
                          marketSentiment?.data.prev_limit_down_count !== null &&
                          marketSentiment?.data.limit_down_count !== undefined && (
                            <span className={`text-lg ${
                              marketSentiment.data.limit_down_count > marketSentiment.data.prev_limit_down_count
                                ? 'text-red-500'
                                : marketSentiment.data.limit_down_count < marketSentiment.data.prev_limit_down_count
                                ? 'text-green-500'
                                : 'text-gray-400'
                            }`}>
                              {marketSentiment.data.limit_down_count > marketSentiment.data.prev_limit_down_count
                                ? '↑'
                                : marketSentiment.data.limit_down_count < marketSentiment.data.prev_limit_down_count
                                ? '↓'
                                : ''}
                            </span>
                          )}
                      </div>
                      <div className="text-xs text-gray-400">
                        {marketSentiment?.data.prev_limit_down_count !== undefined &&
                        marketSentiment?.data.prev_limit_down_count !== null
                          ? `昨日: ${marketSentiment.data.prev_limit_down_count}`
                          : ''}
                      </div>
                    </div>
                    {/* 炸板率 */}
                    <div className="text-center">
                      <div className="text-sm text-gray-500">炸板率</div>
                      <div className="flex items-center justify-center gap-1 mt-1">
                        <span
                          className={`text-2xl font-bold ${
                            (marketSentiment?.data.explosion_rate ?? 0) > 30
                              ? 'text-red-600'
                              : 'text-green-600'
                          }`}
                        >
                          {marketSentiment?.data.explosion_rate?.toFixed(1) ?? '-'}%
                        </span>
                        {marketSentiment?.data.prev_explosion_rate !== undefined &&
                          marketSentiment?.data.prev_explosion_rate !== null &&
                          marketSentiment?.data.explosion_rate !== undefined && (
                            <span className={`text-lg ${
                              marketSentiment.data.explosion_rate > marketSentiment.data.prev_explosion_rate
                                ? 'text-red-500'
                                : marketSentiment.data.explosion_rate < marketSentiment.data.prev_explosion_rate
                                ? 'text-green-500'
                                : 'text-gray-400'
                            }`}>
                              {marketSentiment.data.explosion_rate > marketSentiment.data.prev_explosion_rate
                                ? '↑'
                                : marketSentiment.data.explosion_rate < marketSentiment.data.prev_explosion_rate
                                ? '↓'
                                : ''}
                            </span>
                          )}
                      </div>
                      <div className="text-xs text-gray-400">
                        {marketSentiment?.data.prev_explosion_rate !== undefined &&
                        marketSentiment?.data.prev_explosion_rate !== null
                          ? `昨日: ${marketSentiment.data.prev_explosion_rate.toFixed(1)}%`
                          : ''}
                      </div>
                    </div>
                    {/* 情绪状态 */}
                    {marketSentiment?.data.sentiment_score && (
                      <div className="text-center">
                        <div className="text-sm text-gray-500">情绪状态</div>
                        <div
                          className={`text-2xl font-bold mt-1 ${
                            marketSentiment.data.sentiment_score.sentiment_color === 'deep_red'
                              ? 'text-red-500'
                              : marketSentiment.data.sentiment_score.sentiment_color === 'orange'
                              ? 'text-orange-500'
                              : marketSentiment.data.sentiment_score.sentiment_color === 'yellow'
                              ? 'text-yellow-500'
                              : marketSentiment.data.sentiment_score.sentiment_color === 'gray'
                              ? 'text-gray-500'
                              : marketSentiment.data.sentiment_score.sentiment_color === 'blue'
                              ? 'text-blue-500'
                              : marketSentiment.data.sentiment_score.sentiment_color === 'green'
                              ? 'text-green-500'
                              : 'text-gray-500'
                          }`}
                        >
                          {marketSentiment.data.sentiment_score.sentiment_level}
                        </div>
                      </div>
                    )}
                  </div>
                  {/* 下方: 情绪评分条 - 使用grid对齐 */}
                  {marketSentiment?.data.sentiment_score && (
                    <div className="grid grid-cols-4 gap-6">
                      {/* 情绪条占3列 */}
                      <div className="col-span-3 relative">
                        <div className="h-6 rounded-full overflow-hidden flex border border-gray-200">
                          <div className="bg-green-400 h-full" style={{ width: '18.18%' }} />
                          <div className="bg-blue-400 h-full" style={{ width: '18.18%' }} />
                          <div className="bg-yellow-400 h-full" style={{ width: '9.09%' }} />
                          <div className="bg-gray-300 h-full" style={{ width: '9.09%' }} />
                          <div className="bg-yellow-400 h-full" style={{ width: '9.09%' }} />
                          <div className="bg-orange-400 h-full" style={{ width: '18.18%' }} />
                          <div className="bg-red-500 h-full" style={{ width: '18.18%' }} />
                        </div>
                        <div
                          className="absolute top-0 transform -translate-x-1/2"
                          style={{
                            left: `${((marketSentiment.data.sentiment_score.total_score + 5) / 10) * 100}%`
                          }}
                        >
                          <div className="w-0 h-0 border-l-[6px] border-r-[6px] border-t-[8px] border-l-transparent border-r-transparent border-t-gray-700 -mt-2" />
                        </div>
                        <div className="relative mt-0.5 h-4">
                          {[-5, -3, -1, 0, 1, 3, 5].map((num) => (
                            <div
                              key={num}
                              className="absolute flex flex-col items-center transform -translate-x-1/2"
                              style={{ left: `${((num + 5) / 10) * 100}%` }}
                            >
                              <div className="w-px h-1.5 bg-gray-300" />
                              <span className="text-[10px] text-gray-400">{num > 0 ? `+${num}` : num}</span>
                            </div>
                          ))}
                        </div>
                        {/* 评分明细标签 */}
                        <div className="flex justify-center gap-3 mt-2 text-[10px]">
                          <span className={`px-1.5 py-0.5 rounded ${marketSentiment.data.sentiment_score.up_ratio_score > 0 ? 'bg-red-50 text-red-600' : marketSentiment.data.sentiment_score.up_ratio_score < 0 ? 'bg-green-50 text-green-600' : 'bg-gray-50 text-gray-500'}`}>
                            涨跌{marketSentiment.data.sentiment_score.up_ratio_score > 0 ? '+1' : marketSentiment.data.sentiment_score.up_ratio_score < 0 ? '-1' : '0'}
                          </span>
                          <span className={`px-1.5 py-0.5 rounded ${marketSentiment.data.sentiment_score.amount_change_score > 0 ? 'bg-red-50 text-red-600' : marketSentiment.data.sentiment_score.amount_change_score < 0 ? 'bg-green-50 text-green-600' : 'bg-gray-50 text-gray-500'}`}>
                            量能{marketSentiment.data.sentiment_score.amount_change_score > 0 ? '+1' : marketSentiment.data.sentiment_score.amount_change_score < 0 ? '-1' : '0'}
                          </span>
                          <span className={`px-1.5 py-0.5 rounded ${marketSentiment.data.sentiment_score.limit_up_score > 0 ? 'bg-red-50 text-red-600' : marketSentiment.data.sentiment_score.limit_up_score < 0 ? 'bg-green-50 text-green-600' : 'bg-gray-50 text-gray-500'}`}>
                            涨停{marketSentiment.data.sentiment_score.limit_up_score > 0 ? '+1' : marketSentiment.data.sentiment_score.limit_up_score < 0 ? '-1' : '0'}
                          </span>
                          <span className={`px-1.5 py-0.5 rounded ${marketSentiment.data.sentiment_score.limit_down_score > 0 ? 'bg-red-50 text-red-600' : marketSentiment.data.sentiment_score.limit_down_score < 0 ? 'bg-green-50 text-green-600' : 'bg-gray-50 text-gray-500'}`}>
                            跌停{marketSentiment.data.sentiment_score.limit_down_score > 0 ? '+1' : marketSentiment.data.sentiment_score.limit_down_score < 0 ? '-1' : '0'}
                          </span>
                          <span className={`px-1.5 py-0.5 rounded ${marketSentiment.data.sentiment_score.explosion_rate_score > 0 ? 'bg-red-50 text-red-600' : marketSentiment.data.sentiment_score.explosion_rate_score < 0 ? 'bg-green-50 text-green-600' : 'bg-gray-50 text-gray-500'}`}>
                            炸板{marketSentiment.data.sentiment_score.explosion_rate_score > 0 ? '+1' : marketSentiment.data.sentiment_score.explosion_rate_score < 0 ? '-1' : '0'}
                          </span>
                        </div>
                      </div>
                      {/* 第4列留空，与上方"情绪状态"对齐 */}
                      <div></div>
                    </div>
                  )}
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
                            <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">主力净额</th>
                            <th className="px-3 py-2 text-center text-xs font-medium text-gray-500">首次封板时间</th>
                            <th className="px-3 py-2 text-center text-xs font-medium text-gray-500">炸板次数</th>
                            <th className="px-3 py-2 text-center text-xs font-medium text-gray-500">涨停统计</th>
                            <th className="px-3 py-2 text-center text-xs font-medium text-gray-500">封板类型</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {limitStocks.data.map((stock, index) => (
                            <tr key={stock.stock_code} className="hover:bg-gray-50">
                              <td className="px-3 py-3 text-sm text-center text-gray-500">{index + 1}</td>
                              <td className="px-3 py-3 text-sm text-gray-600">{stock.stock_code}</td>
                              <td className="px-3 py-3 text-sm">
                                <div className="flex items-center gap-2">
                                  <span className="font-medium text-gray-900">{stock.stock_name}</span>
                                  <button
                                    onClick={() => handleAddToWatchlist(stock, marketSentiment?.data.trade_date || '')}
                                    className="w-5 h-5 flex items-center justify-center rounded bg-blue-50 hover:bg-blue-100 text-blue-600 hover:text-blue-700 transition-colors"
                                    title="添加到自选池"
                                  >
                                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M12 4v16m8-8H4" />
                                    </svg>
                                  </button>
                                </div>
                              </td>
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
                              <td className="px-3 py-3 text-sm text-right">
                                {stock.main_net_inflow !== undefined && stock.main_net_inflow !== null ? (
                                  <span className={stock.main_net_inflow >= 0 ? 'text-red-600 font-medium' : 'text-green-600 font-medium'}>
                                    {stock.main_net_inflow >= 0 ? '+' : ''}{(stock.main_net_inflow / 100000000).toFixed(2)}亿
                                  </span>
                                ) : '-'}
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

      {/* Toast 提示 */}
      {toastMessage && (
        <div className="fixed bottom-8 right-8 bg-gray-900 text-white px-6 py-3 rounded-lg shadow-lg animate-fade-in-up z-50">
          {toastMessage}
        </div>
      )}
    </main>
  );
}
