"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Eye, CheckCircle, XCircle } from "lucide-react"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts"
import { fetchSignals, type DecisionRecord } from "@/lib/api"

interface SignalRow {
  id: string
  time: string
  strategy: string
  symbol: string
  direction: string
  strength: number
  factors: number
  l1: string
  l2: string
  l3: string
  status: string
}

function mapSignalRow(rec: DecisionRecord): SignalRow {
  const timeStr = rec.generated_at ? new Date(rec.generated_at).toLocaleTimeString("zh-CN", { hour12: false }) : "—"
  const l1 = rec.eligibility_status !== "rejected" ? "通过" : "拒绝"
  const l2 = rec.layer?.startsWith("L2") ? "通过" : rec.eligibility_status === "rejected" ? "拒绝" : "—"
  const l3 = rec.layer?.startsWith("L3") ? "审核中" : "—"
  const displayStatus =
    rec.publish_workflow_status === "pushed" ? "已推送"
    : rec.eligibility_status === "rejected" ? "已拒绝"
    : "待发送"
  return {
    id: rec.decision_id,
    time: timeStr,
    strategy: rec.strategy_id,
    symbol: rec.publish_target ?? "—",
    direction: rec.action === "buy" ? "多头" : rec.action === "sell" ? "空头" : "—",
    strength: rec.confidence ?? 0,
    factors: 0,
    l1,
    l2,
    l3,
    status: displayStatus,
  }
}

const getStatusBadgeColor = (status: string) => {
  switch (status) {
    case "通过":
      return "bg-green-900 text-green-400"
    case "拒绝":
      return "bg-red-900 text-red-400"
    case "审核中":
      return "bg-yellow-900 text-yellow-400"
    case "已推送":
      return "bg-blue-900 text-blue-400"
    case "已拒绝":
      return "bg-red-900 text-red-400"
    case "待发送":
      return "bg-yellow-900 text-yellow-400"
    default:
      return "bg-neutral-700 text-neutral-300"
  }
}

const getKPIColor = (color: string) => {
  switch (color) {
    case "blue":
      return "text-blue-400"
    case "red":
      return "text-red-400"
    case "green":
      return "text-green-400"
    case "purple":
      return "text-purple-400"
    case "cyan":
      return "text-cyan-400"
    default:
      return "text-white"
  }
}

export default function SignalReview() {
  const [rawSignals, setRawSignals] = useState<DecisionRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedSignal, setSelectedSignal] = useState<SignalRow | null>(null)

  useEffect(() => {
    fetchSignals()
      .then(setRawSignals)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const signalTableData = rawSignals.map(mapSignalRow)

  const total = signalTableData.length
  const rejected = signalTableData.filter(s => s.status === "已拒绝").length
  const pushed = signalTableData.filter(s => s.status === "已推送").length
  const l3Triggered = signalTableData.filter(s => s.l3 !== "—").length
  const l1Rate = total > 0 ? Math.round(((total - rejected) / total) * 100) + "%" : "—"
  const l2Rate = total > 0 ? Math.round((pushed / total) * 100) + "%" : "—"

  const kpiData = [
    { label: "候选信号数", value: String(total), unit: "条", color: "blue" },
    { label: "已拒绝数", value: String(rejected), unit: "条", color: "red" },
    { label: "L1 通过率", value: l1Rate, unit: "", color: "green" },
    { label: "L2 通过率", value: l2Rate, unit: "", color: "green" },
    { label: "L3 触发数", value: String(l3Triggered), unit: "条", color: "purple" },
    { label: "已推送模拟交易", value: String(pushed), unit: "条", color: "cyan" },
  ]

  const timelineData = [
    { stage: "生成信号", count: total },
    { stage: "L1 审查", count: total - rejected },
    { stage: "L2 审查", count: pushed + l3Triggered },
    { stage: "L3 审查", count: l3Triggered },
    { stage: "推送待执行", count: pushed },
  ]

  return (
    <div className="p-6 space-y-6 bg-neutral-950 min-h-screen">
      {/* KPI 卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
        {kpiData.map((kpi, idx) => (
          <Card key={idx} className="bg-neutral-900 border-neutral-700">
            <CardContent className="p-3">
              <p className="text-xs text-neutral-400 mb-1">{kpi.label}</p>
              <p className={`text-xl font-bold ${getKPIColor(kpi.color)}`}>{kpi.value}</p>
              {kpi.unit && <p className="text-xs text-neutral-500 mt-1">{kpi.unit}</p>}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 信号审查流 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 信号表格 */}
        <Card className="bg-neutral-900 border-neutral-700 lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">信号审查详表</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-neutral-700">
                    <th className="text-left py-2 px-2 text-neutral-400 font-medium">时间</th>
                    <th className="text-left py-2 px-2 text-neutral-400 font-medium">策略</th>
                    <th className="text-left py-2 px-2 text-neutral-400 font-medium">标的</th>
                    <th className="text-center py-2 px-2 text-neutral-400 font-medium">方向</th>
                    <th className="text-center py-2 px-2 text-neutral-400 font-medium">强度</th>
                    <th className="text-center py-2 px-2 text-neutral-400 font-medium">因子</th>
                    <th className="text-center py-2 px-2 text-neutral-400 font-medium">L1</th>
                    <th className="text-center py-2 px-2 text-neutral-400 font-medium">L2</th>
                    <th className="text-center py-2 px-2 text-neutral-400 font-medium">L3</th>
                    <th className="text-left py-2 px-2 text-neutral-400 font-medium">状态</th>
                    <th className="text-center py-2 px-2 text-neutral-400 font-medium">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {signalTableData.map((signal) => (
                    <tr key={signal.id} className="border-b border-neutral-800 hover:bg-neutral-800/50 transition-colors">
                      <td className="py-2 px-2 text-neutral-400">{signal.time}</td>
                      <td className="py-2 px-2 text-white font-medium">{signal.strategy}</td>
                      <td className="py-2 px-2 text-neutral-300">{signal.symbol}</td>
                      <td className="py-2 px-2 text-center">
                        <Badge className={signal.direction === "多头" ? "bg-green-900 text-green-400" : "bg-red-900 text-red-400"}>
                          {signal.direction === "多头" ? "↑" : "↓"}
                        </Badge>
                      </td>
                      <td className="py-2 px-2 text-center text-orange-400 font-medium">{(signal.strength * 100).toFixed(0)}%</td>
                      <td className="py-2 px-2 text-center text-neutral-400">{signal.factors}</td>
                      <td className="py-2 px-2 text-center">
                        <Badge className="bg-green-900 text-green-400 text-xs">✓</Badge>
                      </td>
                      <td className="py-2 px-2 text-center">
                        <Badge className={signal.l2 === "通过" ? "bg-green-900 text-green-400" : "bg-red-900 text-red-400"}>
                          {signal.l2 === "通过" ? "✓" : "✕"}
                        </Badge>
                      </td>
                      <td className="py-2 px-2 text-center text-xs text-neutral-400">{signal.l3}</td>
                      <td className="py-2 px-2">
                        <Badge className={getStatusBadgeColor(signal.status)}>{signal.status}</Badge>
                      </td>
                      <td className="py-2 px-2 text-center">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setSelectedSignal(signal)}
                          className="text-orange-500 hover:bg-orange-500/10 h-6 w-6 p-0"
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* 审查抽屉 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">
              {selectedSignal ? "审查详情" : "选择信号查看"}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {selectedSignal ? (
              <>
                <div className="space-y-2 border-b border-neutral-700 pb-3">
                  <p className="text-xs text-neutral-400">策略</p>
                  <p className="text-white font-medium">{selectedSignal.strategy}</p>
                </div>
                <div className="space-y-2 border-b border-neutral-700 pb-3">
                  <p className="text-xs text-neutral-400">标的 / 方向</p>
                  <p className="text-white font-medium">
                    {selectedSignal.symbol} / {selectedSignal.direction}
                  </p>
                </div>
                <div className="space-y-2 border-b border-neutral-700 pb-3">
                  <p className="text-xs text-neutral-400">信号强度</p>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-neutral-700 rounded overflow-hidden">
                      <div
                        className="h-full bg-orange-500"
                        style={{ width: `${selectedSignal.strength * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-white font-medium">{(selectedSignal.strength * 100).toFixed(0)}%</span>
                  </div>
                </div>
                <div className="space-y-2 border-b border-neutral-700 pb-3">
                  <p className="text-xs text-neutral-400">审查链路</p>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-xs">
                      <CheckCircle className="w-4 h-4 text-green-400" />
                      <span className="text-neutral-300">L1: {selectedSignal.l1}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      {selectedSignal.l2 === "通过" ? (
                        <CheckCircle className="w-4 h-4 text-green-400" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-400" />
                      )}
                      <span className="text-neutral-300">L2: {selectedSignal.l2}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-neutral-300">L3: {selectedSignal.l3}</span>
                    </div>
                  </div>
                </div>
                <div className="space-y-2 border-b border-neutral-700 pb-3">
                  <p className="text-xs text-neutral-400">推送目标</p>
                  <Badge className="bg-blue-900 text-blue-400 text-xs">模拟交易</Badge>
                </div>
                <Button className="w-full bg-orange-600 hover:bg-orange-700 text-white">
                  查看完整详情
                </Button>
              </>
            ) : (
              <div className="text-center py-8 text-neutral-500">
                <Eye className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">点击表格中的信号查看详情</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 信号流时间线 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-neutral-300">今日信号流时间线</CardTitle>
        </CardHeader>
        <CardContent className="pt-4">
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={timelineData}
                layout="vertical"
                margin={{ top: 10, right: 30, bottom: 10, left: 10 }}
                barSize={28}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#404040" horizontal={false} />
                <XAxis type="number" stroke="#737373" style={{ fontSize: "11px" }} tick={{ fill: "#a3a3a3" }} tickMargin={8} />
                <YAxis type="category" dataKey="stage" stroke="#737373" style={{ fontSize: "12px" }} tick={{ fill: "#d4d4d4" }} width={75} tickMargin={8} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1f2937",
                    border: "1px solid #404040",
                    borderRadius: "6px",
                    padding: "8px 12px",
                  }}
                  labelStyle={{ color: "#fff", marginBottom: "4px" }}
                  formatter={(value: number) => [`${value} 条`, "信号数"]}
                />
                <Bar dataKey="count" fill="#f97316" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 pt-3 border-t border-neutral-800 text-xs">
            <p className="text-neutral-400 flex flex-wrap items-center gap-1">
              <span className="text-orange-400 font-medium">128</span> 条信号生成
              <span className="text-neutral-600 mx-1">→</span>
              <span className="text-purple-400 font-medium">87%</span> 通过 L1
              <span className="text-neutral-600 mx-1">→</span>
              <span className="text-pink-400 font-medium">63%</span> 通过 L2
              <span className="text-neutral-600 mx-1">→</span>
              <span className="text-cyan-400 font-medium">9%</span> 进入 L3
              <span className="text-neutral-600 mx-1">→</span>
              <span className="text-green-400 font-medium">92</span> 条推送模拟
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
