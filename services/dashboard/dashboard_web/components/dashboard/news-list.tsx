"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { NewsItem } from "@/lib/api/types"

interface NewsListProps {
  news: NewsItem[]
  title?: string
}

function formatTimeAgo(timestamp: string): string {
  const now = new Date()
  const past = new Date(timestamp)
  const diffMs = now.getTime() - past.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return "刚刚"
  if (diffMins < 60) return `${diffMins}分钟前`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}小时前`
  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}天前`
}

export function NewsList({ news, title = "新闻资讯" }: NewsListProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-0">
        <div className="max-h-96 overflow-y-auto space-y-2">
          {news.map((item) => (
            <div
              key={item.id}
              className="flex gap-3 p-3 bg-white/[0.02] hover:bg-white/[0.06] rounded transition-colors cursor-pointer group"
            >
              <div className="flex-1 min-w-0">
                <p className="text-sm text-white group-hover:text-orange-400 transition-colors line-clamp-2">
                  {item.title}
                </p>
                <div className="flex items-center gap-2 mt-1 text-xs text-neutral-400">
                  <span>{item.source}</span>
                  <span>•</span>
                  <span>{formatTimeAgo(item.timestamp)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
