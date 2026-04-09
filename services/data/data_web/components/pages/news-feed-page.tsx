"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"
import { Progress } from "@/components/ui/progress"
import {
  Search,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Minus,
  Clock,
  Send,
  Filter,
  Star,
  ExternalLink,
  AlertCircle,
  Zap,
  BarChart3,
  MessageSquare,
  Activity,
} from "lucide-react"

type SentimentDirection = "positive" | "negative" | "neutral"

interface NewsItem {
  id: string
  title: string
  source: string
  publishTime: string
  summary: string
  keywords: string[]
  sentiment: SentimentDirection
  isImportant: boolean
  isPushed: boolean
  isNew?: boolean
}

interface HotKeyword {
  word: string
  count: number
}

interface PushRecord {
  title: string
  source: string
  time: string
}

interface SentimentBucket {
  sentiment: string
  count: number
}

interface ApiResponse {
  generated_at: string
  summary: { total_items: number; important_count: number; pushed_count: number; source_count: number }
  items: Array<{
    id: string
    title: string
    source: string
    publish_time: string
    summary: string
    keywords: string[]
    sentiment: SentimentDirection
    is_important: boolean
    is_pushed: boolean
    file: string
  }>
  hot_keywords: HotKeyword[]
  source_breakdown: Array<{ source: string; count: number }>
  push_records: PushRecord[]
  sentiment_distribution: SentimentBucket[]
}

export default function NewsFeedPage({ refreshNonce }: { refreshNonce?: number }) {
  const [selectedSource, setSelectedSource] = useState("全部")
  const [searchTerm, setSearchTerm] = useState("")
  const [showImportantOnly, setShowImportantOnly] = useState(false)
  const [autoScroll, setAutoScroll] = useState(true)
  const [isLoading, setIsLoading] = useState(true)
  const [timeRange, setTimeRange] = useState<"1h" | "24h">("1h")

  const [newsItems, setNewsItems] = useState<NewsItem[]>([])
  const [hotKeywords, setHotKeywords] = useState<HotKeyword[]>([])
  const [pushRecords, setPushRecords] = useState<PushRecord[]>([])
  const [sentimentDist, setSentimentDist] = useState<SentimentBucket[]>([])
  const [sources, setSources] = useState<string[]>(["全部"])
  const [fetchError, setFetchError] = useState(false)

  const fetchData = async () => {
    setIsLoading(true)
    setFetchError(false)
    try {
      const res = await fetch("/api/data/api/v1/dashboard/news")
      if (!res.ok) throw new Error("fetch failed")
      const data: ApiResponse = await res.json()

      setNewsItems(
        data.items.map((item) => ({
          id: item.id,
          title: item.title,
          source: item.source,
          publishTime: item.publish_time,
          summary: item.summary,
          keywords: item.keywords ?? [],
          sentiment: item.sentiment,
          isImportant: item.is_important,
          isPushed: item.is_pushed,
        }))
      )
      setHotKeywords(data.hot_keywords ?? [])
      setPushRecords(data.push_records ?? [])
      setSentimentDist(data.sentiment_distribution ?? [])
      setSources(["全部", ...(data.source_breakdown ?? []).map((s) => s.source)])
    } catch {
      setFetchError(true)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [refreshNonce])

  const filteredNews = newsItems.filter((news) => {
    const matchSource = selectedSource === "全部" || news.source === selectedSource
    const matchSearch =
      news.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      news.keywords.some((k) => k.toLowerCase().includes(searchTerm.toLowerCase()))
    const matchImportant = !showImportantOnly || news.isImportant
    return matchSource && matchSearch && matchImportant
  })

  const getSentimentIcon = (sentiment: SentimentDirection) => {
    switch (sentiment) {
      case "positive":
        return <TrendingUp className="w-4 h-4 text-green-500" />
      case "negative":
        return <TrendingDown className="w-4 h-4 text-red-500" />
      case "neutral":
        return <Minus className="w-4 h-4 text-neutral-500" />
    }
  }

  const getSentimentColor = (sentiment: SentimentDirection) => {
    switch (sentiment) {
      case "positive":
        return "border-green-500/30 bg-green-500/10"
      case "negative":
        return "border-red-500/30 bg-red-500/10"
      case "neutral":
        return "border-neutral-500/30 bg-neutral-500/10"
    }
  }

  const handleRefresh = () => {
    fetchData()
  }

  const sentimentTotal = sentimentDist.reduce((sum, b) => sum + b.count, 0)

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-12 w-64 bg-neutral-800" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-32 bg-neutral-800" />
            ))}
          </div>
          <Skeleton className="h-[600px] bg-neutral-800" />
        </div>
      </div>
    )
  }

  return (
    <div className="h-[calc(100vh-3.5rem)] flex flex-col">
      {/* 顶部筛选栏 */}
      <div className="p-4 border-b border-neutral-800 bg-neutral-900/50">
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-white">新闻资讯</h1>
            <p className="text-sm text-neutral-400 mt-1">实时财经资讯聚合与情绪观测</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm">
              <span className="text-neutral-400">仅看重大</span>
              <Switch
                checked={showImportantOnly}
                onCheckedChange={setShowImportantOnly}
                className="data-[state=checked]:bg-orange-500"
              />
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className="text-neutral-400">自动滚动</span>
              <Switch
                checked={autoScroll}
                onCheckedChange={setAutoScroll}
                className="data-[state=checked]:bg-orange-500"
              />
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              className="border-neutral-700 text-neutral-300"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              刷新
            </Button>
          </div>
        </div>

        {/* 来源筛选 */}
        <div className="flex items-center gap-2 mt-4 overflow-x-auto pb-2">
          {sources.map((source) => (
            <button
              key={source}
              onClick={() => setSelectedSource(source)}
              className={`px-3 py-1.5 text-sm rounded-lg whitespace-nowrap transition-colors ${
                selectedSource === source
                  ? "bg-orange-500 text-white"
                  : "bg-neutral-800 text-neutral-400 hover:text-white hover:bg-neutral-700"
              }`}
            >
              {source}
            </button>
          ))}
          <div className="ml-auto">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
              <Input
                placeholder="搜索关键词..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 w-64 h-9 bg-neutral-800 border-neutral-700 text-white placeholder:text-neutral-500"
              />
            </div>
          </div>
        </div>
      </div>

      {/* 主体内容区 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左侧新闻列表 */}
        <div className="flex-1 flex flex-col min-w-0">
          <ScrollArea className="flex-1 p-4">
            {fetchError ? (
              <div className="flex flex-col items-center justify-center py-20 text-neutral-500">
                <AlertCircle className="w-10 h-10 mb-3 text-red-500/60" />
                <p className="text-sm">数据加载失败，请稍后重试</p>
                <Button variant="outline" size="sm" onClick={handleRefresh} className="mt-4 border-neutral-700 text-neutral-400">
                  重新加载
                </Button>
              </div>
            ) : filteredNews.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 text-neutral-500">
                <MessageSquare className="w-10 h-10 mb-3 text-neutral-600" />
                <p className="text-sm">暂无新闻数据</p>
              </div>
            ) : (
              <div className="space-y-3">
                {filteredNews.map((news) => (
                  <Card
                    key={news.id}
                    className={`bg-neutral-900 border-neutral-800 hover:border-neutral-700 transition-all cursor-pointer ${
                      news.isNew ? "ring-1 ring-orange-500/50" : ""
                    }`}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        {/* 情绪指示器 */}
                        <div
                          className={`flex-shrink-0 p-2 rounded-lg border ${getSentimentColor(news.sentiment)}`}
                        >
                          {getSentimentIcon(news.sentiment)}
                        </div>

                        <div className="flex-1 min-w-0">
                          {/* 标题行 */}
                          <div className="flex items-start justify-between gap-2 mb-2">
                            <h3 className="text-sm font-medium text-white leading-tight">
                              {news.isNew && (
                                <Badge className="mr-2 bg-orange-500/20 text-orange-400 border-orange-500/30 text-xs">
                                  新
                                </Badge>
                              )}
                              {news.title}
                            </h3>
                            {news.isImportant && (
                              <Star className="w-4 h-4 text-yellow-500 flex-shrink-0" />
                            )}
                          </div>

                          {/* 摘要 */}
                          <p className="text-xs text-neutral-400 line-clamp-2 mb-2">
                            {news.summary}
                          </p>

                          {/* 底部信息 */}
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Badge
                                variant="outline"
                                className="text-xs border-neutral-700 text-neutral-400"
                              >
                                {news.source}
                              </Badge>
                              <span className="text-xs text-neutral-500 flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {news.publishTime}
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              {news.keywords.slice(0, 3).map((keyword) => (
                                <Badge
                                  key={keyword}
                                  variant="outline"
                                  className="text-xs border-neutral-700 text-neutral-500 bg-neutral-800/50"
                                >
                                  {keyword}
                                </Badge>
                              ))}
                              {news.isPushed && (
                                <Send className="w-3 h-3 text-green-500" />
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </ScrollArea>
        </div>

        {/* 右侧分析栏 */}
        <div className="w-80 border-l border-neutral-800 bg-neutral-900/50 flex flex-col">
          <ScrollArea className="flex-1">
            {/* 情绪分布 */}
            <div className="p-4 border-b border-neutral-800">
              <h3 className="text-sm font-medium text-neutral-300 uppercase tracking-wider mb-4 flex items-center gap-2">
                <Activity className="w-4 h-4 text-orange-500" />
                情绪分布
              </h3>
              {sentimentDist.length === 0 ? (
                <p className="text-xs text-neutral-500">暂无数据</p>
              ) : (
                <div className="space-y-3">
                  {sentimentDist.map((bucket) => {
                    const pct = sentimentTotal > 0 ? Math.round((bucket.count / sentimentTotal) * 100) : 0
                    const label = bucket.sentiment === "positive" ? "正面" : bucket.sentiment === "negative" ? "负面" : "中性"
                    const color = bucket.sentiment === "positive" ? "text-green-400" : bucket.sentiment === "negative" ? "text-red-400" : "text-neutral-400"
                    return (
                      <div key={bucket.sentiment}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs text-neutral-400">{label}</span>
                          <div className="flex items-center gap-2">
                            <span className={`text-sm font-bold ${color}`}>{bucket.count}</span>
                            <span className="text-xs text-neutral-500">{pct}%</span>
                          </div>
                        </div>
                        <Progress
                          value={pct}
                          className="h-2 bg-neutral-800"
                        />
                      </div>
                    )
                  })}
                </div>
              )}
            </div>

            {/* 关键词热度榜 */}
            <div className="p-4 border-b border-neutral-800">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-neutral-300 uppercase tracking-wider flex items-center gap-2">
                  <Zap className="w-4 h-4 text-orange-500" />
                  关键词热度榜
                </h3>
                <div className="flex items-center gap-1 bg-neutral-800 rounded-lg p-1">
                  <button
                    onClick={() => setTimeRange("1h")}
                    className={`px-2 py-0.5 text-xs rounded ${
                      timeRange === "1h"
                        ? "bg-neutral-700 text-white"
                        : "text-neutral-400"
                    }`}
                  >
                    1小时
                  </button>
                  <button
                    onClick={() => setTimeRange("24h")}
                    className={`px-2 py-0.5 text-xs rounded ${
                      timeRange === "24h"
                        ? "bg-neutral-700 text-white"
                        : "text-neutral-400"
                    }`}
                  >
                    24小时
                  </button>
                </div>
              </div>
              {hotKeywords.length === 0 ? (
                <p className="text-xs text-neutral-500">暂无热词数据</p>
              ) : (
                <div className="space-y-2">
                  {hotKeywords.map((item, index) => (
                    <div
                      key={item.word}
                      className="flex items-center justify-between p-2 bg-neutral-800/50 rounded-lg hover:bg-neutral-800 transition-colors cursor-pointer"
                    >
                      <div className="flex items-center gap-3">
                        <span
                          className={`w-5 h-5 rounded text-xs font-bold flex items-center justify-center ${
                            index < 3
                              ? "bg-orange-500 text-white"
                              : "bg-neutral-700 text-neutral-400"
                          }`}
                        >
                          {index + 1}
                        </span>
                        <span className="text-sm text-white">{item.word}</span>
                      </div>
                      <span className="text-xs text-neutral-400 font-mono">{item.count}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 重大新闻推送记录 */}
            <div className="p-4">
              <h3 className="text-sm font-medium text-neutral-300 uppercase tracking-wider mb-4 flex items-center gap-2">
                <Send className="w-4 h-4 text-orange-500" />
                推送记录
              </h3>
              {pushRecords.length === 0 ? (
                <p className="text-xs text-neutral-500">暂无推送记录</p>
              ) : (
                <div className="space-y-3">
                  {pushRecords.map((record, index) => (
                    <div
                      key={index}
                      className="p-3 bg-neutral-800/50 rounded-lg border border-neutral-800"
                    >
                      <p className="text-sm text-white line-clamp-1 mb-2">{record.title}</p>
                      <div className="flex items-center justify-between text-xs">
                        <Badge
                          variant="outline"
                          className="border-green-500/30 text-green-400"
                        >
                          {record.source}
                        </Badge>
                        <span className="text-neutral-500">{record.time}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </ScrollArea>
        </div>
      </div>
    </div>
  )
}
