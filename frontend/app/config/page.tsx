'use client'

import { useState, useEffect } from 'react'
import { PremiumScoreResponse, BacktestRecord, BacktestResultsResponse, BacktestStatistics, BacktestStatisticsResponse } from '@/types/api'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// 配置模块选项卡
const configTabs = [
  { id: 'premium-score', name: '个股溢价评分', icon: '📊' },
  { id: 'backtest-results', name: '股票评测结果', icon: '📈' },
  { id: 'backtest-params', name: '回测参数', icon: '⚙️', disabled: true },
  { id: 'alert-rules', name: '提醒规则', icon: '🔔', disabled: true },
]

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

export default function ConfigPage() {
  const [activeTab, setActiveTab] = useState('premium-score')
  const [stockCode, setStockCode] = useState('')
  const [tradeDate, setTradeDate] = useState('')
  const [loading, setLoading] = useState(false)
  const [scoreData, setScoreData] = useState<PremiumScoreResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  // 回测结果相关状态
  const [backtestRecords, setBacktestRecords] = useState<BacktestRecord[]>([])
  const [backtestStats, setBacktestStats] = useState<BacktestStatistics | null>(null)
  const [backtestLoading, setBacktestLoading] = useState(false)
  const [backtestStartDate, setBacktestStartDate] = useState('')
  const [backtestEndDate, setBacktestEndDate] = useState('')

  // 分页状态
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize] = useState(20)
  const [totalRecords, setTotalRecords] = useState(0)
  const [totalPages, setTotalPages] = useState(0)

  // 复选框状态
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [isDeleting, setIsDeleting] = useState(false)

  // 股票详情弹窗状态
  const [showStockDetail, setShowStockDetail] = useState(false)
  const [stockDetailData, setStockDetailData] = useState<any>(null)
  const [stockDetailLoading, setStockDetailLoading] = useState(false)

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

  // 获取回测结果列表
  const fetchBacktestResults = async (page: number = 1) => {
    setBacktestLoading(true)

    try {
      // 构建查询参数
      const params = new URLSearchParams()
      if (backtestStartDate) params.append('start_date', backtestStartDate)
      if (backtestEndDate) params.append('end_date', backtestEndDate)
      params.append('page', page.toString())
      params.append('page_size', pageSize.toString())

      const response = await fetch(`${API_BASE_URL}/api/backtest/results?${params}`)
      if (!response.ok) throw new Error('获取回测数据失败')

      const data: BacktestResultsResponse = await response.json()
      setBacktestRecords(data.data || [])
      setTotalRecords(data.total || 0)
      setTotalPages(data.total_pages || 0)
      setCurrentPage(page)

      // 同时获取统计数据
      const statsResponse = await fetch(`${API_BASE_URL}/api/backtest/statistics`)
      if (statsResponse.ok) {
        const statsData: BacktestStatisticsResponse = await statsResponse.json()
        setBacktestStats(statsData.data)
      }
    } catch (err: any) {
      console.error('获取回测数据失败:', err)
    } finally {
      setBacktestLoading(false)
    }
  }

  // 翻页处理
  const handlePageChange = (page: number) => {
    setSelectedIds([]) // 切换页面时清空选择
    fetchBacktestResults(page)
  }

  // 全选/取消全选
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      const allIds = backtestRecords.map(r => r.id)
      setSelectedIds(allIds)
    } else {
      setSelectedIds([])
    }
  }

  // 单个选择
  const handleSelectOne = (id: number, checked: boolean) => {
    if (checked) {
      setSelectedIds([...selectedIds, id])
    } else {
      setSelectedIds(selectedIds.filter(i => i !== id))
    }
  }

  // 删除选中的记录
  const handleDeleteSelected = async () => {
    if (selectedIds.length === 0) {
      alert('请先选择要删除的记录')
      return
    }

    if (!confirm(`确定要删除选中的 ${selectedIds.length} 条记录吗？删除后无法恢复。`)) {
      return
    }

    setIsDeleting(true)

    try {
      const params = new URLSearchParams()
      selectedIds.forEach(id => params.append('record_ids', id.toString()))

      const response = await fetch(`${API_BASE_URL}/api/backtest/records?${params}`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        throw new Error('删除失败')
      }

      const data = await response.json()

      // 删除成功，刷新列表
      alert(data.message || `成功删除 ${data.deleted_count} 条记录`)
      setSelectedIds([])
      fetchBacktestResults(currentPage)

    } catch (err: any) {
      alert('删除失败: ' + err.message)
    } finally {
      setIsDeleting(false)
    }
  }

  // 获取股票涨停时的详细数据
  const fetchStockDetail = async (stockCode: string, tradeDate: string) => {
    setStockDetailLoading(true)
    setShowStockDetail(true)
    setStockDetailData(null)

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/backtest/stock-detail/${stockCode}?trade_date=${tradeDate}`
      )

      if (!response.ok) {
        throw new Error('获取股票详情失败')
      }

      const data = await response.json()
      setStockDetailData(data.data)

    } catch (err: any) {
      alert('获取股票详情失败: ' + err.message)
      setShowStockDetail(false)
    } finally {
      setStockDetailLoading(false)
    }
  }

  // 当切换到回测页签时自动加载数据
  useEffect(() => {
    if (activeTab === 'backtest-results') {
      fetchBacktestResults()
    }
  }, [activeTab])

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* 页面标题 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">配置中心</h1>
          <p className="text-gray-600">
            个股分析配置、回测参数设置、提醒规则管理
          </p>
        </div>

        {/* 选项卡导航 */}
        <div className="bg-white rounded-lg shadow-sm mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6" aria-label="Tabs">
              {configTabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => !tab.disabled && setActiveTab(tab.id)}
                  disabled={tab.disabled}
                  className={`
                    py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap
                    ${activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : tab.disabled
                      ? 'border-transparent text-gray-400 cursor-not-allowed'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  <span className="mr-2">{tab.icon}</span>
                  {tab.name}
                  {tab.disabled && <span className="ml-2 text-xs">(即将上线)</span>}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* 个股溢价评分模块 */}
        {activeTab === 'premium-score' && (
          <div className="space-y-6">
            {/* 模块说明 */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-blue-900 mb-2">💡 功能说明</h3>
              <p className="text-sm text-blue-800">
                个股明日溢价概率评分基于技术面、资金面、题材地位、位置风险、市场环境五维度综合评估，
                总分范围 -9 ~ +9，等级分为：极高、高、偏高、中性、偏低、低
              </p>
            </div>

            {/* 评分因子配置 */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">📋 评分因子配置 (v2.0)</h3>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* 技术面阈值 */}
                <div className="border border-gray-200 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-900 mb-3">🎯 技术面阈值</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">一字板封板时间</span>
                      <span className="font-mono">≤ 0分钟</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">早盘封板 (10:00前)</span>
                      <span className="font-mono">≤ 30分钟</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">午盘封板 (13:00前)</span>
                      <span className="font-mono">≤ 210分钟</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">尾盘封板 (14:00前)</span>
                      <span className="font-mono">≤ 270分钟</span>
                    </div>
                    <div className="border-t border-gray-200 pt-2 mt-2">
                      <div className="flex justify-between">
                        <span className="text-gray-600">低换手率</span>
                        <span className="font-mono">≤ 5%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">中低换手率</span>
                        <span className="font-mono">5% - 10%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">中高换手率</span>
                        <span className="font-mono">10% - 15%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">高换手率</span>
                        <span className="font-mono">15% - 20%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">极高换手率</span>
                        <span className="font-mono">&gt; 25%</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 资金面阈值 */}
                <div className="border border-gray-200 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-900 mb-3">💰 资金面阈值</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">强封单比</span>
                      <span className="font-mono">&gt; 10%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">中等封单比</span>
                      <span className="font-mono">3% - 10%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">弱封单比</span>
                      <span className="font-mono">0.5% - 3%</span>
                    </div>
                    <div className="border-t border-gray-200 pt-2 mt-2">
                      <div className="flex justify-between">
                        <span className="text-gray-600">明显砸盘 (净流出)</span>
                        <span className="font-mono">&lt; -10%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">轻微流出</span>
                        <span className="font-mono">-10% ~ 0%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">小幅流入</span>
                        <span className="font-mono">0% - 5%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">中等流入</span>
                        <span className="font-mono">5% - 10%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">大幅流入</span>
                        <span className="font-mono">&gt; 10%</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 题材地位判断 */}
                <div className="border border-gray-200 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-900 mb-3">🔥 题材地位判断</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">热门概念TOP10</span>
                      <span className="text-blue-600">从hot_concepts表查询</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">主线板块判断</span>
                      <span className="text-blue-600">涨停数 ≥ 8</span>
                    </div>
                    <div className="border-t border-gray-200 pt-2 mt-2">
                      <div className="space-y-1">
                        <div className="flex justify-between">
                          <span className="text-gray-600">完整梯队</span>
                          <span className="font-mono">≥3只 + 多层级</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">一般梯队</span>
                          <span className="font-mono">1-2只</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">独苗</span>
                          <span className="font-mono">仅1只</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 位置风险阈值 */}
                <div className="border border-gray-200 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-900 mb-3">📍 位置风险阈值</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">极高位风险</span>
                      <span className="font-mono">≥ 7板</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">高位风险</span>
                      <span className="font-mono">5-6板</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">中位</span>
                      <span className="font-mono">3-4板</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">低位</span>
                      <span className="font-mono">2板</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">首板</span>
                      <span className="font-mono">1板</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* 市场环境映射 */}
              <div className="border border-gray-200 rounded-lg p-4 mt-6">
                <h4 className="font-semibold text-gray-900 mb-3">🌡️ 市场环境评分映射</h4>
                <div className="grid grid-cols-5 gap-4 text-sm">
                  <div className="text-center">
                    <div className="text-blue-600 font-semibold mb-1">冰点期</div>
                    <div className="font-mono text-lg">-2</div>
                  </div>
                  <div className="text-center">
                    <div className="text-yellow-600 font-semibold mb-1">回暖期</div>
                    <div className="font-mono text-lg">-1</div>
                  </div>
                  <div className="text-center">
                    <div className="text-green-600 font-semibold mb-1">退潮期</div>
                    <div className="font-mono text-lg">-2</div>
                  </div>
                  <div className="text-center">
                    <div className="text-orange-600 font-semibold mb-1">加速期</div>
                    <div className="font-mono text-lg">+1</div>
                  </div>
                  <div className="text-center">
                    <div className="text-red-600 font-semibold mb-1">高潮期</div>
                    <div className="font-mono text-lg">+2</div>
                  </div>
                </div>
                <div className="mt-3 text-xs text-gray-500 text-center">
                  * 市场环境得分 = 阶段得分 × 0.5，最终计入总分
                </div>
              </div>

              {/* 总分计算说明 */}
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mt-6">
                <h4 className="font-semibold text-gray-900 mb-2">📐 总分计算公式</h4>
                <div className="text-sm text-gray-700 space-y-1">
                  <div className="font-mono">总分 = 技术面得分 + 资金面得分 + 题材地位得分 + 位置风险得分 + (市场环境得分 × 0.5)</div>
                  <div className="text-xs text-gray-500">
                    • 各维度得分范围: -2 ~ +2 (市场环境原始得分同样，但乘以0.5后为 -1 ~ +1)<br/>
                    • 总分理论范围: -9 ~ +9<br/>
                    • 溢价等级: ≥6极高, 4~6高, 2~4偏高, 0~2中性, -2~0偏低, &lt;-2低
                  </div>
                </div>
              </div>
            </div>

            {/* 查询表单 */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">查询个股评分</h3>
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
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
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
        )}

        {/* 股票评测结果模块 */}
        {activeTab === 'backtest-results' && (
          <div className="space-y-6">
            {/* 模块说明 */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-blue-900 mb-2">💡 功能说明</h3>
              <p className="text-sm text-blue-800">
                展示历史评测记录，对比预测评分与次日实际表现，验证评分模型的准确性
              </p>
            </div>

            {/* 查询条件 */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">查询条件</h3>
              <div className="flex gap-4 items-end">
                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    开始日期
                  </label>
                  <input
                    type="date"
                    value={backtestStartDate}
                    onChange={(e) => setBacktestStartDate(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    结束日期
                  </label>
                  <input
                    type="date"
                    value={backtestEndDate}
                    onChange={(e) => setBacktestEndDate(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <button
                  onClick={fetchBacktestResults}
                  disabled={backtestLoading}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  {backtestLoading ? '查询中...' : '查询'}
                </button>
              </div>
            </div>

            {/* 统计概览 */}
            {backtestStats && backtestStats.total > 0 && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">统计概览</h3>

                {/* 整体统计 */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <div className="bg-gray-50 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-gray-900">{backtestStats.total}</div>
                    <div className="text-sm text-gray-600 mt-1">总记录数</div>
                  </div>
                  <div className="bg-green-50 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {backtestStats.overall?.avg_next_day_pct?.toFixed(2) || '0.00'}%
                    </div>
                    <div className="text-sm text-gray-600 mt-1">平均次日涨幅</div>
                  </div>
                  <div className="bg-blue-50 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {backtestStats.overall?.profitable_rate?.toFixed(1) || '0.0'}%
                    </div>
                    <div className="text-sm text-gray-600 mt-1">盈利率</div>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {backtestStats.overall?.prediction_accuracy?.toFixed(1) || '0.0'}%
                    </div>
                    <div className="text-sm text-gray-600 mt-1">预测准确率</div>
                  </div>
                </div>

                {/* 按等级统计 */}
                {backtestStats.by_level && Object.keys(backtestStats.by_level).length > 0 && (
                  <div className="mt-6">
                    <h4 className="text-md font-semibold text-gray-900 mb-3">各等级表现</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {Object.entries(backtestStats.by_level)
                        .sort(([a], [b]) => {
                          const order = ['极高', '高', '偏高', '中性', '偏低', '低']
                          return order.indexOf(a) - order.indexOf(b)
                        })
                        .map(([level, stats]) => (
                          <div key={level} className={`border rounded-lg p-4 ${getLevelColor(level)} bg-opacity-10`}>
                            <div className="flex items-center justify-between mb-2">
                              <span className={`px-3 py-1 rounded text-sm font-semibold ${getLevelColor(level)}`}>
                                {level}
                              </span>
                              <span className="text-sm text-gray-600">{stats.count}只</span>
                            </div>
                            <div className="space-y-1 text-sm">
                              <div className="flex justify-between">
                                <span className="text-gray-600">平均涨幅</span>
                                <span className={`font-semibold ${stats.avg_next_day_pct >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                                  {stats.avg_next_day_pct >= 0 ? '+' : ''}{stats.avg_next_day_pct.toFixed(2)}%
                                </span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-600">盈利率</span>
                                <span className="font-semibold">{stats.profitable_rate.toFixed(1)}%</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-600">准确率</span>
                                <span className="font-semibold">{stats.prediction_accuracy.toFixed(1)}%</span>
                              </div>
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* 回测记录列表 */}
            {backtestRecords.length > 0 ? (
              <div className="bg-white rounded-lg shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">
                    回测记录 (共 {totalRecords} 条，第 {currentPage}/{totalPages} 页)
                  </h3>
                  {selectedIds.length > 0 && (
                    <button
                      onClick={handleDeleteSelected}
                      disabled={isDeleting}
                      className="px-4 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                    >
                      {isDeleting ? (
                        <>
                          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                          </svg>
                          删除中...
                        </>
                      ) : (
                        <>
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                          删除选中 ({selectedIds.length})
                        </>
                      )}
                    </button>
                  )}
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase w-12">
                          <input
                            type="checkbox"
                            checked={selectedIds.length === backtestRecords.length && backtestRecords.length > 0}
                            onChange={(e) => handleSelectAll(e.target.checked)}
                            className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                          />
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">日期</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">股票</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">连板</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">评分</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">等级</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">次日涨跌</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">预测结果</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {backtestRecords.map((record) => (
                        <tr key={record.id} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-center">
                            <input
                              type="checkbox"
                              checked={selectedIds.includes(record.id)}
                              onChange={(e) => handleSelectOne(record.id, e.target.checked)}
                              className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                            />
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-900">{record.trade_date}</td>
                          <td className="px-4 py-3 text-sm">
                            <button
                              onClick={() => fetchStockDetail(record.stock_code, record.trade_date)}
                              className="text-left hover:bg-blue-50 rounded px-2 py-1 -mx-2 -my-1 transition-colors group"
                            >
                              <div className="font-medium text-blue-600 group-hover:text-blue-700 group-hover:underline">
                                {record.stock_name}
                              </div>
                              <div className="text-gray-500 text-xs">{record.stock_code}</div>
                            </button>
                          </td>
                          <td className="px-4 py-3 text-sm text-center text-gray-900">
                            {record.continuous_days}板
                          </td>
                          <td className="px-4 py-3 text-sm text-center">
                            <span className={`font-bold ${
                              record.total_score >= 8 ? 'text-red-600' :
                              record.total_score >= 7 ? 'text-orange-500' :
                              record.total_score >= 6 ? 'text-yellow-600' :
                              record.total_score >= 5 ? 'text-gray-600' :
                              record.total_score >= 4 ? 'text-blue-500' :
                              'text-green-600'
                            }`}>
                              {record.total_score.toFixed(1)}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm text-center">
                            <span className={`px-2 py-1 text-xs rounded font-medium ${getLevelColor(record.premium_level)}`}>
                              {record.premium_level}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm text-center">
                            {record.next_day_change_pct !== null && record.next_day_change_pct !== undefined ? (
                              <div>
                                <span className={`font-bold ${
                                  record.next_day_change_pct >= 0 ? 'text-red-600' : 'text-green-600'
                                }`}>
                                  {record.next_day_change_pct >= 0 ? '+' : ''}{record.next_day_change_pct.toFixed(2)}%
                                </span>
                                {record.is_next_day_limit_up && (
                                  <span className="ml-1 text-xs text-red-600">涨停</span>
                                )}
                                {record.is_next_day_limit_down && (
                                  <span className="ml-1 text-xs text-green-600">跌停</span>
                                )}
                              </div>
                            ) : (
                              <span className="text-gray-400">-</span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-sm text-center">
                            {record.prediction_result === 'correct' && (
                              <span className="px-2 py-1 text-xs rounded bg-green-100 text-green-800">✓ 正确</span>
                            )}
                            {record.prediction_result === 'wrong' && (
                              <span className="px-2 py-1 text-xs rounded bg-red-100 text-red-800">✗ 错误</span>
                            )}
                            {record.prediction_result === 'neutral' && (
                              <span className="px-2 py-1 text-xs rounded bg-gray-100 text-gray-600">— 中性</span>
                            )}
                            {!record.prediction_result && (
                              <span className="text-gray-400">-</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* 分页器 */}
                {totalPages > 1 && (
                  <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
                    <div className="text-sm text-gray-700">
                      显示第 {(currentPage - 1) * pageSize + 1} 到 {Math.min(currentPage * pageSize, totalRecords)} 条，共 {totalRecords} 条记录
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handlePageChange(1)}
                        disabled={currentPage === 1}
                        className="px-3 py-1 text-sm border border-gray-300 bg-white rounded hover:bg-blue-50 hover:border-blue-400 hover:text-blue-600 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white disabled:hover:border-gray-300 disabled:hover:text-gray-700 transition-colors"
                      >
                        首页
                      </button>
                      <button
                        onClick={() => handlePageChange(currentPage - 1)}
                        disabled={currentPage === 1}
                        className="px-3 py-1 text-sm border border-gray-300 bg-white rounded hover:bg-blue-50 hover:border-blue-400 hover:text-blue-600 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white disabled:hover:border-gray-300 disabled:hover:text-gray-700 transition-colors"
                      >
                        上一页
                      </button>

                      {/* 页码按钮 */}
                      <div className="flex items-center gap-1">
                        {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                          let pageNum: number
                          if (totalPages <= 5) {
                            pageNum = i + 1
                          } else if (currentPage <= 3) {
                            pageNum = i + 1
                          } else if (currentPage >= totalPages - 2) {
                            pageNum = totalPages - 4 + i
                          } else {
                            pageNum = currentPage - 2 + i
                          }

                          return (
                            <button
                              key={pageNum}
                              onClick={() => handlePageChange(pageNum)}
                              className={`px-3 py-1 text-sm border rounded transition-colors font-medium ${
                                currentPage === pageNum
                                  ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                                  : 'bg-white border-gray-300 text-gray-700 hover:bg-blue-50 hover:border-blue-400 hover:text-blue-600'
                              }`}
                            >
                              {pageNum}
                            </button>
                          )
                        })}
                      </div>

                      <button
                        onClick={() => handlePageChange(currentPage + 1)}
                        disabled={currentPage === totalPages}
                        className="px-3 py-1 text-sm border border-gray-300 bg-white rounded hover:bg-blue-50 hover:border-blue-400 hover:text-blue-600 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white disabled:hover:border-gray-300 disabled:hover:text-gray-700 transition-colors"
                      >
                        下一页
                      </button>
                      <button
                        onClick={() => handlePageChange(totalPages)}
                        disabled={currentPage === totalPages}
                        className="px-3 py-1 text-sm border border-gray-300 bg-white rounded hover:bg-blue-50 hover:border-blue-400 hover:text-blue-600 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white disabled:hover:border-gray-300 disabled:hover:text-gray-700 transition-colors"
                      >
                        末页
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : backtestLoading ? (
              <div className="bg-white rounded-lg shadow-sm p-12 text-center">
                <div className="text-gray-500">加载中...</div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm p-12 text-center">
                <div className="text-gray-400 mb-2">暂无数据</div>
                <p className="text-sm text-gray-500">请设置查询条件后点击"查询"按钮</p>
              </div>
            )}
          </div>
        )}

        {/* 其他模块占位 */}
        {activeTab === 'backtest-params' && (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <div className="text-gray-400 mb-4">
              <svg className="mx-auto h-16 w-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">回测参数配置</h3>
            <p className="text-gray-500">该功能正在开发中，敬请期待</p>
          </div>
        )}

        {activeTab === 'alert-rules' && (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <div className="text-gray-400 mb-4">
              <svg className="mx-auto h-16 w-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">提醒规则管理</h3>
            <p className="text-gray-500">该功能正在开发中，敬请期待</p>
          </div>
        )}
      </div>

      {/* 股票详情弹窗 */}
      {showStockDetail && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            {/* 弹窗标题 */}
            <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">
                涨停详情 {stockDetailData && `- ${stockDetailData.stock_name} (${stockDetailData.stock_code})`}
              </h3>
              <button
                onClick={() => setShowStockDetail(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* 弹窗内容 */}
            <div className="p-6">
              {stockDetailLoading ? (
                <div className="text-center py-12">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                  <p className="mt-2 text-gray-500">加载中...</p>
                </div>
              ) : stockDetailData ? (
                <div className="space-y-6">
                  {/* 基本信息 */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="text-sm text-gray-600 mb-1">交易日期</div>
                      <div className="text-lg font-semibold text-gray-900">{stockDetailData.trade_date}</div>
                    </div>
                    <div className="bg-red-50 rounded-lg p-4">
                      <div className="text-sm text-gray-600 mb-1">涨跌幅</div>
                      <div className="text-lg font-semibold text-red-600">
                        +{stockDetailData.change_pct?.toFixed(2)}%
                      </div>
                    </div>
                    <div className="bg-blue-50 rounded-lg p-4">
                      <div className="text-sm text-gray-600 mb-1">最新价</div>
                      <div className="text-lg font-semibold text-gray-900">
                        {stockDetailData.close_price?.toFixed(2)}
                      </div>
                    </div>
                    <div className="bg-purple-50 rounded-lg p-4">
                      <div className="text-sm text-gray-600 mb-1">连板数</div>
                      <div className="text-lg font-semibold text-purple-600">
                        {stockDetailData.continuous_days}板
                      </div>
                    </div>
                  </div>

                  {/* 详细数据表格 */}
                  <div className="border rounded-lg overflow-hidden">
                    <table className="min-w-full divide-y divide-gray-200">
                      <tbody className="bg-white divide-y divide-gray-200">
                        <tr>
                          <td className="px-4 py-3 text-sm font-medium text-gray-700 bg-gray-50 w-1/3">流通市值</td>
                          <td className="px-4 py-3 text-sm text-gray-900">
                            {stockDetailData.circulation_market_cap
                              ? `${(stockDetailData.circulation_market_cap / 100000000).toFixed(1)}亿`
                              : '-'}
                          </td>
                        </tr>
                        <tr>
                          <td className="px-4 py-3 text-sm font-medium text-gray-700 bg-gray-50">换手率</td>
                          <td className="px-4 py-3 text-sm text-gray-900">
                            {stockDetailData.turnover_rate?.toFixed(2)}%
                          </td>
                        </tr>
                        <tr>
                          <td className="px-4 py-3 text-sm font-medium text-gray-700 bg-gray-50">封板资金</td>
                          <td className="px-4 py-3 text-sm text-gray-900">
                            {stockDetailData.sealed_amount
                              ? `${(stockDetailData.sealed_amount / 100000000).toFixed(2)}亿`
                              : '-'}
                          </td>
                        </tr>
                        <tr>
                          <td className="px-4 py-3 text-sm font-medium text-gray-700 bg-gray-50">主力净流入</td>
                          <td className="px-4 py-3 text-sm">
                            {stockDetailData.main_net_inflow !== undefined && stockDetailData.main_net_inflow !== null ? (
                              <span className={stockDetailData.main_net_inflow >= 0 ? 'text-red-600 font-medium' : 'text-green-600 font-medium'}>
                                {stockDetailData.main_net_inflow >= 0 ? '+' : ''}
                                {(stockDetailData.main_net_inflow / 100000000).toFixed(2)}亿
                              </span>
                            ) : '-'}
                          </td>
                        </tr>
                        <tr>
                          <td className="px-4 py-3 text-sm font-medium text-gray-700 bg-gray-50">首次封板时间</td>
                          <td className="px-4 py-3 text-sm text-gray-900">
                            {stockDetailData.first_limit_time || '-'}
                          </td>
                        </tr>
                        <tr>
                          <td className="px-4 py-3 text-sm font-medium text-gray-700 bg-gray-50">炸板次数</td>
                          <td className="px-4 py-3 text-sm">
                            {stockDetailData.opening_times !== undefined && stockDetailData.opening_times !== null ? (
                              <span className={stockDetailData.opening_times > 0 ? 'text-orange-600 font-medium' : 'text-gray-900'}>
                                {stockDetailData.opening_times}次
                              </span>
                            ) : '-'}
                          </td>
                        </tr>
                        <tr>
                          <td className="px-4 py-3 text-sm font-medium text-gray-700 bg-gray-50">涨停统计</td>
                          <td className="px-4 py-3 text-sm text-gray-900">
                            {stockDetailData.limit_stats || '-'}
                          </td>
                        </tr>
                        <tr>
                          <td className="px-4 py-3 text-sm font-medium text-gray-700 bg-gray-50">封板类型</td>
                          <td className="px-4 py-3 text-sm">
                            {stockDetailData.is_strong_limit ? (
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
                        {stockDetailData.concepts && stockDetailData.concepts.length > 0 && (
                          <tr>
                            <td className="px-4 py-3 text-sm font-medium text-gray-700 bg-gray-50">所属概念</td>
                            <td className="px-4 py-3 text-sm text-gray-900">
                              <div className="flex flex-wrap gap-1">
                                {stockDetailData.concepts.map((concept: string, index: number) => (
                                  <span
                                    key={index}
                                    className="px-2 py-0.5 text-xs bg-blue-50 text-blue-700 rounded"
                                  >
                                    {concept}
                                  </span>
                                ))}
                              </div>
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>

                  {/* 说明文字 */}
                  <div className="text-sm text-gray-500 bg-gray-50 rounded-lg p-4">
                    <p className="mb-2">💡 <strong>数据说明：</strong></p>
                    <ul className="list-disc list-inside space-y-1 ml-2">
                      <li>以上数据为该股票在涨停当日的实际情况</li>
                      <li>可对比预测评分与次日实际表现，分析评分模型的准确性</li>
                      <li>一字板：当日未开板，首次封板时间≤09:30</li>
                      <li>换手板：当日有开板或首次封板时间&gt;09:30</li>
                    </ul>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  暂无数据
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
