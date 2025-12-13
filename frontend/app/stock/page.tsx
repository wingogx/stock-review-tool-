'use client'

import { useState, useEffect } from 'react'
import { PremiumScoreResponse } from '@/types/api'
import { getWatchlist, removeFromWatchlist, WatchlistStock } from '@/lib/watchlist'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// 等级颜色映射
const getLevelColor = (level: string): string => {
  const colorMap: Record<string, string> = {
    '极高': 'bg-red-600 text-white',
    '高': 'bg-orange-500 text-white',
    '偏高': 'bg-yellow-500 text-white',
    '中性': 'bg-gray-400 text-white',
    '偏低': 'bg-blue-400 text-white',
    '低': 'bg-green-500 text-white',
  }
  return colorMap[level] || 'bg-gray-400 text-white'
}

// 得分颜色（根据分数）
const getScoreColor = (score: number): string => {
  if (score >= 1.5) return 'text-red-600 font-bold'
  if (score >= 0.5) return 'text-orange-500 font-semibold'
  if (score >= -0.5) return 'text-gray-600'
  if (score >= -1.5) return 'text-blue-500 font-semibold'
  return 'text-green-600 font-bold'
}

export default function StockAnalysisPage() {
  const [stockCode, setStockCode] = useState('')
  const [tradeDate, setTradeDate] = useState('')
  const [loading, setLoading] = useState(false)
  const [scoreData, setScoreData] = useState<PremiumScoreResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  // 自选池状态
  const [watchlist, setWatchlist] = useState<WatchlistStock[]>([])

  // 选中的股票（用于批量评测）
  const [selectedStocks, setSelectedStocks] = useState<Set<string>>(new Set())

  // 评测结果存储 { "stockCode_tradeDate": { score, level } }
  const [scoreResults, setScoreResults] = useState<Record<string, { score: number; level: string; color: string }>>({})

  // 批量评测状态
  const [batchEvaluating, setBatchEvaluating] = useState(false)
  const [evaluateProgress, setEvaluateProgress] = useState({ current: 0, total: 0 })

  // 加载自选池
  useEffect(() => {
    setWatchlist(getWatchlist())
  }, [])

  // 从自选池移除股票
  const handleRemoveFromWatchlist = (stockCode: string, tradeDate: string) => {
    removeFromWatchlist(stockCode, tradeDate)
    setWatchlist(getWatchlist())
    // 同时从选中列表中移除
    const newSelected = new Set(selectedStocks)
    newSelected.delete(`${stockCode}_${tradeDate}`)
    setSelectedStocks(newSelected)
  }

  // 切换复选框
  const toggleStockSelection = (stockCode: string, tradeDate: string) => {
    const key = `${stockCode}_${tradeDate}`
    const newSelected = new Set(selectedStocks)
    if (newSelected.has(key)) {
      newSelected.delete(key)
    } else {
      newSelected.add(key)
    }
    setSelectedStocks(newSelected)
  }

  // 全选/取消全选
  const toggleSelectAll = () => {
    if (selectedStocks.size === watchlist.length) {
      setSelectedStocks(new Set())
    } else {
      const allKeys = watchlist.map(s => `${s.stock_code}_${s.trade_date}`)
      setSelectedStocks(new Set(allKeys))
    }
  }

  // 批量评测
  const handleBatchEvaluate = async () => {
    console.log('=== 批量评测开始 ===')
    console.log('选中的股票数量:', selectedStocks.size)
    console.log('选中的股票keys:', Array.from(selectedStocks))
    console.log('自选池总数:', watchlist.length)
    console.log('自选池数据:', watchlist)

    if (selectedStocks.size === 0) {
      alert('请先选择要评测的股票')
      return
    }

    setBatchEvaluating(true)

    const selectedList = watchlist.filter(s =>
      selectedStocks.has(`${s.stock_code}_${s.trade_date}`)
    )

    console.log(`筛选后准备评测 ${selectedList.length} 只股票:`, selectedList)

    if (selectedList.length === 0) {
      console.error('❌ 错误：筛选后没有找到匹配的股票！')
      alert('未找到匹配的股票，请检查自选池数据')
      setBatchEvaluating(false)
      return
    }

    setEvaluateProgress({ current: 0, total: selectedList.length })

    for (let i = 0; i < selectedList.length; i++) {
      const stock = selectedList[i]
      console.log(`[${i + 1}/${selectedList.length}] 正在评测: ${stock.stock_name} (${stock.stock_code})`)
      console.log(`原始trade_date: ${stock.trade_date}`)

      // 转换日期格式：YYYYMMDD -> YYYY-MM-DD
      let formattedDate = stock.trade_date
      if (stock.trade_date && stock.trade_date.length === 8 && !stock.trade_date.includes('-')) {
        formattedDate = `${stock.trade_date.substring(0, 4)}-${stock.trade_date.substring(4, 6)}-${stock.trade_date.substring(6, 8)}`
      }
      console.log(`格式化后trade_date: ${formattedDate}`)

      try {
        const url = `${API_BASE_URL}/api/stock/premium-score?stock_code=${stock.stock_code}&trade_date=${formattedDate}`
        console.log(`API URL: ${url}`)
        const response = await fetch(url)

        if (response.ok) {
          const data: PremiumScoreResponse = await response.json()
          const stockKey = `${stock.stock_code}_${stock.trade_date}`

          // 立即更新结果，让用户看到实时反馈
          setScoreResults(prev => ({
            ...prev,
            [stockKey]: {
              score: data.data.total_score,
              level: data.data.premium_level,
              color: data.data.premium_level_color
            }
          }))

          console.log(`✓ ${stock.stock_name} 评测完成，得分: ${data.data.total_score}`)
        } else {
          console.error(`✗ ${stock.stock_name} 评测失败: HTTP ${response.status}`)
        }
      } catch (err) {
        console.error(`✗ ${stock.stock_name} 评测失败:`, err)
      }

      // 更新进度
      setEvaluateProgress({ current: i + 1, total: selectedList.length })
    }

    console.log('批量评测完成！')
    setBatchEvaluating(false)
  }

  const fetchPremiumScore = async () => {
    if (!stockCode || !/^\d{6}$/.test(stockCode)) {
      setError('请输入有效的6位股票代码')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const url = tradeDate
        ? `${API_BASE_URL}/api/stock/premium-score?stock_code=${stockCode}&trade_date=${tradeDate}`
        : `${API_BASE_URL}/api/stock/premium-score?stock_code=${stockCode}`

      const response = await fetch(url)

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || '获取评分失败')
      }

      const data: PremiumScoreResponse = await response.json()
      setScoreData(data)
    } catch (err: any) {
      setError(err.message || '网络请求失败')
      setScoreData(null)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      fetchPremiumScore()
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* 页面标题 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">个股分析</h1>
          <p className="text-gray-600">
            自选池管理与个股明日溢价概率评分
          </p>
        </div>

        {/* 自选池卡片 */}
        {watchlist.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-4">
                <h2 className="text-xl font-semibold text-gray-900">
                  自选池 ({watchlist.length})
                </h2>
                <button
                  onClick={handleBatchEvaluate}
                  disabled={batchEvaluating || selectedStocks.size === 0}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors text-sm font-medium"
                >
                  {batchEvaluating ? `评测中... (${evaluateProgress.current}/${evaluateProgress.total})` : '开始评测'}
                </button>
                {selectedStocks.size > 0 && (
                  <span className="text-sm text-gray-600">
                    已选 {selectedStocks.size} 只
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-500">勾选股票后点击评测</p>
            </div>

            {/* 评分说明 */}
            <div className="mb-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm font-medium text-gray-700">评分说明（10分制）：</span>
                <div className="flex items-center gap-1">
                  <span className="px-2 py-1 text-xs rounded font-medium bg-red-600 text-white">极高</span>
                  <span className="text-xs text-gray-600">≥8分</span>
                </div>
                <span className="text-gray-300">|</span>
                <div className="flex items-center gap-1">
                  <span className="px-2 py-1 text-xs rounded font-medium bg-orange-500 text-white">高</span>
                  <span className="text-xs text-gray-600">7~8分</span>
                </div>
                <span className="text-gray-300">|</span>
                <div className="flex items-center gap-1">
                  <span className="px-2 py-1 text-xs rounded font-medium bg-yellow-500 text-white">偏高</span>
                  <span className="text-xs text-gray-600">6~7分</span>
                </div>
                <span className="text-gray-300">|</span>
                <div className="flex items-center gap-1">
                  <span className="px-2 py-1 text-xs rounded font-medium bg-gray-400 text-white">中性</span>
                  <span className="text-xs text-gray-600">5~6分</span>
                </div>
                <span className="text-gray-300">|</span>
                <div className="flex items-center gap-1">
                  <span className="px-2 py-1 text-xs rounded font-medium bg-blue-400 text-white">偏低</span>
                  <span className="text-xs text-gray-600">4~5分</span>
                </div>
                <span className="text-gray-300">|</span>
                <div className="flex items-center gap-1">
                  <span className="px-2 py-1 text-xs rounded font-medium bg-green-500 text-white">低</span>
                  <span className="text-xs text-gray-600">&lt;4分</span>
                </div>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-center text-xs font-medium text-gray-500">
                      <input
                        type="checkbox"
                        checked={watchlist.length > 0 && selectedStocks.size === watchlist.length}
                        onChange={toggleSelectAll}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500 cursor-pointer"
                      />
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">代码</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">名称</th>
                    <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">最新价</th>
                    <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">流通市值</th>
                    <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">换手率</th>
                    <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">封板资金</th>
                    <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">主力净额</th>
                    <th className="px-3 py-2 text-center text-xs font-medium text-gray-500">首次封板时间</th>
                    <th className="px-3 py-2 text-center text-xs font-medium text-gray-500">炸板次数</th>
                    <th className="px-3 py-2 text-center text-xs font-medium text-gray-500">封板类型</th>
                    <th className="px-3 py-2 text-center text-xs font-medium text-gray-500">评测分值</th>
                    <th className="px-3 py-2 text-center text-xs font-medium text-gray-500">溢价等级</th>
                    <th className="px-3 py-2 text-center text-xs font-medium text-gray-500">操作</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {watchlist.map((stock, index) => {
                    const stockKey = `${stock.stock_code}_${stock.trade_date}`
                    const isSelected = selectedStocks.has(stockKey)
                    const scoreResult = scoreResults[stockKey]

                    return (
                    <tr key={`${stock.stock_code}-${stock.trade_date}`} className="hover:bg-gray-50">
                      <td className="px-3 py-3 text-sm text-center">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleStockSelection(stock.stock_code, stock.trade_date)}
                          className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500 cursor-pointer"
                        />
                      </td>
                      <td className="px-3 py-3 text-sm text-gray-600">{stock.stock_code}</td>
                      <td className="px-3 py-3 text-sm">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900">{stock.stock_name}</span>
                          {stock.continuous_days > 1 && (
                            <span className="px-1.5 py-0.5 text-xs bg-red-100 text-red-600 rounded">
                              {stock.continuous_days}连板
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-3 py-3 text-sm text-right text-gray-900">
                        {stock.close_price?.toFixed(2) || '-'}
                      </td>
                      <td className="px-3 py-3 text-sm text-right text-gray-600">
                        {stock.circulation_market_cap ? `${(stock.circulation_market_cap / 100000000).toFixed(1)}亿` : '-'}
                      </td>
                      <td className="px-3 py-3 text-sm text-right text-gray-600">
                        {stock.turnover_rate !== undefined ? `${stock.turnover_rate.toFixed(2)}%` : '-'}
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
                      {/* 评测分值 */}
                      <td className="px-3 py-3 text-sm text-center">
                        {scoreResult ? (
                          <span className={`font-bold ${
                            scoreResult.score >= 8 ? 'text-red-600' :
                            scoreResult.score >= 7 ? 'text-orange-500' :
                            scoreResult.score >= 6 ? 'text-yellow-600' :
                            scoreResult.score >= 5 ? 'text-gray-600' :
                            scoreResult.score >= 4 ? 'text-blue-500' :
                            'text-green-600'
                          }`}>
                            {scoreResult.score.toFixed(1)}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      {/* 溢价等级 */}
                      <td className="px-3 py-3 text-sm text-center">
                        {scoreResult ? (
                          <span className={`px-2 py-1 text-xs rounded font-medium ${getLevelColor(scoreResult.level)}`}>
                            {scoreResult.level}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-3 py-3 text-sm text-center">
                        <button
                          onClick={() => handleRemoveFromWatchlist(stock.stock_code, stock.trade_date)}
                          className="text-red-600 hover:text-red-800 font-medium"
                          title="从自选池移除"
                        >
                          移除
                        </button>
                      </td>
                    </tr>
                  )}
                  )}
                </tbody>
              </table>
            </div>

            <div className="mt-4 text-xs text-gray-500 border-t pt-3">
              <p>提示: 从首页连板股票列表点击"+"按钮可添加到自选池</p>
            </div>
          </div>
        )}

        {watchlist.length === 0 && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 mb-6 text-center">
            <svg className="w-16 h-16 mx-auto text-gray-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-2">自选池为空</h3>
            <p className="text-gray-600 mb-4">
              在首页连板股票列表中点击股票名称旁的"+"按钮，即可添加到自选池
            </p>
          </div>
        )}

        {/* 查询表单 */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">个股明日溢价概率评分</h2>
          <p className="text-gray-600 mb-4 text-sm">
            基于技术面、资金面、题材地位、位置风险、市场环境五维度综合评估
          </p>
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                股票代码
              </label>
              <input
                type="text"
                value={stockCode}
                onChange={(e) => setStockCode(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="输入6位股票代码，如 600519"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                maxLength={6}
              />
            </div>
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                交易日期（可选）
              </label>
              <input
                type="date"
                value={tradeDate}
                onChange={(e) => setTradeDate(e.target.value)}
                onKeyPress={handleKeyPress}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <button
              onClick={fetchPremiumScore}
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? '计算中...' : '查询评分'}
            </button>
          </div>
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* 评分结果 */}
        {scoreData && scoreData.data && (
          <div className="space-y-6">
            {/* 总分卡片 */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    {scoreData.data.stock_name} ({scoreData.data.stock_code})
                  </h2>
                  <p className="text-gray-600">{scoreData.data.trade_date}</p>
                </div>
                <div className={`px-6 py-3 rounded-lg ${getLevelColor(scoreData.data.premium_level)}`}>
                  <div className="text-center">
                    <div className="text-3xl font-bold">{scoreData.data.total_score.toFixed(2)}</div>
                    <div className="text-sm mt-1">{scoreData.data.premium_level}</div>
                  </div>
                </div>
              </div>

              {/* 总分进度条 */}
              <div className="mt-4">
                <div className="flex justify-between text-sm text-gray-600 mb-2">
                  <span>总分范围: -9 ~ +9</span>
                  <span>当前: {scoreData.data.total_score.toFixed(2)}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                  <div
                    className={`h-full transition-all ${
                      scoreData.data.total_score >= 0 ? 'bg-gradient-to-r from-green-400 to-red-500' : 'bg-gradient-to-r from-blue-500 to-gray-400'
                    }`}
                    style={{ width: `${((scoreData.data.total_score + 9) / 18) * 100}%` }}
                  />
                </div>
              </div>
            </div>

            {/* 各维度评分 */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* 技术面 */}
              <div className="bg-white rounded-lg shadow-sm p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">技术面</h3>
                  <span className={`text-2xl font-bold ${getScoreColor(scoreData.data.technical_score)}`}>
                    {scoreData.data.technical_score >= 0 ? '+' : ''}{scoreData.data.technical_score.toFixed(2)}
                  </span>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">首次封板</span>
                    <span className="font-medium">{scoreData.data.technical_detail.first_limit_time || '-'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">开板次数</span>
                    <span className="font-medium">{scoreData.data.technical_detail.opening_times}次</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">换手率</span>
                    <span className="font-medium">
                      {scoreData.data.technical_detail.turnover_rate?.toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">一字板</span>
                    <span className="font-medium">{scoreData.data.technical_detail.is_one_word ? '是' : '否'}</span>
                  </div>
                  <div className="pt-2 border-t border-gray-200">
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>时间得分: {scoreData.data.technical_detail.time_score.toFixed(1)}</span>
                      <span>换手得分: {scoreData.data.technical_detail.turnover_score.toFixed(1)}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* 资金面 */}
              <div className="bg-white rounded-lg shadow-sm p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">资金面</h3>
                  <span className={`text-2xl font-bold ${getScoreColor(scoreData.data.capital_score)}`}>
                    {scoreData.data.capital_score >= 0 ? '+' : ''}{scoreData.data.capital_score.toFixed(2)}
                  </span>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">封单金额</span>
                    <span className="font-medium">
                      {scoreData.data.capital_detail.sealed_amount
                        ? `${(scoreData.data.capital_detail.sealed_amount / 10000).toFixed(2)}亿`
                        : '-'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">成交额</span>
                    <span className="font-medium">
                      {scoreData.data.capital_detail.amount
                        ? `${(scoreData.data.capital_detail.amount / 10000).toFixed(2)}亿`
                        : '-'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">封单比</span>
                    <span className="font-medium">
                      {scoreData.data.capital_detail.sealed_ratio?.toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">主力净流入</span>
                    <span className={`font-medium ${
                      (scoreData.data.capital_detail.main_net_inflow || 0) > 0 ? 'text-red-600' : 'text-green-600'
                    }`}>
                      {scoreData.data.capital_detail.main_net_inflow
                        ? `${(scoreData.data.capital_detail.main_net_inflow / 10000).toFixed(2)}亿`
                        : '-'}
                    </span>
                  </div>
                  <div className="pt-2 border-t border-gray-200">
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>封单得分: {scoreData.data.capital_detail.sealed_score.toFixed(1)}</span>
                      <span>流入得分: {scoreData.data.capital_detail.inflow_score.toFixed(1)}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* 题材地位 */}
              <div className="bg-white rounded-lg shadow-sm p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">题材地位</h3>
                  <span className={`text-2xl font-bold ${getScoreColor(scoreData.data.theme_score)}`}>
                    {scoreData.data.theme_score >= 0 ? '+' : ''}{scoreData.data.theme_score.toFixed(2)}
                  </span>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">主概念</span>
                    <span className="font-medium">{scoreData.data.theme_detail.main_concept || '-'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">热门概念TOP10</span>
                    <span className="font-medium">{scoreData.data.theme_detail.is_in_top10 ? '是' : '否'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">主线板块</span>
                    <span className="font-medium">{scoreData.data.theme_detail.is_main_line ? '是' : '否'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">梯队状态</span>
                    <span className="font-medium">
                      {scoreData.data.theme_detail.ladder_status === 'complete' ? '完整' :
                       scoreData.data.theme_detail.ladder_status === 'normal' ? '一般' : '独苗'}
                    </span>
                  </div>
                  <div className="pt-2 border-t border-gray-200">
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>热度得分: {scoreData.data.theme_detail.theme_hot_score.toFixed(1)}</span>
                      <span>梯队得分: {scoreData.data.theme_detail.ladder_score.toFixed(1)}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* 位置风险 */}
              <div className="bg-white rounded-lg shadow-sm p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">位置风险</h3>
                  <span className={`text-2xl font-bold ${getScoreColor(scoreData.data.position_score)}`}>
                    {scoreData.data.position_score >= 0 ? '+' : ''}{scoreData.data.position_score.toFixed(2)}
                  </span>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">连板天数</span>
                    <span className="font-medium text-lg">{scoreData.data.position_detail.continuous_days}板</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">风险等级</span>
                    <span className="font-medium">{scoreData.data.position_detail.position_risk_level}</span>
                  </div>
                </div>
              </div>

              {/* 市场环境 */}
              <div className="bg-white rounded-lg shadow-sm p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">市场环境</h3>
                  <span className={`text-2xl font-bold ${getScoreColor(scoreData.data.market_score)}`}>
                    {scoreData.data.market_score >= 0 ? '+' : ''}{scoreData.data.market_score.toFixed(2)}
                  </span>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">情绪阶段</span>
                    <span className="font-medium text-lg">{scoreData.data.market_detail.emotion_stage}</span>
                  </div>
                  <div className="text-xs text-gray-500 mt-2">
                    * 市场环境得分 = 阶段得分 × 0.5
                  </div>
                </div>
              </div>
            </div>

            {/* 免责声明 */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <p className="text-sm text-yellow-800">
                <strong>⚠️ 风险提示：</strong>
                本评分仅基于历史数据和当日盘面特征的统计性评估，不构成对任何个股的投资建议或收益承诺。
                股市有风险，投资需谨慎。
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
