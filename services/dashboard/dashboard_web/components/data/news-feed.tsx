"use client"

import { useState, useEffect, useCallback, useMemo } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Search,
  RefreshCw,
  TrendingUp,
  AlertCircle,
  MessageSquare,
  ExternalLink,
  Globe,
  Rss,
  Clock,
  BarChart2,
} from "lucide-react"
import { dataApi, NewsApiRecord, RssRecord, SentimentRecord } from "@/lib/api/data"

// ── 统一条目结构 ─────────────────────────────────────────────
interface FeedItem {
  uid: string
  source: string
  feed: string
  title: string
  summary: string
  url: string | null
  timestamp: string
  type: "news_api" | "rss"
  mode: string
}

function toFeedItem(r: NewsApiRecord): FeedItem {
  return {
    uid: r.uid,
    source: r.source,
    feed: r.source,
    title: r.title || "(无标题)",
    summary: r.content?.slice(0, 200) || "",
    url: r.url || null,
    timestamp: r.timestamp,
    type: "news_api",
    mode: r.mode,
  }
}

function rssToFeedItem(r: RssRecord): FeedItem {
  return {
    uid: r.uid,
    source: r.indicator,
    feed: r.feed || r.indicator,
    title: r.title || "(无标题)",
    summary: r.summary?.slice(0, 200) || r.full_text?.slice(0, 200) || "",
    url: r.link || null,
    timestamp: r.timestamp,
    type: "rss",
    mode: r.mode,
  }
}

function fmtTime(ts: string): string {
  try {
    const d = new Date(ts)
    if (isNaN(d.getTime())) return ts.slice(0, 16)
    const now = new Date()
    const diffMs = now.getTime() - d.getTime()
    const diffH = diffMs / (1000 * 60 * 60)
    if (diffH < 1) return `${Math.round(diffMs / 60000)}分钟前`
    if (diffH < 24) return `${Math.round(diffH)}小时前`
    return d.toLocaleDateString("zh-CN", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" })
  } catch {
    return ts.slice(0, 16)
  }
}

function SentimentPanel({ records }: { records: SentimentRecord[] }) {
  const latest = useMemo(() => {
    const map = new Map<string, SentimentRecord>()
    for (const r of records) {
      const existing = map.get(r.indicator + "_" + r.item)
      if (!existing || r.timestamp > existing.timestamp) map.set(r.indicator + "_" + r.item, r)
    }
    return Array.from(map.values()).slice(0, 10)
  }, [records])

  return (
    <div className="space-y-1.5">
      {latest.length === 0 ? (
        <p className="text-xs text-muted-foreground py-2">暂无情绪数据</p>
      ) : (
        latest.map((r) => (
          <div key={r.indicator + r.item + r.timestamp} className="flex items-center justify-between px-2.5 py-1.5 rounded-md bg-muted/30">
            <span className="text-xs text-muted-foreground truncate max-w-[110px]">
              {r.item || r.indicator}
            </span>
            <span className={`text-xs font-mono font-semibold ${
              r.item === "上涨" || r.item === "涨停" ? "text-green-400" :
              r.item === "下跌" || r.item === "跌停" ? "text-red-400" : "text-foreground"
            }`}>
              {r.value != null ? r.value.toLocaleString() : "—"}
            </span>
          </div>
        ))
      )}
    </div>
  )
}

type TabType = "all" | "news_api" | "rss"

export default function NewsFeed() {
  const [tab, setTab] = useState<TabType>("all")
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedSource, setSelectedSource] = useState("全部")
  const [isLoading, setIsLoading] = useState(true)
  const [fetchError, setFetchError] = useState(false)

  const [newsApiItems, setNewsApiItems] = useState<FeedItem[]>([])
  const [rssItems, setRssItems] = useState<FeedItem[]>([])
  const [sentimentRecords, setSentimentRecords] = useState<SentimentRecord[]>([])
  const [lastUpdate, setLastUpdate] = useState("")

  const fetchData = useCallback(async () => {
    setIsLoading(true)
    setFetchError(false)
    try {
      const [naRes, rssRes, sentRes] = await Promise.all([
        dataApi.getNewsApiContext().catch(() => ({ records: [] as NewsApiRecord[], count: 0, data_type: "" })),
        dataApi.getRssContext().catch(() => ({ records: [] as RssRecord[], count: 0, data_type: "" })),
        dataApi.getSentimentContext().catch(() => ({ records: [] as SentimentRecord[], count: 0, data_type: "" })),
      ])
      setNewsApiItems(naRes.records.map(toFeedItem))
      setRssItems(rssRes.records.map(rssToFeedItem))
      setSentimentRecords(sentRes.records)
      setLastUpdate(new Date().toLocaleTimeString("zh-CN"))
    } catch {
      setFetchError(true)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    const t = setInterval(fetchData, 60000)
    return () => clearInterval(t)
  }, [fetchData])

  const allItems = useMemo(() => {
    const base = tab === "news_api" ? newsApiItems : tab === "rss" ? rssItems : [...newsApiItems, ...rssItems]
    return [...base].sort((a, b) => {
      try { return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime() }
      catch { return 0 }
    })
  }, [tab, newsApiItems, rssItems])

  const sources = useMemo(() => {
    const s = new Set(allItems.map(i => i.feed))
    return ["全部", ...Array.from(s).sort()]
  }, [allItems])

  const filtered = useMemo(() => {
    return allItems.filter(item => {
      if (selectedSource !== "全部" && item.feed !== selectedSource) return false
      if (searchTerm) {
        const q = searchTerm.toLowerCase()
        if (!item.title.toLowerCase().includes(q) && !item.summary.toLowerCase().includes(q) && !item.feed.toLowerCase().includes(q)) return false
      }
      return true
    })
  }, [allItems, selectedSource, searchTerm])

  if (isLoading) {
    return (
      <div className="p-6 space-y-4">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          <div className="lg:col-span-3 space-y-3">
            {[1, 2, 3, 4, 5].map(i => <Skeleton key={i} className="h-24" />)}
          </div>
          <Skeleton className="h-96" />
        </div>
      </div>
    )
  }

  return (
    <div className="h-[calc(100vh-3.5rem)] flex flex-col">
      {/* ── 顶栏 ─────────────────────────────────────────────── */}
      <div className="px-5 py-3 border-b border-border bg-card/50 space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold text-foreground">新闻资讯</h1>
            <p className="text-xs text-muted-foreground mt-0.5">
              news_api {newsApiItems.length} 条 · RSS {rssItems.length} 条
              {lastUpdate && ` · 更新于 ${lastUpdate}`}
            </p>
          </div>
          <Button variant="outline" size="sm" onClick={fetchData} className="gap-1.5">
            <RefreshCw className="w-3.5 h-3.5" />
            刷新
          </Button>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Tabs value={tab} onValueChange={v => { setTab(v as TabType); setSelectedSource("全部") }}>
            <TabsList className="h-8 bg-muted/50">
              <TabsTrigger value="all" className="h-6 text-xs">全部 ({newsApiItems.length + rssItems.length})</TabsTrigger>
              <TabsTrigger value="news_api" className="h-6 text-xs gap-1">
                <Globe className="w-3 h-3" />新闻 API ({newsApiItems.length})
              </TabsTrigger>
              <TabsTrigger value="rss" className="h-6 text-xs gap-1">
                <Rss className="w-3 h-3" />RSS ({rssItems.length})
              </TabsTrigger>
            </TabsList>
          </Tabs>
          <div className="relative flex-1 min-w-[180px] max-w-xs">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
            <Input
              placeholder="搜索标题/来源..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="pl-8 h-8 text-xs"
            />
          </div>
          <span className="text-xs text-muted-foreground">{filtered.length} 条</span>
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto pb-0.5">
          {sources.slice(0, 20).map(src => (
            <button
              key={src}
              onClick={() => setSelectedSource(src)}
              className={`px-2.5 py-1 text-xs rounded-md whitespace-nowrap transition-colors flex-shrink-0 ${
                selectedSource === src
                  ? "bg-orange-500 text-white"
                  : "bg-muted text-muted-foreground hover:text-foreground"
              }`}
            >
              {src}
            </button>
          ))}
          {sources.length > 20 && (
            <span className="text-xs text-muted-foreground flex-shrink-0">+{sources.length - 20}</span>
          )}
        </div>
      </div>

      {/* ── 主体 ─────────────────────────────────────────────── */}
      <div className="flex-1 flex overflow-hidden">
        <ScrollArea className="flex-1">
          <div className="p-4 space-y-2.5">
            {fetchError ? (
              <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
                <AlertCircle className="w-10 h-10 mb-3 text-red-500/60" />
                <p className="text-sm">数据加载失败</p>
                <Button variant="outline" size="sm" onClick={fetchData} className="mt-3">重试</Button>
              </div>
            ) : filtered.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
                <MessageSquare className="w-10 h-10 mb-3 opacity-40" />
                <p className="text-sm">暂无数据</p>
              </div>
            ) : (
              filtered.map(item => (
                <Card key={item.uid} className="hover:border-orange-500/30 transition-colors">
                  <CardContent className="p-3.5">
                    <div className="flex items-start gap-3">
                      <div className={`flex-shrink-0 w-7 h-7 rounded-md flex items-center justify-center mt-0.5 ${
                        item.type === "news_api" ? "bg-blue-500/15" : "bg-orange-500/15"
                      }`}>
                        {item.type === "news_api"
                          ? <Globe className="w-3.5 h-3.5 text-blue-400" />
                          : <Rss className="w-3.5 h-3.5 text-orange-400" />
                        }
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start gap-2 mb-1">
                          <h3 className="text-sm font-medium text-foreground leading-snug flex-1 min-w-0">
                            {item.url ? (
                              <a
                                href={item.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="hover:text-orange-400 transition-colors"
                              >
                                {item.title}
                                <ExternalLink className="w-3 h-3 inline-block ml-1 opacity-50" />
                              </a>
                            ) : item.title}
                          </h3>
                        </div>
                        {item.summary && (
                          <p className="text-xs text-muted-foreground line-clamp-2 mb-2 leading-relaxed">
                            {item.summary}
                          </p>
                        )}
                        <div className="flex items-center gap-2 flex-wrap">
                          <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-4">
                            {item.feed}
                          </Badge>
                          {item.mode === "mock" && (
                            <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-4 border-yellow-500/40 text-yellow-500">
                              模拟
                            </Badge>
                          )}
                          <span className="text-[10px] text-muted-foreground flex items-center gap-1 ml-auto">
                            <Clock className="w-2.5 h-2.5" />
                            {fmtTime(item.timestamp)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </ScrollArea>

        {/* ── 右侧情绪面板 ──────────────────────────────────── */}
        <div className="w-56 flex-shrink-0 border-l border-border bg-card/50">
          <ScrollArea className="h-full">
            <div className="p-4 space-y-5">
              <div>
                <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider mb-2.5 flex items-center gap-1">
                  <BarChart2 className="w-3 h-3" />数据来源
                </p>
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between px-2.5 py-1.5 rounded-md bg-blue-500/10 border border-blue-500/20">
                    <span className="text-xs text-blue-400 flex items-center gap-1">
                      <Globe className="w-3 h-3" />新闻 API
                    </span>
                    <span className="text-xs font-mono font-bold text-blue-400">{newsApiItems.length}</span>
                  </div>
                  <div className="flex items-center justify-between px-2.5 py-1.5 rounded-md bg-orange-500/10 border border-orange-500/20">
                    <span className="text-xs text-orange-400 flex items-center gap-1">
                      <Rss className="w-3 h-3" />RSS
                    </span>
                    <span className="text-xs font-mono font-bold text-orange-400">{rssItems.length}</span>
                  </div>
                </div>
              </div>

              <div>
                <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider mb-2.5 flex items-center gap-1">
                  <TrendingUp className="w-3 h-3" />市场情绪
                </p>
                <SentimentPanel records={sentimentRecords} />
              </div>

              <div>
                <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider mb-2.5">
                  热门来源
                </p>
                {(() => {
                  const cnt = new Map<string, number>()
                  allItems.forEach(i => cnt.set(i.feed, (cnt.get(i.feed) ?? 0) + 1))
                  return Array.from(cnt.entries())
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 8)
                    .map(([feed, count]) => (
                      <div
                        key={feed}
                        className="flex items-center justify-between px-2 py-1 rounded hover:bg-muted/40 cursor-pointer transition-colors"
                        onClick={() => setSelectedSource(feed)}
                      >
                        <span className="text-[11px] text-muted-foreground truncate max-w-[110px]">{feed}</span>
                        <span className="text-[11px] font-mono text-foreground ml-1">{count}</span>
                      </div>
                    ))
                })()}
              </div>
            </div>
          </ScrollArea>
        </div>
      </div>
    </div>
  )
}
