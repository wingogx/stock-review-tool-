'use client';

/**
 * 趋势分析页面
 */

import { Card } from '@/components/ui/card';

export default function TrendPage() {
  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">趋势分析</h1>
          <p className="text-gray-500 mt-1">板块轮动与热点追踪</p>
        </div>

        <Card title="功能开发中">
          <div className="text-center py-16">
            <svg className="mx-auto h-16 w-16 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900">趋势分析模块</h3>
            <p className="mt-2 text-gray-500">
              即将推出：概念板块趋势、行业轮动分析、热点持续性追踪
            </p>
          </div>
        </Card>
      </div>
    </main>
  );
}
