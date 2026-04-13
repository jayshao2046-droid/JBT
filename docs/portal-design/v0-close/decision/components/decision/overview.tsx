"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  fetchStrategyOverview,
  fetchSignalOverview,
  fetchRuntimeOverview,
  type StrategyOverviewResponse,
  type SignalOverviewResponse,
  type ModelRuntimeOverview,
} from "@/lib/api"

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case "pass":
      return "bg-green-900/20 text-green-400 border-green-600/50"
    case "warning":
      return "bg-yellow-900/20 text-yellow-400 border-yellow-600/50"
    case "alert":
      return "bg-red-900/20 text-red-400 border-red-600/50"
    default:
      return "bg-neutral-900/20 text-neutral-400"
  }
}

const pipelineColors = ["#f97316", "#f59e0b", "#22c55e", "#3b82f6", "#8b5cf6", "#06b6d4", "#10b981"]

interface OverviewProps {
  refreshToken?: number
}

export default function DecisionOverview({ refreshToken }: OverviewProps) {
  const [strategyOv, setStrategyOv] = useState<StrategyOverviewResponse | null>(null)
  const [signalOv, setSignalOv] = useState<SignalOverviewResponse | null>(null)
  const [runtime, setRuntime] = useState<ModelRuntimeOverview | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      fetchStrategyOverview().catch(() => null),
      fetchSignalOverview().catch(() => null),
      fetchRuntimeOverview().catch(() => null),
    ]).then(([s, sig, rt]) => {
      setStrategyOv(s)
      setSignalOv(sig)
      setRuntime(rt)
    }).finally(() => setLoading(false))
  }, [refreshToken])

  const kpis = strategyOv?.kpis
  const sigKpis = signalOv?.kpis
  const pipelineData = strategyOv?.pipeline ?? []
  const blockerData = strategyOv?.blockers ?? []
  const pendingActions = (strategyOv?.pending_actions ?? []).slice(0, 5)
  const localModels = runtime?.local_models ?? []
  const onlineModels = runtime?.online_models ?? []
  const execGate = runtime?.execution_gate

  const signalTimeline = (signalOv?.timeline ?? []).map(item => ({
    time: item.generated_at ? new Date(item.generated_at).toLocaleTimeString("zh-CN", { hour12: false }) : "—",
    strategy: item.strategy_id,
    action: item.action,
    status: item.publish_workflow_status,
    summary: item.summary,
  }))

  return (
    <div className="p-6 space-y-6 bg-neutral-950 min-h-screen">
      {/* 策略 KPI */}
      <div>
        <p className="text-xs text-neutral-500 mb-3 uppercase tracking-wider">策略仓库</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "策略总数", value: kpis?.total ?? 0, color: "text-white" },
            { label: "可发布", value: kpis?.publish_ready ?? 0, color: "text-cyan-400" },
            { label: "已发布", value: kpis?.published ?? 0, color: "text-green-400" },
            { label: "待审批", value: kpis?.pending_approvals ?? 0, color: "text-orange-400" },
          ].map((kpi, idx) => (
            <Card key={idx} className="bg-neutral-900 border-neutral-700">
              <CardContent className="p-4">
                <p className="text-xs text-neutral-400 mb-2">{kpi.label}</p>
                <p className={`text-2xl font-bold ${kpi.color}`}>{kpi.value}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* 信号 KPI */}
      <div>
        <p className="text-xs text-neutral-500 mb-3 uppercase tracking-wider">信号审查</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "信号总数", value: sigKpis?.total ?? 0, color: "text-blue-400" },
            { label: "已通过", value: sigKpis?.approved ?? 0, color: "text-green-400" },
            { label: "待发布", value: sigKpis?.ready_for_publish ?? 0, color: "text-cyan-400" },
            { label: "实盘锁定可见", value: sigKpis?.locked_visible ?? 0, color: "text-purple-400" },
          ].map((kpi, idx) => (
            <Card key={idx} className="bg-neutral-900 border-neutral-700">
              <CardContent className="p-4">
                <p className="text-xs text-neutral-400 mb-2">{kpi.label}</p>
                <p className={`text-2xl font-bold ${kpi.color}`}>{kpi.value}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* 决策流水线 + 模型栈摘要 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 决策流水线 */}
        <Card className="bg-neutral-900 border-neutral-700 lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">策略生命周期流水线</CardTitle>
          </CardHeader>
          <CardContent>
            {pipelineData.length === 0 ? (
              <p className="text-sm text-neutral-500 text-center py-8">暂无策略数据</p>
            ) : (
              <div className="flex items-start justify-between gap-1 overflow-x-auto pb-2">
                {pipelineData.map((stage, idx) => (
                  <div key={stage.key} className="flex flex-col items-center flex-shrink-0 min-w-[64px]">
                    <div
                      className="w-14 h-14 rounded-lg flex items-center justify-center text-white font-bold text-sm mb-2"
                      style={{ backgroundColor: pipelineColors[idx % pipelineColors.length] }}
                    >
                      {stage.count}
                    </div>
                    <p className="text-[10px] text-neutral-400 text-center w-16 leading-tight">{stage.label}</p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* 模型栈摘要 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">模型栈</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {localModels.length === 0 && onlineModels.length === 0 ? (
              <p className="text-sm text-neutral-500 text-center py-4">暂无已配置模型</p>
            ) : (
              [...localModels, ...onlineModels].map((m, idx) => (
                <div key={idx} className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full shrink-0 ${m.status === "configured" || m.status === "running" ? "bg-green-400" : "bg-neutral-600"}`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white truncate">{m.model_name}</p>
                    <p className="text-xs text-neutral-500">{m.route_role}</p>
                  </div>
                  <Badge className="bg-neutral-800 text-neutral-300 text-[10px] shrink-0">{m.deployment_class}</Badge>
                </div>
              ))
            )}
            {execGate && (
              <div className="border-t border-neutral-700 pt-3 mt-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-neutral-400">执行目标</span>
                  <span className="text-xs text-orange-400 font-medium">{execGate.target}</span>
                </div>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-xs text-neutral-400">实盘</span>
                  <Badge className={execGate.live_trading_locked ? "bg-red-900 text-red-400" : "bg-green-900 text-green-400"} style={{ fontSize: "10px" }}>
                    {execGate.live_trading_locked ? "锁定" : "开放"}
                  </Badge>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 阻塞事项 + 信号时间线 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">阻塞事项</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {blockerData.length === 0 ? (
              <p className="text-sm text-green-400/70 text-center py-4">无阻塞</p>
            ) : (
              blockerData.map((item, idx) => (
                <div key={idx} className={`border rounded p-3 ${getSeverityColor(item.severity)}`}>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{item.label}</span>
                    <Badge className="bg-opacity-20">{item.count}</Badge>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">最近信号时间线</CardTitle>
          </CardHeader>
          <CardContent>
            {signalTimeline.length === 0 ? (
              <p className="text-sm text-neutral-500 text-center py-4">暂无信号记录</p>
            ) : (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {signalTimeline.map((item, idx) => (
                  <div key={idx} className="flex items-start gap-3 border-b border-neutral-800 pb-2">
                    <span className="text-xs text-neutral-500 w-16 shrink-0 font-mono">{item.time}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-white truncate">{item.strategy}</p>
                      <p className="text-xs text-neutral-400 mt-0.5 truncate">{item.summary}</p>
                    </div>
                    <Badge className={item.action === "approve" ? "bg-green-900 text-green-400" : "bg-yellow-900 text-yellow-400"}>
                      {item.action}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 待处理动作 */}
      {pendingActions.length > 0 && (
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">待处理动作 ({pendingActions.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {pendingActions.map((action, idx) => (
                <div key={idx} className="border border-neutral-700 rounded p-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">{action.strategy_name}</p>
                      <p className="text-xs text-neutral-400 mt-1">{action.detail}</p>
                    </div>
                    <Badge className={
                      action.type === "ready" ? "bg-green-900 text-green-400"
                      : action.type === "approval" ? "bg-yellow-900 text-yellow-400"
                      : "bg-red-900 text-red-400"
                    }>
                      {action.type === "ready" ? "可发布" : action.type === "approval" ? "待审批" : "阻塞"}
                    </Badge>
                  </div>
                  <p className="text-xs text-neutral-500 mt-2">{action.lifecycle_status} · {action.updated_at?.slice(0, 10) ?? "—"}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 研究就绪度 */}
      {strategyOv?.research_readiness && (
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">研究就绪度概览</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
              {[
                { label: "研究通过", value: strategyOv.research_readiness.research_ready, color: "text-green-400" },
                { label: "研究缺失", value: strategyOv.research_readiness.research_missing, color: "text-red-400" },
                { label: "回测通过", value: strategyOv.research_readiness.backtest_ready, color: "text-green-400" },
                { label: "回测缺失", value: strategyOv.research_readiness.backtest_missing, color: "text-red-400" },
                { label: "因子对齐", value: strategyOv.research_readiness.factor_aligned, color: "text-green-400" },
                { label: "因子失配", value: strategyOv.research_readiness.factor_mismatch, color: "text-yellow-400" },
                { label: "实盘锁定", value: strategyOv.research_readiness.live_locked, color: "text-blue-400" },
              ].map((item, idx) => (
                <div key={idx} className="text-center p-3 bg-neutral-800 rounded-lg">
                  <p className={`text-lg font-bold ${item.color}`}>{item.value}</p>
                  <p className="text-[10px] text-neutral-400 mt-1">{item.label}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
