"use client"

import { useState } from "react"
import { Brain, CheckCircle, XCircle, Clock, Filter, TrendingUp, TrendingDown } from "lucide-react"
import { MainLayout } from "@/components/layout/main-layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { toast } from "sonner"

const signals = [
  { id: "SIG-001", model: "趋势跟踪模型 v2.3", symbol: "IF2501", direction: "多", confidence: 87, price: 3892.4, time: "09:31:05", status: "待审" },
  { id: "SIG-002", model: "均值回归模型", symbol: "CU主力", direction: "空", confidence: 72, price: 75200, time: "09:28:44", status: "待审" },
  { id: "SIG-003", model: "量价背离模型", symbol: "RB2501", direction: "多", confidence: 91, price: 3268, time: "09:25:18", status: "已批准" },
  { id: "SIG-004", model: "多因子选股 v1.1", symbol: "IC2501", direction: "空", confidence: 65, price: 5588.6, time: "09:20:33", status: "已拒绝" },
  { id: "SIG-005", model: "高频套利策略", symbol: "IH2501", direction: "多", confidence: 78, price: 2756.4, time: "09:15:02", status: "已批准" },
  { id: "SIG-006", model: "趋势跟踪模型 v2.3", symbol: "AU2506", direction: "空", confidence: 83, price: 624.2, time: "09:10:55", status: "待审" },
]

type SignalStatus = "全部" | "待审" | "已批准" | "已拒绝"

export default function DecisionSignalPage() {
  const [filterStatus, setFilterStatus] = useState<SignalStatus>("全部")
  const [signalList, setSignalList] = useState(signals)

  const filtered = filterStatus === "全部" ? signalList : signalList.filter((s) => s.status === filterStatus)

  const handleApprove = (id: string) => {
    setSignalList((prev) => prev.map((s) => s.id === id ? { ...s, status: "已批准" } : s))
    toast.success(`信号 ${id} 已批准`)
  }

  const handleReject = (id: string) => {
    setSignalList((prev) => prev.map((s) => s.id === id ? { ...s, status: "已拒绝" } : s))
    toast.error(`信号 ${id} 已拒绝`)
  }

  const pendingCount = signalList.filter((s) => s.status === "待审").length

  return (
    <MainLayout title="智能决策" subtitle="信号审查">
      <div className="p-4 md:p-6 space-y-6">
        {/* 统计概览 */}
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: "待审信号", value: pendingCount, color: "text-yellow-400", border: "border-yellow-500/30" },
            { label: "今日已批准", value: signalList.filter((s) => s.status === "已批准").length, color: "text-green-400", border: "border-green-500/30" },
            { label: "今日已拒绝", value: signalList.filter((s) => s.status === "已拒绝").length, color: "text-red-400", border: "border-red-500/30" },
          ].map((stat) => (
            <Card key={stat.label} className={cn("bg-card border", stat.border)}>
              <CardContent className="p-4 text-center">
                <p className="text-xs text-muted-foreground mb-1">{stat.label}</p>
                <p className={cn("text-3xl font-bold", stat.color)}>{stat.value}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* 信号列表 */}
        <Card className="bg-card border-border">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-base text-foreground flex items-center gap-2">
              <Brain className="w-4 h-4 text-purple-500" />
              信号列表
            </CardTitle>
            <div className="flex gap-2">
              {(["全部", "待审", "已批准", "已拒绝"] as SignalStatus[]).map((s) => (
                <Button
                  key={s}
                  size="sm"
                  variant={filterStatus === s ? "default" : "outline"}
                  onClick={() => setFilterStatus(s)}
                  className={cn(
                    "h-7 text-xs",
                    filterStatus === s ? "bg-purple-600 hover:bg-purple-700 text-white" : "border-border text-muted-foreground hover:text-foreground"
                  )}
                >
                  {s}
                </Button>
              ))}
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    {["信号ID", "模型", "合约", "方向", "置信度", "参考价", "时间", "状态", "操作"].map((h) => (
                      <th key={h} className="text-left py-3 px-4 text-xs text-muted-foreground font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((sig) => (
                    <tr key={sig.id} className="border-b border-border/50 hover:bg-accent/20">
                      <td className="py-3 px-4 text-muted-foreground font-mono text-xs">{sig.id}</td>
                      <td className="py-3 px-4 text-foreground text-xs">{sig.model}</td>
                      <td className="py-3 px-4 text-foreground font-mono">{sig.symbol}</td>
                      <td className="py-3 px-4">
                        <Badge variant="outline" className={cn(
                          "text-xs",
                          sig.direction === "多" ? "border-green-500/30 text-green-400" : "border-red-500/30 text-red-400"
                        )}>
                          {sig.direction === "多" ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                          {sig.direction}
                        </Badge>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 bg-accent rounded-full overflow-hidden">
                            <div className={cn("h-full rounded-full", sig.confidence >= 80 ? "bg-green-500" : sig.confidence >= 65 ? "bg-yellow-500" : "bg-red-500")} style={{ width: `${sig.confidence}%` }} />
                          </div>
                          <span className="text-xs font-mono text-muted-foreground">{sig.confidence}%</span>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-muted-foreground font-mono text-xs">{sig.price.toLocaleString()}</td>
                      <td className="py-3 px-4 text-muted-foreground text-xs font-mono">{sig.time}</td>
                      <td className="py-3 px-4">
                        <Badge variant="outline" className={cn(
                          "text-xs",
                          sig.status === "待审" ? "border-yellow-500/30 text-yellow-400" :
                          sig.status === "已批准" ? "border-green-500/30 text-green-400" :
                          "border-red-500/30 text-red-400"
                        )}>
                          {sig.status === "待审" ? <Clock className="w-3 h-3 mr-1" /> : sig.status === "已批准" ? <CheckCircle className="w-3 h-3 mr-1" /> : <XCircle className="w-3 h-3 mr-1" />}
                          {sig.status}
                        </Badge>
                      </td>
                      <td className="py-3 px-4">
                        {sig.status === "待审" && (
                          <div className="flex gap-1">
                            <Button size="sm" onClick={() => handleApprove(sig.id)} className="h-7 px-2 bg-green-600 hover:bg-green-700 text-white text-xs">
                              批准
                            </Button>
                            <Button size="sm" onClick={() => handleReject(sig.id)} variant="outline" className="h-7 px-2 border-red-500/50 text-red-400 hover:bg-red-500/10 text-xs">
                              拒绝
                            </Button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  )
}
