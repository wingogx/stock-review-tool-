'use client';

/**
 * 个股分析页面
 */

import { Card } from '@/components/ui/card';

export default function StockPage() {
  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">个股分析</h1>
          <p className="text-gray-500 mt-1">自选股监控与个股深度分析</p>
        </div>

        <Card title="功能开发中">
          <div className="text-center py-16">
            <svg className="mx-auto h-16 w-16 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900">个股分析模块</h3>
            <p className="mt-2 text-gray-500">
              即将推出：自选股管理、个股K线分析、龙虎榜追踪
            </p>
          </div>
        </Card>
      </div>
    </main>
  );
}
