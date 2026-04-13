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

// 模拟新闻数据
const newsData: NewsItem[] = [
  {
    id: "1",
    title: "美联储官员暗示可能在年内降息，美债收益率应声下跌",
    source: "财联社",
    publishTime: "10:42",
    summary: "美联储理事沃勒周三表示，如果通胀继续放缓，美联储可能最早在今年夏天降息。此番言论推动美债收益率走低，美股期货上涨。",
    keywords: ["美联储", "降息", "美债"],
    sentiment: "positive",
    isImportant: true,
    isPushed: true,
    isNew: true,
  },
  {
    id: "2",
    title: "沪铜主力合约突破78000元关口，创近三月新高",
    source: "东方财富",
    publishTime: "10:38",
    summary: "受全球铜矿供应担忧及国内需求预期改善影响，沪铜期货主力合约今日盘中突破78000元/吨，为近三个月以来首次。",
    keywords: ["沪铜", "期货", "突破"],
    sentiment: "positive",
    isImportant: true,
    isPushed: true,
    isNew: true,
  },
  {
    id: "3",
    title: "国内钢材库存连续第八周下降，市场情绪有所改善",
    source: "新浪财经",
    publishTime: "10:35",
    summary: "据最新数据显示，国内主要钢材品种社会库存连续第八周下降，降幅有所扩大，显示终端需求正在逐步恢复。",
    keywords: ["钢材", "库存", "需求"],
    sentiment: "positive",
    isImportant: false,
    isPushed: false,
  },
  {
    id: "4",
    title: "欧佩克+意外宣布延长减产至年底，油价短线跳涨",
    source: "路透社",
    publishTime: "10:30",
    summary: "欧佩克+周三意外宣布将自愿减产措施延长至2025年底，布伦特原油价格短线跳涨超过2%。",
    keywords: ["欧佩克", "原油", "减产"],
    sentiment: "positive",
    isImportant: true,
    isPushed: true,
  },
  {
    id: "5",
    title: "豆粕期货承压下行，南美大豆丰产预期施压",
    source: "财联社",
    publishTime: "10:25",
    summary: "受南美大豆丰产预期及国内养殖需求疲软影响，豆粕期货今日延续弱势，主力合约跌幅超过1%。",
    keywords: ["豆粕", "大豆", "养殖"],
    sentiment: "negative",
    isImportant: false,
    isPushed: false,
  },
  {
    id: "6",
    title: "上海金属网：LME铜库存骤降15%，供应紧张加剧",
    source: "上海金属网",
    publishTime: "10:20",
    summary: "LME官方数据显示，铜库存在过去一周骤降15%至历史低位附近，反映出全球铜市场供应紧张局面正在加剧。",
    keywords: ["LME", "铜库存", "供应"],
    sentiment: "positive",
    isImportant: true,
    isPushed: false,
  },
  {
    id: "7",
    title: "中国3月PMI数据超预期，制造业重回扩张区间",
    source: "证券时报",
    publishTime: "10:15",
    summary: "国家统计局公布数据显示，3月制造业PMI录得50.8%，重回扩张区间，超出市场预期，显示经济复苏动能增强。",
    keywords: ["PMI", "制造业", "经济"],
    sentiment: "positive",
    isImportant: true,
    isPushed: true,
  },
  {
    id: "8",
    title: "BDI指数连续第五日上涨，航运市场持续复苏",
    source: "彭博",
    publishTime: "10:10",
    summary: "波罗的海干散货指数（BDI）周三上涨2.3%，连续第五个交易日走高，反映全球贸易活动正在稳步恢复。",
    keywords: ["BDI", "航运", "贸易"],
    sentiment: "positive",
    isImportant: false,
    isPushed: false,
  },
  {
    id: "9",
    title: "螺纹钢期货震荡走弱，房地产需求担忧重燃",
    source: "东方财富",
    publishTime: "10:05",
    summary: "尽管钢材库存下降，但市场对房地产需求的担忧再度升温，螺纹钢期货今日震荡走弱，午盘跌幅扩大。",
    keywords: ["螺纹钢", "房地产", "需求"],
    sentiment: "negative",
    isImportant: false,
    isPushed: false,
  },
  {
    id: "10",
    title: "黄金ETF持仓量回升，避险情绪支撑金价",
    source: "财联社",
    publishTime: "10:00",
    summary: "全球最大黄金ETF-SPDR持仓量连续第三周回升，地缘政治不确定性和避险情绪为金价提供支撑。",
    keywords: ["黄金", "ETF", "避险"],
    sentiment: "neutral",
    isImportant: false,
    isPushed: false,
  },
]

// 情绪指标数据
const sentimentIndicators = [
  { name: "恐慌贪婪指数", value: 62, status: "贪婪", color: "text-green-400", change: "+5" },
  { name: "社交热度", value: 78, status: "高", color: "text-orange-400", change: "+12" },
  { name: "消费者情绪", value: 45, status: "中性", color: "text-neutral-400", change: "-2" },
  { name: "不确定性指数", value: 28, status: "低", color: "text-green-400", change: "-8" },
]

// 热词榜
const hotKeywords = [
  { word: "美联储", count: 156, trend: "up" },
  { word: "降息", count: 142, trend: "up" },
  { word: "铜价", count: 98, trend: "up" },
  { word: "PMI", count: 87, trend: "new" },
  { word: "原油", count: 76, trend: "up" },
  { word: "房地产", count: 65, trend: "down" },
  { word: "黄金", count: 58, trend: "stable" },
  { word: "库存", count: 52, trend: "up" },
]

// 推送记录
const pushRecords = [
  { title: "美联储官员暗示可能在年内降息", channel: "飞书新闻通道", time: "10:42" },
  { title: "沪铜主力合约突破78000元关口", channel: "飞书新闻通道", time: "10:38" },
  { title: "欧佩克+意外宣布延长减产至年底", channel: "飞书交易通道", time: "10:30" },
  { title: "中国3月PMI数据超预期", channel: "飞书新闻通道", time: "10:15" },
]

const sources = ["全部", "财联社", "东方财富", "新浪财经", "上海金属网", "证券时报", "RSS聚合", "宏观资讯"]

export default function NewsFeedPage() {
  const [selectedSource, setSelectedSource] = useState("全部")
  const [searchTerm, setSearchTerm] = useState("")
  const [showImportantOnly, setShowImportantOnly] = useState(false)
  const [autoScroll, setAutoScroll] = useState(true)
  const [isLoading, setIsLoading] = useState(false)
  const [timeRange, setTimeRange] = useState<"1h" | "24h">("1h")

  const filteredNews = newsData.filter((news) => {
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
    setIsLoading(true)
    setTimeout(() => setIsLoading(false), 800)
  }

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
          </ScrollArea>
        </div>

        {/* 右侧分析栏 */}
        <div className="w-80 border-l border-neutral-800 bg-neutral-900/50 flex flex-col">
          <ScrollArea className="flex-1">
            {/* 情绪指数仪表盘 */}
            <div className="p-4 border-b border-neutral-800">
              <h3 className="text-sm font-medium text-neutral-300 uppercase tracking-wider mb-4 flex items-center gap-2">
                <Activity className="w-4 h-4 text-orange-500" />
                情绪指数仪表盘
              </h3>
              <div className="space-y-4">
                {sentimentIndicators.map((indicator) => (
                  <div key={indicator.name}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-neutral-400">{indicator.name}</span>
                      <div className="flex items-center gap-2">
                        <span className={`text-sm font-bold ${indicator.color}`}>
                          {indicator.value}
                        </span>
                        <Badge
                          variant="outline"
                          className={`text-xs ${
                            indicator.change.startsWith("+")
                              ? "border-green-500/30 text-green-400"
                              : "border-red-500/30 text-red-400"
                          }`}
                        >
                          {indicator.change}
                        </Badge>
                      </div>
                    </div>
                    <Progress
                      value={indicator.value}
                      className="h-2 bg-neutral-800"
                    />
                    <p className="text-xs text-neutral-500 mt-1">{indicator.status}</p>
                  </div>
                ))}
              </div>
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
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-neutral-400 font-mono">{item.count}</span>
                      {item.trend === "up" && <TrendingUp className="w-3 h-3 text-green-500" />}
                      {item.trend === "down" && <TrendingDown className="w-3 h-3 text-red-500" />}
                      {item.trend === "new" && (
                        <Badge className="text-xs bg-orange-500/20 text-orange-400 border-0">NEW</Badge>
                      )}
                      {item.trend === "stable" && <Minus className="w-3 h-3 text-neutral-500" />}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 重大新闻推送记录 */}
            <div className="p-4">
              <h3 className="text-sm font-medium text-neutral-300 uppercase tracking-wider mb-4 flex items-center gap-2">
                <Send className="w-4 h-4 text-orange-500" />
                推送记录
              </h3>
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
                        {record.channel}
                      </Badge>
                      <span className="text-neutral-500">{record.time}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </ScrollArea>
        </div>
      </div>
    </div>
  )
}
