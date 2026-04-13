'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { NewsItem, formatTimeAgo } from '@/lib/mock-data'
import { cn } from '@/lib/utils'

interface NewsListProps {
  news: NewsItem[]
  title: string
}

export function NewsList({ news, title }: NewsListProps) {
  const getImportanceBadge = (importance: string) => {
    const styles = {
      high: 'bg-red-500/20 text-red-400 border-red-500/30',
      medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
      low: 'bg-neutral-700/50 text-neutral-400 border-neutral-600/50',
    }
    const labels = {
      high: '重要',
      medium: '普通',
      low: '低',
    }
    return { style: styles[importance as keyof typeof styles], label: labels[importance as keyof typeof labels] }
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-0">
        <div className="max-h-96 overflow-y-auto space-y-2">
          {news.map((item) => {
            const importance = getImportanceBadge(item.importance)
            return (
              <div
                key={item.id}
                className="flex gap-3 p-3 bg-white/[0.02] hover:bg-white/[0.06] rounded transition-colors cursor-pointer group"
              >
                <Badge
                  variant="outline"
                  className={cn('text-xs px-1.5 py-0 shrink-0 mt-0.5', importance.style)}
                >
                  {importance.label}
                </Badge>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white group-hover:text-orange-400 transition-colors line-clamp-2">
                    {item.title}
                  </p>
                  <div className="flex items-center gap-2 mt-1 text-xs text-neutral-400">
                    <span>{item.source}</span>
                    <span>•</span>
                    <span>{formatTimeAgo(item.publishTime)}</span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
