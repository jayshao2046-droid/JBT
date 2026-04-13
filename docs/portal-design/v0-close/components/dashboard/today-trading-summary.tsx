'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { BarChart3, ShoppingCart, TrendingUp, Percent } from 'lucide-react'
import { cn } from '@/lib/utils'

export function TodayTradingSummary() {
  const summaryData = [
    {
      label: '交易笔数',
      value: '28',
      subtext: '开仓18/平仓10',
      icon: BarChart3,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/20',
    },
    {
      label: '买入金额',
      value: '¥2.5M',
      subtext: '总成交',
      icon: TrendingUp,
      color: 'text-green-400',
      bgColor: 'bg-green-500/20',
    },
    {
      label: '卖出金额',
      value: '¥2.3M',
      subtext: '总成交',
      icon: ShoppingCart,
      color: 'text-red-400',
      bgColor: 'bg-red-500/20',
    },
    {
      label: '手续费',
      value: '¥8,500',
      subtext: '累计成本',
      icon: Percent,
      color: 'text-yellow-400',
      bgColor: 'bg-yellow-500/20',
    },
  ]

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">今日交易汇总</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-3">
          {summaryData.map((item, idx) => {
            const Icon = item.icon
            return (
              <div key={idx} className="bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.05] transition-colors rounded-lg p-3 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-neutral-400">{item.label}</span>
                  <div className={cn('p-1.5 rounded', item.bgColor)}>
                    <Icon className={cn('w-4 h-4', item.color)} />
                  </div>
                </div>
                <div>
                  <p className={cn('text-lg font-semibold', item.color)}>{item.value}</p>
                  <p className="text-xs text-neutral-500 mt-1">{item.subtext}</p>
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
