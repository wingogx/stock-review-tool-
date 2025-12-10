'use client';

/**
 * 情绪分析页面
 */

import { Card } from '@/components/ui/card';

export default function SentimentPage() {
  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">情绪分析</h1>
          <p className="text-gray-500 mt-1">市场情绪指标与资金流向分析</p>
        </div>

        <Card title="功能开发中">
          <div className="text-center py-16">
            <svg className="mx-auto h-16 w-16 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900">情绪分析模块</h3>
            <p className="mt-2 text-gray-500">
              即将推出：市场情绪指数、恐慌贪婪指标、资金流向热力图
            </p>
          </div>
        </Card>
      </div>
    </main>
  );
}
