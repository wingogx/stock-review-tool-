'use client';

/**
 * 大盘分析页面
 */

import { Card } from '@/components/ui/card';

export default function MarketPage() {
  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">大盘分析</h1>
          <p className="text-gray-500 mt-1">大盘指数走势与技术分析</p>
        </div>

        <Card title="功能开发中">
          <div className="text-center py-16">
            <svg className="mx-auto h-16 w-16 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900">大盘分析模块</h3>
            <p className="mt-2 text-gray-500">
              即将推出：上证/深证/创业板K线图、技术指标分析、支撑压力位
            </p>
          </div>
        </Card>
      </div>
    </main>
  );
}
