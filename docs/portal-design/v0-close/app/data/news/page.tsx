"use client"

import { Newspaper, ExternalLink, TrendingUp, TrendingDown, Minus } from "lucide-react"
import { MainLayout } from "@/components/layout/main-layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

const newsItems = [
  {
    id: 1, title: "央行宣布下调存款准备金率0.5个百分点，释放流动性约1万亿元",
    source: "新华社", time: "09:45", category: "宏观政策", sentiment: "利多",
    related: ["股指期货", "债券"],
  },
  {
    id: 2, title: "1月份PMI数据超预期，制造业持续扩张",
    source: "国家统计局", time: "09:30", category: "经济数据", sentiment: "利多",
    related: ["商品期货", "股指"],
  },
  {
    id: 3, title: "国际铜价下跌，美元走强抑制商品需求",
    source: "彭博社", time: "08:58", category: "国际市场", sentiment: "利空",
    related: ["铜", "铝"],
  },
  {
    id: 4, title: "螺纹钢库存持续下降，钢材现货价格小幅上涨",
    source: "中国钢铁工业协会", time: "08:30", category: "行业报告", sentiment: "利多",
    related: ["螺纹钢", "热卷"],
  },
  {
    id: 5, title: "美联储会议纪要显示维持利率不变立场",
    source: "路透社", time: "昨日 22:00", category: "国际宏观", sentiment: "中性",
    related: ["黄金", "外汇"],
  },
  {
    id: 6, title: "大豆主产区天气干旱，农产品期货出现上涨",
    source: "农业农村部", time: "昨日 18:00", category: "农产品", sentiment: "利多",
    related: ["豆粕", "菜粕"],
  },
]

const sentimentConfig: Record<string, { color: string; icon: typeof TrendingUp; border: string }> = {
  利多: { color: "text-green-400", icon: TrendingUp, border: "border-green-500/30" },
  利空: { color: "text-red-400", icon: TrendingDown, border: "border-red-500/30" },
  中性: { color: "text-muted-foreground", icon: Minus, border: "border-border" },
}

export default function DataNewsPage() {
  return (
    <MainLayout title="数据采集" subtitle="新闻资讯">
      <div className="p-4 md:p-6 space-y-6">
        {/* 情感统计 */}
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: "利多信号", count: newsItems.filter((n) => n.sentiment === "利多").length, color: "text-green-400", border: "border-green-500/30" },
            { label: "利空信号", count: newsItems.filter((n) => n.sentiment === "利空").length, color: "text-red-400", border: "border-red-500/30" },
            { label: "中性信号", count: newsItems.filter((n) => n.sentiment === "中性").length, color: "text-muted-foreground", border: "border-border" },
          ].map((stat) => (
            <Card key={stat.label} className={cn("bg-card border", stat.border)}>
              <CardContent className="p-4 text-center">
                <p className="text-xs text-muted-foreground mb-1">{stat.label}</p>
                <p className={cn("text-2xl font-bold", stat.color)}>{stat.count}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* 新闻列表 */}
        <Card className="bg-card border-border">
          <CardHeader className="pb-3">
            <CardTitle className="text-base text-foreground flex items-center gap-2">
              <Newspaper className="w-4 h-4 text-cyan-500" />
              今日资讯
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {newsItems.map((news) => {
              const cfg = sentimentConfig[news.sentiment]
              const SentimentIcon = cfg.icon
              return (
                <div key={news.id} className="p-4 bg-accent/50 rounded-lg hover:bg-accent transition-colors cursor-pointer group">
                  <div className="flex items-start gap-3">
                    <div className={cn("mt-0.5 shrink-0", cfg.color)}>
                      <SentimentIcon className="w-4 h-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <h4 className="text-sm text-foreground leading-snug group-hover:text-cyan-400 transition-colors">
                          {news.title}
                        </h4>
                        <ExternalLink className="w-3.5 h-3.5 text-muted-foreground shrink-0 mt-0.5 group-hover:text-cyan-500 transition-colors" />
                      </div>
                      <div className="flex flex-wrap items-center gap-2 mt-2">
                        <span className="text-xs text-muted-foreground">{news.source}</span>
                        <span className="text-muted-foreground/50">·</span>
                        <span className="text-xs text-muted-foreground">{news.time}</span>
                        <Badge variant="outline" className="text-xs border-border text-muted-foreground">{news.category}</Badge>
                        <Badge variant="outline" className={cn("text-xs", cfg.border, cfg.color)}>{news.sentiment}</Badge>
                        <div className="flex gap-1">
                          {news.related.map((r) => (
                            <span key={r} className="text-xs text-cyan-500 bg-cyan-500/10 px-1.5 py-0.5 rounded">{r}</span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  )
}
