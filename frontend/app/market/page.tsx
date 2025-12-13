'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import dynamic from 'next/dynamic';

// 动态导入ECharts避免SSR问题
const ReactECharts = dynamic(() => import('echarts-for-react'), { ssr: false });

// 通用K线图配置生成函数
const getKlineOption = (klineData: any[], showLegend: boolean = true) => {
  if (klineData.length === 0) return {};

  // 日期数据
  const dates = klineData.map((item: any) => item.trade_date);

  // K线数据格式: [开盘, 收盘, 最低, 最高]
  const klineValues = klineData.map((item: any) => [
    item.open_price,
    item.close_price,
    item.low_price,
    item.high_price
  ]);

  // 找出最高点和最低点
  let maxHighIndex = 0;
  let minLowIndex = 0;
  let maxHigh = klineData[0]?.high_price || 0;
  let minLow = klineData[0]?.low_price || Infinity;

  klineData.forEach((item: any, index: number) => {
    if (item.high_price > maxHigh) {
      maxHigh = item.high_price;
      maxHighIndex = index;
    }
    if (item.low_price < minLow) {
      minLow = item.low_price;
      minLowIndex = index;
    }
  });

  // 直接从数据库获取均线数据
  const getMAData = (maField: 'ma5' | 'ma10' | 'ma20') => {
    return klineData.map((item: any) =>
      item[maField] != null ? item[maField].toFixed(2) : null
    );
  };

  return {
    animation: false,
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: function (params: any) {
        const kline = params.find((p: any) => p.seriesName === 'K线');
        if (!kline) return '';
        const data = klineData[kline.dataIndex];
        return `
          <div style="font-size:12px;">
            <div style="font-weight:bold;margin-bottom:4px;">${data.trade_date}</div>
            <div>开盘: ${data.open_price.toFixed(2)}</div>
            <div>收盘: ${data.close_price.toFixed(2)}</div>
            <div>最高: ${data.high_price.toFixed(2)}</div>
            <div>最低: ${data.low_price.toFixed(2)}</div>
            <div>涨跌幅: <span style="color:${data.change_pct >= 0 ? '#ef4444' : '#22c55e'}">${data.change_pct >= 0 ? '+' : ''}${data.change_pct.toFixed(2)}%</span></div>
            <div>成交额: ${(data.amount / 100000000).toFixed(0)}亿元</div>
            <div style="margin-top:4px;border-top:1px solid #eee;padding-top:4px;">
              <span style="color:#000000">MA5: ${data.ma5?.toFixed(2) || '-'}</span>
              <span style="margin-left:8px;color:#eab308">MA10: ${data.ma10?.toFixed(2) || '-'}</span>
              <span style="margin-left:8px;color:#ec4899">MA20: ${data.ma20?.toFixed(2) || '-'}</span>
            </div>
          </div>
        `;
      }
    },
    legend: {
      show: showLegend,
      data: [
        { name: 'K线', itemStyle: { color: '#ef4444' } },
        { name: 'MA5', itemStyle: { color: '#000000' } },
        { name: 'MA10', itemStyle: { color: '#eab308' } },
        { name: 'MA20', itemStyle: { color: '#ec4899' } }
      ],
      top: 10
    },
    grid: {
      left: '10%',
      right: '10%',
      top: 60,
      bottom: 60
    },
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: true,
      axisLine: { lineStyle: { color: '#777' } },
      axisLabel: {
        formatter: function (value: string) {
          return value.substring(5); // 只显示月-日
        }
      },
      min: 'dataMin',
      max: 'dataMax'
    },
    yAxis: {
      scale: true,
      splitArea: {
        show: true
      },
      axisLine: { lineStyle: { color: '#777' } },
      splitLine: { lineStyle: { color: '#eee' } }
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      }
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: klineValues,
        itemStyle: {
          color: '#ef4444',        // 上涨颜色（红色）
          color0: '#22c55e',       // 下跌颜色（绿色）
          borderColor: '#ef4444',
          borderColor0: '#22c55e'
        },
        markPoint: {
          symbol: 'pin',
          symbolSize: 50,
          data: [
            {
              name: '最高',
              coord: [maxHighIndex, maxHigh],
              value: maxHigh.toFixed(2),
              itemStyle: { color: '#ef4444' },
              label: {
                formatter: '最高\n{c}',
                color: '#fff',
                fontSize: 10
              }
            },
            {
              name: '最低',
              coord: [minLowIndex, minLow],
              value: minLow.toFixed(2),
              itemStyle: { color: '#22c55e' },
              label: {
                formatter: '最低\n{c}',
                color: '#fff',
                fontSize: 10
              },
              symbolRotate: 180
            }
          ]
        }
      },
      {
        name: 'MA5',
        type: 'line',
        data: getMAData('ma5'),
        smooth: true,
        lineStyle: { width: 1.5, color: '#000000' },  // 黑色
        symbol: 'none',
        connectNulls: true  // 连接null值处的断点
      },
      {
        name: 'MA10',
        type: 'line',
        data: getMAData('ma10'),
        smooth: true,
        lineStyle: { width: 1.5, color: '#eab308' },  // 黄色
        symbol: 'none',
        connectNulls: true  // 连接null值处的断点
      },
      {
        name: 'MA20',
        type: 'line',
        data: getMAData('ma20'),
        smooth: true,
        lineStyle: { width: 1.5, color: '#ec4899' },  // 粉色
        symbol: 'none',
        connectNulls: true  // 连接null值处的断点
      }
    ]
  };
};

export default function MarketAnalysisPage() {
  // 获取上证指数60日K线数据
  const { data: shResponse, isLoading: shLoading } = useQuery({
    queryKey: ['index-history', 'SH000001', 60],
    queryFn: () => apiClient.get('/api/market/index/history?index_code=SH000001&days=60'),
  });

  // 获取深证成指60日K线数据
  const { data: szResponse, isLoading: szLoading } = useQuery({
    queryKey: ['index-history', 'SZ399001', 60],
    queryFn: () => apiClient.get('/api/market/index/history?index_code=SZ399001&days=60'),
  });

  // 获取创业板指60日K线数据
  const { data: cybResponse, isLoading: cybLoading } = useQuery({
    queryKey: ['index-history', 'SZ399006', 60],
    queryFn: () => apiClient.get('/api/market/index/history?index_code=SZ399006&days=60'),
  });

  // 获取历史成交额数据
  const { data: sentimentHistoryResponse, isLoading: sentimentHistoryLoading } = useQuery({
    queryKey: ['sentiment-history', 60],
    queryFn: () => apiClient.get('/api/market/sentiment/history?days=60'),
  });

  // 从axios响应中提取实际数据
  const shIndexData = shResponse?.data;
  const shKlineData = shIndexData?.data || [];
  const shTrendAnalysis = shIndexData?.trend_analysis;

  const szIndexData = szResponse?.data;
  const szKlineData = szIndexData?.data || [];
  const szTrendAnalysis = szIndexData?.trend_analysis;

  const cybIndexData = cybResponse?.data;
  const cybKlineData = cybIndexData?.data || [];

  const sentimentHistoryData = sentimentHistoryResponse?.data?.data || [];

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">大盘分析</h1>
        <p className="text-sm text-gray-500">
          数据日期: {shKlineData.length > 0 ? shKlineData[shKlineData.length - 1]?.trade_date : '加载中...'}
        </p>
      </div>

      {/* 上证指数走势判断卡片 */}
      {shTrendAnalysis && shTrendAnalysis.trend && (
        <Card>
          <CardContent className="pt-6">
            <div className="mb-3">
              <h2 className="text-xl font-bold text-blue-600">上证指数</h2>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold mb-2">
                  走势判断: <span className={`${
                    shTrendAnalysis.trend === '上涨' ? 'text-red-500' :
                    shTrendAnalysis.trend === '下跌' ? 'text-green-500' : 'text-blue-600'
                  }`}>{shTrendAnalysis.trend}</span>
                </h3>
                <p className="text-sm text-gray-500">
                  {shTrendAnalysis.description}
                </p>
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold">
                  {shTrendAnalysis.current_price}
                </div>
                <div className={`text-sm ${shTrendAnalysis.change_5d >= 0 ? 'text-red-500' : 'text-green-500'}`}>
                  近5日: {shTrendAnalysis.change_5d >= 0 ? '+' : ''}{shTrendAnalysis.change_5d.toFixed(2)}%
                </div>
              </div>
            </div>

            {/* 均线数据 */}
            <div className="grid grid-cols-3 gap-4 mt-4">
              <div className="text-center p-3 bg-gray-50 rounded">
                <div className="text-sm text-gray-500 mb-2">MA5</div>
                <div className={`text-4xl font-bold ${
                  shTrendAnalysis.ma5_position === 'above' ? 'text-red-500' :
                  shTrendAnalysis.ma5_position === 'below' ? 'text-green-500' : 'text-gray-500'
                }`}>
                  {shTrendAnalysis.ma5_position === 'above' ? '高' :
                   shTrendAnalysis.ma5_position === 'below' ? '破' : '平'}
                </div>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded">
                <div className="text-sm text-gray-500 mb-2">MA10</div>
                <div className={`text-4xl font-bold ${
                  shTrendAnalysis.ma10_position === 'above' ? 'text-red-500' :
                  shTrendAnalysis.ma10_position === 'below' ? 'text-green-500' : 'text-gray-500'
                }`}>
                  {shTrendAnalysis.ma10_position === 'above' ? '高' :
                   shTrendAnalysis.ma10_position === 'below' ? '破' : '平'}
                </div>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded">
                <div className="text-sm text-gray-500 mb-2">MA20</div>
                <div className={`text-4xl font-bold ${
                  shTrendAnalysis.ma20_position === 'above' ? 'text-red-500' :
                  shTrendAnalysis.ma20_position === 'below' ? 'text-green-500' : 'text-gray-500'
                }`}>
                  {shTrendAnalysis.ma20_position === 'above' ? '高' :
                   shTrendAnalysis.ma20_position === 'below' ? '破' : '平'}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 深证成指走势判断卡片 */}
      {szTrendAnalysis && szTrendAnalysis.trend && (
        <Card>
          <CardContent className="pt-6">
            <div className="mb-3">
              <h2 className="text-xl font-bold text-green-600">深证成指</h2>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold mb-2">
                  走势判断: <span className={`${
                    szTrendAnalysis.trend === '上涨' ? 'text-red-500' :
                    szTrendAnalysis.trend === '下跌' ? 'text-green-500' : 'text-blue-600'
                  }`}>{szTrendAnalysis.trend}</span>
                </h3>
                <p className="text-sm text-gray-500">
                  {szTrendAnalysis.description}
                </p>
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold">
                  {szTrendAnalysis.current_price}
                </div>
                <div className={`text-sm ${szTrendAnalysis.change_5d >= 0 ? 'text-red-500' : 'text-green-500'}`}>
                  近5日: {szTrendAnalysis.change_5d >= 0 ? '+' : ''}{szTrendAnalysis.change_5d.toFixed(2)}%
                </div>
              </div>
            </div>

            {/* 均线数据 */}
            <div className="grid grid-cols-3 gap-4 mt-4">
              <div className="text-center p-3 bg-gray-50 rounded">
                <div className="text-sm text-gray-500 mb-2">MA5</div>
                <div className={`text-4xl font-bold ${
                  szTrendAnalysis.ma5_position === 'above' ? 'text-red-500' :
                  szTrendAnalysis.ma5_position === 'below' ? 'text-green-500' : 'text-gray-500'
                }`}>
                  {szTrendAnalysis.ma5_position === 'above' ? '高' :
                   szTrendAnalysis.ma5_position === 'below' ? '破' : '平'}
                </div>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded">
                <div className="text-sm text-gray-500 mb-2">MA10</div>
                <div className={`text-4xl font-bold ${
                  szTrendAnalysis.ma10_position === 'above' ? 'text-red-500' :
                  szTrendAnalysis.ma10_position === 'below' ? 'text-green-500' : 'text-gray-500'
                }`}>
                  {szTrendAnalysis.ma10_position === 'above' ? '高' :
                   szTrendAnalysis.ma10_position === 'below' ? '破' : '平'}
                </div>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded">
                <div className="text-sm text-gray-500 mb-2">MA20</div>
                <div className={`text-4xl font-bold ${
                  szTrendAnalysis.ma20_position === 'above' ? 'text-red-500' :
                  szTrendAnalysis.ma20_position === 'below' ? 'text-green-500' : 'text-gray-500'
                }`}>
                  {szTrendAnalysis.ma20_position === 'above' ? '高' :
                   szTrendAnalysis.ma20_position === 'below' ? '破' : '平'}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 三大指数K线图并排展示 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* 上证指数K线图 */}
        <Card>
          <CardHeader>
            <CardTitle>上证指数（近60日）</CardTitle>
          </CardHeader>
          <CardContent>
            {shLoading ? (
              <div className="text-center py-12 text-gray-500">
                加载中...
              </div>
            ) : shKlineData.length > 0 ? (
              <ReactECharts
                option={getKlineOption(shKlineData)}
                style={{ height: '400px', width: '100%' }}
                notMerge={true}
              />
            ) : (
              <div className="text-center py-12 text-gray-500">
                暂无数据
              </div>
            )}
          </CardContent>
        </Card>

        {/* 深证成指K线图 */}
        <Card>
          <CardHeader>
            <CardTitle>深证成指（近60日）</CardTitle>
          </CardHeader>
          <CardContent>
            {szLoading ? (
              <div className="text-center py-12 text-gray-500">
                加载中...
              </div>
            ) : szKlineData.length > 0 ? (
              <ReactECharts
                option={getKlineOption(szKlineData, false)}
                style={{ height: '400px', width: '100%' }}
                notMerge={true}
              />
            ) : (
              <div className="text-center py-12 text-gray-500">
                暂无数据
              </div>
            )}
          </CardContent>
        </Card>

        {/* 创业板指K线图 */}
        <Card>
          <CardHeader>
            <CardTitle>创业板指（近60日）</CardTitle>
          </CardHeader>
          <CardContent>
            {cybLoading ? (
              <div className="text-center py-12 text-gray-500">
                加载中...
              </div>
            ) : cybKlineData.length > 0 ? (
              <ReactECharts
                option={getKlineOption(cybKlineData, false)}
                style={{ height: '400px', width: '100%' }}
                notMerge={true}
              />
            ) : (
              <div className="text-center py-12 text-gray-500">
                暂无数据
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 大盘每日总成交额柱状图 */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>两市每日总成交额（近60日）</CardTitle>
          {sentimentHistoryData.length > 0 && (() => {
            const latestData = sentimentHistoryData[sentimentHistoryData.length - 1];
            const prevData = sentimentHistoryData.length > 1 ? sentimentHistoryData[sentimentHistoryData.length - 2] : null;
            const todayAmount = Math.round(latestData.total_amount / 100000000);
            const changePct = prevData
              ? ((latestData.total_amount - prevData.total_amount) / prevData.total_amount * 100)
              : 0;
            const isUp = changePct >= 0;
            return (
              <div className="text-right">
                <div className="text-2xl font-bold">{todayAmount.toLocaleString()}<span className="text-sm font-normal text-gray-500 ml-1">亿</span></div>
                <div className={`text-xs ${isUp ? 'text-red-500' : 'text-green-500'}`}>
                  较昨日: {isUp ? '+' : ''}{changePct.toFixed(2)}%
                </div>
              </div>
            );
          })()}
        </CardHeader>
        <CardContent>
          {sentimentHistoryLoading ? (
            <div className="text-center py-12 text-gray-500">
              加载中...
            </div>
          ) : sentimentHistoryData.length > 0 ? (
            <ReactECharts
              option={{
                animation: false,
                tooltip: {
                  trigger: 'axis',
                  formatter: function (params: any) {
                    const data = params[0];
                    const item = sentimentHistoryData[data.dataIndex];
                    return `<div style="font-size:12px;">
                      <div style="font-weight:bold;margin-bottom:4px;">${data.name}</div>
                      <div>成交额: ${data.value}亿元</div>
                      <div>涨: ${item.up_count} / 跌: ${item.down_count}</div>
                    </div>`;
                  }
                },
                grid: {
                  left: '3%',
                  right: '3%',
                  top: 40,
                  bottom: 60,
                  containLabel: true
                },
                xAxis: {
                  type: 'category',
                  data: sentimentHistoryData.map((item: any) => item.trade_date),
                  axisLine: { lineStyle: { color: '#777' } },
                  axisLabel: {
                    formatter: function (value: string) {
                      return value.substring(5);
                    },
                    rotate: 45
                  }
                },
                yAxis: {
                  type: 'value',
                  name: '成交额(亿元)',
                  axisLine: { lineStyle: { color: '#777' } },
                  splitLine: { lineStyle: { color: '#eee' } }
                },
                dataZoom: [{ type: 'inside', start: 0, end: 100 }],
                series: [{
                  name: '成交额',
                  type: 'bar',
                  data: sentimentHistoryData.map((item: any, index: number) => {
                    const currentAmount = item.total_amount;
                    const prevAmount = index > 0 ? sentimentHistoryData[index - 1].total_amount : currentAmount;
                    const isVolumeUp = currentAmount >= prevAmount; // 放量用红色，缩量用绿色
                    return {
                      value: Math.round(currentAmount / 100000000),
                      itemStyle: {
                        color: isVolumeUp ? '#ef4444' : '#22c55e'
                      }
                    };
                  }),
                  barWidth: '60%'
                }]
              }}
              style={{ height: '300px', width: '100%' }}
              notMerge={true}
            />
          ) : (
            <div className="text-center py-12 text-gray-500">
              暂无数据
            </div>
          )}
        </CardContent>
      </Card>

    </div>
  );
}
