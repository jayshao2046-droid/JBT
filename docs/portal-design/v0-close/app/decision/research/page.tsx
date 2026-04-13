"use client"

import { FlaskConical, FileText, BookOpen, TrendingUp, Calendar } from "lucide-react"
import { MainLayout } from "@/components/layout/main-layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

const researchNotes = [
  { id: "RN-001", title: "动量因子在商品期货中的适用性研究", author: "admin", date: "2025-01-08", tags: ["动量", "商品期货", "因子"], status: "已完成" },
  { id: "RN-002", title: "基于 Transformer 的价格序列预测实验", author: "admin", date: "2025-01-05", tags: ["深度学习", "Transformer", "预测"], status: "进行中" },
  { id: "RN-003", title: "跨品种套利机会扫描报告 Q4 2024", author: "admin", date: "2024-12-30", tags: ["套利", "季报"], status: "已完成" },
  { id: "RN-004", title: "高频数据的噪声过滤方法对比", author: "admin", date: "2024-12-22", tags: ["高频", "信号处理"], status: "草稿" },
]

const experiments = [
  { name: "LSTM vs Transformer 价格预测", status: "进行中", progress: 68, metric: "RMSE: 0.0234" },
  { name: "多因子等权 vs IC 加权对比", status: "完成", progress: 100, metric: "信息比率: 1.34" },
  { name: "波动率聚类分析", status: "完成", progress: 100, metric: "轮廓系数: 0.72" },
  { name: "强化学习仓位管理", status: "规划中", progress: 0, metric: "--" },
]

const statusColors: Record<string, string> = {
  已完成: "border-green-500/30 text-green-400",
  进行中: "border-blue-500/30 text-blue-400",
  草稿: "border-border text-muted-foreground",
  规划中: "border-yellow-500/30 text-yellow-400",
  完成: "border-green-500/30 text-green-400",
}

export default function DecisionResearchPage() {
  return (
    <MainLayout title="智能决策" subtitle="研究中心">
      <div className="p-4 md:p-6 space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 研究笔记 */}
          <Card className="bg-card border-border">
            <CardHeader className="pb-3">
              <CardTitle className="text-base text-foreground flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-purple-500" />
                研究笔记
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {researchNotes.map((note) => (
                <div key={note.id} className="p-3 bg-accent/50 rounded-lg hover:bg-accent transition-colors cursor-pointer">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <h4 className="text-sm text-foreground leading-snug flex-1">{note.title}</h4>
                    <Badge variant="outline" className={cn("text-xs shrink-0", statusColors[note.status])}>{note.status}</Badge>
                  </div>
                  <div className="flex flex-wrap gap-1 mb-2">
                    {note.tags.map((tag) => (
                      <span key={tag} className="text-xs text-purple-400 bg-purple-500/10 px-1.5 py-0.5 rounded">#{tag}</span>
                    ))}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Calendar className="w-3 h-3" />
                    <span>{note.date}</span>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* 实验追踪 */}
          <Card className="bg-card border-border">
            <CardHeader className="pb-3">
              <CardTitle className="text-base text-foreground flex items-center gap-2">
                <FlaskConical className="w-4 h-4 text-purple-500" />
                实验追踪
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {experiments.map((exp) => (
                <div key={exp.name} className="p-3 bg-accent/50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-foreground">{exp.name}</span>
                    <Badge variant="outline" className={cn("text-xs", statusColors[exp.status])}>{exp.status}</Badge>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-1.5 bg-accent rounded-full overflow-hidden">
                      <div
                        className="h-full bg-purple-500 rounded-full transition-all"
                        style={{ width: `${exp.progress}%` }}
                      />
                    </div>
                    <span className="text-xs text-muted-foreground font-mono w-8">{exp.progress}%</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1.5 font-mono">{exp.metric}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </MainLayout>
  )
}
