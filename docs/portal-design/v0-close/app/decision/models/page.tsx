"use client"

import { Brain, Cpu, Cloud, Activity, ChevronRight } from "lucide-react"
import Link from "next/link"
import { MainLayout } from "@/components/layout/main-layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"

const models = [
  {
    id: "model-01", name: "趋势跟踪模型 v2.3", type: "本地", engine: "PyTorch",
    status: "运行中", accuracy: 87.4, todaySignals: 12, lastTrained: "2025-01-01",
    description: "基于LSTM的时序趋势预测模型，适用于商品期货",
  },
  {
    id: "model-02", name: "均值回归模型", type: "本地", engine: "Scikit-learn",
    status: "空闲", accuracy: 74.2, todaySignals: 5, lastTrained: "2024-12-28",
    description: "统计套利模型，利用协整关系识别价差回归机会",
  },
  {
    id: "model-03", name: "量价背离模型", type: "本地", engine: "XGBoost",
    status: "运行中", accuracy: 91.1, todaySignals: 18, lastTrained: "2025-01-03",
    description: "通过量价关系异常检测潜在的趋势反转信号",
  },
  {
    id: "model-04", name: "GPT-4o 宏观分析", type: "在线", engine: "OpenAI",
    status: "就绪", accuracy: null, todaySignals: 3, lastTrained: "N/A",
    description: "利用大语言模型分析宏观新闻和政策，生成基本面信号",
  },
  {
    id: "model-05", name: "Claude 策略优化", type: "在线", engine: "Anthropic",
    status: "就绪", accuracy: null, todaySignals: 2, lastTrained: "N/A",
    description: "用于策略参数优化和风险评估的 Claude 智能体",
  },
]

const factors = [
  { name: "动量因子 (12-1)", category: "技术", importance: 0.18, direction: "正向" },
  { name: "波动率因子", category: "风险", importance: 0.15, direction: "负向" },
  { name: "成交量变化率", category: "量价", importance: 0.12, direction: "正向" },
  { name: "资金流入指数", category: "资金", importance: 0.11, direction: "正向" },
  { name: "基差率", category: "期现", importance: 0.10, direction: "混合" },
  { name: "跨期价差", category: "期现", importance: 0.09, direction: "混合" },
]

export default function DecisionModelsPage() {
  return (
    <MainLayout title="智能决策" subtitle="模型与因子">
      <div className="p-4 md:p-6 space-y-6">
        {/* 模型列表 */}
        <div>
          <h2 className="text-base font-semibold text-foreground mb-4 flex items-center gap-2">
            <Brain className="w-4 h-4 text-purple-500" />
            已部署模型
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {models.map((model) => (
              <Card key={model.id} className="bg-card border-border hover:border-purple-500/30 transition-colors cursor-pointer group">
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      {model.type === "本地" ? (
                        <Cpu className="w-4 h-4 text-purple-500 shrink-0" />
                      ) : (
                        <Cloud className="w-4 h-4 text-blue-500 shrink-0" />
                      )}
                      <CardTitle className="text-sm text-foreground leading-snug">{model.name}</CardTitle>
                    </div>
                    <Badge variant="outline" className={cn(
                      "text-xs shrink-0",
                      model.status === "运行中" ? "border-green-500/30 text-green-400" :
                      model.status === "就绪" ? "border-blue-500/30 text-blue-400" :
                      "border-border text-muted-foreground"
                    )}>
                      {model.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-muted-foreground mb-3 leading-relaxed">{model.description}</p>
                  <div className="grid grid-cols-3 gap-2 text-center mb-3">
                    <div>
                      <p className="text-xs text-muted-foreground">引擎</p>
                      <p className="text-xs text-muted-foreground font-mono">{model.engine}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">准确率</p>
                      <p className="text-xs text-purple-400 font-mono">{model.accuracy ? `${model.accuracy}%` : "N/A"}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">今日信号</p>
                      <p className="text-xs text-foreground font-mono">{model.todaySignals}</p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>上次训练: {model.lastTrained}</span>
                    <ChevronRight className="w-3 h-3 group-hover:text-purple-400 transition-colors" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* 因子分析 */}
        <Card className="bg-card border-border">
          <CardHeader className="pb-3">
            <CardTitle className="text-base text-foreground flex items-center gap-2">
              <Activity className="w-4 h-4 text-purple-500" />
              因子重要性排行
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {factors.map((factor, idx) => (
              <div key={factor.name} className="flex items-center gap-4">
                <span className="w-5 text-xs text-muted-foreground text-right">{idx + 1}</span>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-foreground">{factor.name}</span>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs border-border text-muted-foreground">{factor.category}</Badge>
                      <Badge variant="outline" className={cn(
                        "text-xs",
                        factor.direction === "正向" ? "border-green-500/30 text-green-400" :
                        factor.direction === "负向" ? "border-red-500/30 text-red-400" :
                        "border-yellow-500/30 text-yellow-400"
                      )}>{factor.direction}</Badge>
                      <span className="text-xs font-mono text-muted-foreground w-10 text-right">
                        {(factor.importance * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  <Progress value={factor.importance * 100} className="h-1.5" />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  )
}
