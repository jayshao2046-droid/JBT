'use client'

import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import { KPIData } from '@/lib/mock-data'

interface KPICardProps {
  data: KPIData
}

export function KPICard({ data }: KPICardProps) {
  const Icon = data.icon
  
  const getChangeColor = (type?: string) => {
    switch (type) {
      case 'positive':
        return 'text-red-400'
      case 'negative':
        return 'text-green-400'
      default:
        return 'text-muted-foreground'
    }
  }

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'success':
        return { bg: 'bg-green-500/20', text: 'text-green-400', border: 'border-green-500/30' }
      case 'warning':
        return { bg: 'bg-yellow-500/20', text: 'text-yellow-400', border: 'border-yellow-500/30' }
      case 'danger':
        return { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/30' }
      default:
        return { bg: 'bg-orange-500/20', text: 'text-orange-400', border: 'border-orange-500/30' }
    }
  }

  const statusStyle = getStatusColor(data.status)

  return (
    <Card className={cn(
      'transition-all duration-300 overflow-hidden',
      statusStyle.border
    )}>
      <CardContent className="p-4 relative">
        <div className="space-y-3">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <p className="text-xs text-muted-foreground mb-1 text-float">{data.title}</p>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-foreground kpi-value">
                  {typeof data.value === 'number' 
                    ? data.value.toLocaleString(undefined, { 
                        maximumFractionDigits: data.value > 100 ? 0 : 2 
                      })
                    : data.value}
                </span>
                {data.change && (
                  <span className={cn('text-xs font-medium text-float', getChangeColor(data.changeType))}>
                    {data.change}
                  </span>
                )}
              </div>
            </div>
            <div className={cn(
              'p-2 rounded-lg backdrop-blur-sm',
              statusStyle.bg,
              'shadow-lg'
            )}>
              <Icon className={cn('w-5 h-5 drop-shadow-lg', statusStyle.text)} />
            </div>
          </div>

          {data.progress !== undefined && (
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground text-float">{data.description}</span>
                <span className="text-foreground font-mono text-float">{data.progress}%</span>
              </div>
              <Progress value={data.progress} className="h-1" />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
