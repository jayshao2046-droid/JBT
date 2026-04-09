"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Eye, CheckCircle, XCircle, Loader2 } from "lucide-react"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts"
import { fetchSignalOverview, submitApproval, completeApproval, fetchApprovals, type SignalOverviewResponse, type DecisionRecord, type ApprovalRecord } from "@/lib/api"

interface SignalRow {
  id: string
  time: string
  strategy: string
  symbol: string
  action: string
  strength: number
  factors: number
  eligibility: string
  layer: string
  publishStatus: string
  reasoning: string
}

function mapSignalRow(rec: DecisionRecord): SignalRow {
  const timeStr = rec.generated_at ? new Date(rec.generated_at).toLocaleTimeString("zh-CN", { hour12: false }) : "—"
  return {
    id: rec.decision_id,
    time: timeStr,
    strategy: rec.strategy_id,
    symbol: rec.symbol ?? "—",
    action: rec.action,
    strength: rec.confidence ?? 0,
    factors: rec.factor_count ?? 0,
    eligibility: rec.eligibility_status,
    layer: rec.layer,
    publishStatus: rec.publish_workflow_status,
    reasoning: rec.reasoning_summary,
  }
}

const getStatusBadgeColor = (status: string) => {
  switch (status) {
    case "ready_for_publish":
      return "bg-green-900 text-green-400"
    case "locked_visible":
      return "bg-blue-900 text-blue-400"
    case "none":
      return "bg-neutral-700 text-neutral-300"
    default:
      return "bg-yellow-900 text-yellow-400"
  }
}

const getActionBadgeColor = (action: string) => {
  switch (action) {
    case "approve":
      return "bg-green-900 text-green-400"
    case "hold":
      return "bg-yellow-900 text-yellow-400"
    default:
      return "bg-neutral-700 text-neutral-300"
  }
}

interface SignalReviewProps {
  refreshToken?: number
}

export default function SignalReview({ refreshToken }: SignalReviewProps) {
  const [overview, setOverview] = useState<SignalOverviewResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedSignal, setSelectedSignal] = useState<SignalRow | null>(null)
  const [approving, setApproving] = useState(false)
  const [approvalResult, setApprovalResult] = useState<{ ok: boolean; msg: string } | null>(null)
  const [approvals, setApprovals] = useState<ApprovalRecord[]>([])

  const reload = () => {
    setLoading(true)
    Promise.all([
      fetchSignalOverview().catch(() => null),
      fetchApprovals().catch(() => []),
    ]).then(([ov, appr]) => {
      if (ov) setOverview(ov)
      setApprovals(appr ?? [])
    }).finally(() => setLoading(false))
  }

  useEffect(() => { reload() }, [refreshToken])

  /* 提交审批 → 立即完成（approve / reject） */
  const handleApproval = async (signal: SignalRow, result: "approve" | "reject") => {
    setApproving(true)
    setApprovalResult(null)
    try {
      // 1. 提交审批请求
      const approval = await submitApproval({
        strategy_id: signal.strategy,
        target: "sim-trading",
        requester: "dashboard-user",
        notes: `${result === "approve" ? "通过" : "拒绝"}信号 ${signal.id}`,
      })
      // 2. 立即完成审批
      await completeApproval(approval.approval_id, { result, notes: `via dashboard` })
      setApprovalResult({ ok: true, msg: result === "approve" ? "✓ 已通过" : "✕ 已拒绝" })
      reload()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "审批失败"
      setApprovalResult({ ok: false, msg })
    } finally {
      setApproving(false)
    }
  }

  const kpis = overview?.kpis
  const signalTableData = (overview?.recent_signals ?? []).map(mapSignalRow)
  const stageCounts = overview?.stage_counts ?? []

  const kpiData = [
    { label: "信号总数", value: String(kpis?.total ?? 0), color: "text-blue-400" },
    { label: "已通过", value: String(kpis?.approved ?? 0), color: "text-green-400" },
    { label: "持有观望", value: String(kpis?.hold ?? 0), color: "text-yellow-400" },
    { label: "已阻塞", value: String(kpis?.blocked ?? 0), color: "text-red-400" },
    { label: "待发布", value: String(kpis?.ready_for_publish ?? 0), color: "text-cyan-400" },
    { label: "实盘锁定可见", value: String(kpis?.locked_visible ?? 0), color: "text-purple-400" },
  ]

  return (
    <div className="p-6 space-y-6 bg-neutral-950 min-h-screen">
      {/* KPI 卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
        {kpiData.map((kpi, idx) => (
          <Card key={idx} className="bg-neutral-900 border-neutral-700">
            <CardContent className="p-3">
              <p className="text-xs text-neutral-400 mb-1">{kpi.label}</p>
              <p className={`text-xl font-bold ${kpi.color}`}>{kpi.value}</p>
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
            {signalTableData.length === 0 ? (
              <p className="text-sm text-neutral-500 text-center py-8">暂无信号记录</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-neutral-700">
                      <th className="text-left py-2 px-2 text-neutral-400 font-medium">时间</th>
                      <th className="text-left py-2 px-2 text-neutral-400 font-medium">策略</th>
                      <th className="text-left py-2 px-2 text-neutral-400 font-medium">标的</th>
                      <th className="text-center py-2 px-2 text-neutral-400 font-medium">动作</th>
                      <th className="text-center py-2 px-2 text-neutral-400 font-medium">强度</th>
                      <th className="text-center py-2 px-2 text-neutral-400 font-medium">因子数</th>
                      <th className="text-center py-2 px-2 text-neutral-400 font-medium">层级</th>
                      <th className="text-center py-2 px-2 text-neutral-400 font-medium">资格</th>
                      <th className="text-left py-2 px-2 text-neutral-400 font-medium">发布状态</th>
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
                          <Badge className={getActionBadgeColor(signal.action)}>{signal.action}</Badge>
                        </td>
                        <td className="py-2 px-2 text-center text-orange-400 font-medium">{(signal.strength * 100).toFixed(0)}%</td>
                        <td className="py-2 px-2 text-center text-neutral-400">{signal.factors}</td>
                        <td className="py-2 px-2 text-center text-neutral-300">{signal.layer}</td>
                        <td className="py-2 px-2 text-center">
                          <Badge className={signal.eligibility === "eligible" ? "bg-green-900 text-green-400" : signal.eligibility === "blocked" ? "bg-red-900 text-red-400" : "bg-yellow-900 text-yellow-400"}>
                            {signal.eligibility}
                          </Badge>
                        </td>
                        <td className="py-2 px-2">
                          <Badge className={getStatusBadgeColor(signal.publishStatus)}>{signal.publishStatus}</Badge>
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
            )}
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
                  <p className="text-xs text-neutral-400">标的 / 动作</p>
                  <p className="text-white font-medium">
                    {selectedSignal.symbol} / {selectedSignal.action}
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

                {/* 决策层级流 — 展示信号经过的模型审查路径 */}
                <div className="space-y-2 border-b border-neutral-700 pb-3">
                  <p className="text-xs text-neutral-400">决策路径</p>
                  <div className="flex items-center gap-1 text-[10px]">
                    {["L1 门禁", "L2 主审", "L3 在线"].map((layer, idx) => {
                      const isActive = selectedSignal.layer === `L${idx + 1}` || (
                        idx === 0 && ["L2", "L3"].includes(selectedSignal.layer)
                      ) || (idx === 1 && selectedSignal.layer === "L3")
                      const isCurrent = selectedSignal.layer === `L${idx + 1}`
                      return (
                        <div key={layer} className="flex items-center gap-1">
                          <span className={`px-2 py-0.5 rounded ${isCurrent ? "bg-orange-500 text-white font-bold" : isActive ? "bg-green-900 text-green-400" : "bg-neutral-800 text-neutral-500"}`}>
                            {layer}
                          </span>
                          {idx < 2 && <span className="text-neutral-600">→</span>}
                        </div>
                      )
                    })}
                  </div>
                  <p className="text-[10px] text-neutral-500 mt-1">
                    {selectedSignal.layer === "L1" && "门禁层：Qwen2.5 快速 gate/deny 二分过滤"}
                    {selectedSignal.layer === "L2" && "主审层：Qwen3 14B 深度因子评估 + 置信度打分"}
                    {selectedSignal.layer === "L3" && "在线确认层：外部大模型二次确认（高风险信号）"}
                  </p>
                </div>

                <div className="space-y-2 border-b border-neutral-700 pb-3">
                  <p className="text-xs text-neutral-400">资格状态</p>
                  <Badge className={selectedSignal.eligibility === "eligible" ? "bg-green-900 text-green-400" : "bg-red-900 text-red-400"}>
                    {selectedSignal.eligibility}
                  </Badge>
                </div>
                <div className="space-y-2 border-b border-neutral-700 pb-3">
                  <p className="text-xs text-neutral-400">推理摘要</p>
                  <p className="text-xs text-neutral-300 leading-relaxed">{selectedSignal.reasoning}</p>
                </div>
                <div className="space-y-2">
                  <p className="text-xs text-neutral-400">发布状态</p>
                  <Badge className={getStatusBadgeColor(selectedSignal.publishStatus)}>{selectedSignal.publishStatus}</Badge>
                </div>

                {/* 审批操作按钮 */}
                <div className="border-t border-neutral-700 pt-3 space-y-2">
                  <p className="text-xs text-neutral-400">审批操作</p>
                  <div className="grid grid-cols-2 gap-2">
                    <Button
                      size="sm"
                      className="bg-green-700 hover:bg-green-600 text-white text-xs h-8"
                      disabled={approving}
                      onClick={() => handleApproval(selectedSignal, "approve")}
                    >
                      {approving ? <Loader2 className="w-3 h-3 animate-spin" /> : <><CheckCircle className="w-3 h-3 mr-1" />通过</>}
                    </Button>
                    <Button
                      size="sm"
                      className="bg-red-700 hover:bg-red-600 text-white text-xs h-8"
                      disabled={approving}
                      onClick={() => handleApproval(selectedSignal, "reject")}
                    >
                      {approving ? <Loader2 className="w-3 h-3 animate-spin" /> : <><XCircle className="w-3 h-3 mr-1" />拒绝</>}
                    </Button>
                  </div>
                  {approvalResult && (
                    <p className={`text-xs text-center ${approvalResult.ok ? "text-green-400" : "text-red-400"}`}>
                      {approvalResult.msg}
                    </p>
                  )}
                </div>
              </>
            ) : (
              <div className="text-center py-8 text-neutral-500">
                <Eye className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">点击表格中的信号查看详情</p>
                <p className="text-xs text-neutral-600 mt-2">包含决策路径、模型审查层级</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 阶段统计 */}
      {stageCounts.length > 0 && (
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-neutral-300">信号阶段分布</CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={stageCounts}
                  layout="vertical"
                  margin={{ top: 10, right: 30, bottom: 10, left: 10 }}
                  barSize={28}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#404040" horizontal={false} />
                  <XAxis type="number" stroke="#737373" style={{ fontSize: "11px" }} tick={{ fill: "#a3a3a3" }} tickMargin={8} />
                  <YAxis type="category" dataKey="label" stroke="#737373" style={{ fontSize: "12px" }} tick={{ fill: "#d4d4d4" }} width={100} tickMargin={8} />
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
          </CardContent>
        </Card>
      )}

      {/* 待处理审批 */}
      {approvals.length > 0 && (
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-neutral-300">审批记录 ({approvals.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {approvals.slice(0, 20).map((a, idx) => (
                <div key={idx} className="flex items-center gap-3 border border-neutral-700 rounded p-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-white truncate">{a.strategy_id} → {a.target}</p>
                    <p className="text-[10px] text-neutral-500">{a.submitted_at?.slice(0, 19)} · {a.requester}</p>
                  </div>
                  <Badge className={
                    a.approval_status === "completed" && a.result === "approve" ? "bg-green-900 text-green-400"
                    : a.approval_status === "completed" && a.result === "reject" ? "bg-red-900 text-red-400"
                    : "bg-yellow-900 text-yellow-400"
                  }>
                    {a.approval_status === "completed" ? (a.result === "approve" ? "已通过" : "已拒绝") : "待处理"}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
