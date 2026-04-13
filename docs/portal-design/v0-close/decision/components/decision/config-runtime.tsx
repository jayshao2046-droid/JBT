"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { fetchModelStatus, fetchRuntimeOverview, type ModelStatus, type ModelRuntimeOverview } from "@/lib/api"

const getStatusBadgeColor = (status: string) => {
  switch (status) {
    case "pass":
      return "bg-green-900 text-green-400"
    case "warning":
      return "bg-yellow-900 text-yellow-400"
    case "alert":
      return "bg-red-900 text-red-400"
    default:
      return "bg-neutral-700 text-neutral-300"
  }
}

const getModelStatusColor = (status: string) => {
  switch (status) {
    case "running":
    case "active":
      return "bg-green-900 text-green-400"
    case "ready":
      return "bg-blue-900 text-blue-400"
    case "default":
      return "bg-orange-900 text-orange-400"
    case "upgrade":
      return "bg-purple-900 text-purple-400"
    case "standby":
      return "bg-yellow-900 text-yellow-400"
    default:
      return "bg-neutral-700 text-neutral-300"
  }
}

export default function ConfigRuntime({ refreshToken }: { refreshToken?: number }) {
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null)
  const [runtime, setRuntime] = useState<ModelRuntimeOverview | null>(null)

  useEffect(() => {
    fetchModelStatus().then(setModelStatus).catch(() => {})
    fetchRuntimeOverview().then(setRuntime).catch(() => {})
  }, [refreshToken])

  const localModels = runtime?.local_models ?? []
  const onlineModels = runtime?.online_models ?? []
  const execGate = runtime?.execution_gate
  const modelRouter = runtime?.model_router
  const researchWindow = runtime?.research_window
  const integrations = runtime?.service_integrations ?? []

  const kpiData = [
    { label: "执行门禁状态", value: modelStatus ? (modelStatus.execution_gate_enabled ? "启用" : "关闭") : "—", status: modelStatus?.execution_gate_enabled ? "pass" : "warning", color: "orange" },
    { label: "实盘门禁", value: modelStatus ? (modelStatus.live_trading_gate_locked ? "锁定" : "开放") : "—", status: modelStatus?.live_trading_gate_locked ? "pass" : "alert", color: "red" },
    { label: "回测证书要求", value: modelStatus ? (modelStatus.model_router_require_backtest_cert ? "强制" : "宽松") : "—", status: "pass", color: "blue" },
    { label: "研究快照要求", value: modelStatus ? (modelStatus.model_router_require_research_snapshot ? "强制" : "宽松") : "—", status: "pass", color: "blue" },
    { label: "执行目标", value: modelStatus?.execution_gate_target ?? "—", status: "pass", color: "green" },
    { label: "运行时健康", value: runtime?.runtime_status?.health ?? "—", status: runtime?.runtime_status?.health === "healthy" ? "pass" : "warning", color: "green" },
  ]

  return (
    <div className="p-6 space-y-6 bg-neutral-950 min-h-screen">
      {/* KPI 卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {kpiData.map((kpi, idx) => (
          <Card key={idx} className="bg-neutral-900 border-neutral-700">
            <CardContent className="p-3">
              <p className="text-xs text-neutral-400 mb-1 truncate">{kpi.label}</p>
              <div className="flex items-end justify-between">
                <p className={`text-sm font-bold ${kpi.color === "green" ? "text-green-400" : kpi.color === "blue" ? "text-blue-400" : kpi.color === "red" ? "text-red-400" : "text-orange-400"}`}>
                  {kpi.value}
                </p>
                <Badge className={getStatusBadgeColor(kpi.status)} style={{ height: "18px", fontSize: "10px" }}>
                  ✓
                </Badge>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 执行门禁摘要 */}
      {execGate && (
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">执行门禁</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="border border-neutral-700 rounded p-3">
                <p className="text-xs text-neutral-400 mb-1">启用状态</p>
                <Badge className={execGate.enabled ? "bg-green-900 text-green-400" : "bg-neutral-700 text-neutral-300"}>
                  {execGate.enabled ? "启用" : "关闭"}
                </Badge>
              </div>
              <div className="border border-neutral-700 rounded p-3">
                <p className="text-xs text-neutral-400 mb-1">执行目标</p>
                <p className="text-sm font-medium text-white">{execGate.target}</p>
              </div>
              <div className="border border-neutral-700 rounded p-3">
                <p className="text-xs text-neutral-400 mb-1">实盘锁定</p>
                <Badge className={execGate.live_trading_locked ? "bg-red-900 text-red-400" : "bg-green-900 text-green-400"}>
                  {execGate.live_trading_locked ? "锁定" : "开放"}
                </Badge>
              </div>
              <div className="border border-neutral-700 rounded p-3">
                <p className="text-xs text-neutral-400 mb-1">摘要</p>
                <p className="text-xs text-neutral-200">{execGate.summary}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 本地模型 + 在线模型 — 简要列表 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">本地模型 ({localModels.length})</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {localModels.length > 0 ? localModels.map((m, idx) => (
              <div key={idx} className="flex items-center gap-3 border border-neutral-700 rounded p-2">
                <div className={`w-2 h-2 rounded-full shrink-0 ${m.status === "configured" || m.status === "running" ? "bg-green-400" : "bg-neutral-600"}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white truncate">{m.model_name}</p>
                  <p className="text-xs text-neutral-500">{m.route_role}</p>
                </div>
                <Badge className={getModelStatusColor(m.status)} style={{ fontSize: "10px" }}>{m.status}</Badge>
              </div>
            )) : (
              <p className="text-sm text-neutral-500 text-center py-4">暂无本地模型</p>
            )}
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">在线模型 ({onlineModels.length})</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {onlineModels.length > 0 ? onlineModels.map((m, idx) => (
              <div key={idx} className="flex items-center gap-3 border border-neutral-700 rounded p-2">
                <div className={`w-2 h-2 rounded-full shrink-0 ${m.status === "configured" || m.status === "running" ? "bg-green-400" : "bg-neutral-600"}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white truncate">{m.model_name}</p>
                  <p className="text-xs text-neutral-500">{m.route_role}</p>
                </div>
                <Badge className={getModelStatusColor(m.status)} style={{ fontSize: "10px" }}>{m.status}</Badge>
              </div>
            )) : (
              <p className="text-sm text-neutral-500 text-center py-4">暂无在线模型</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 模型路由 + 研究窗口 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {modelRouter && (
          <Card className="bg-neutral-900 border-neutral-700">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-neutral-300">模型路由</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-neutral-400">回测证书要求</span>
                <Badge className={modelRouter.require_backtest_cert ? "bg-green-900 text-green-400" : "bg-neutral-700 text-neutral-300"}>
                  {modelRouter.require_backtest_cert ? "强制" : "宽松"}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-neutral-400">研究快照要求</span>
                <Badge className={modelRouter.require_research_snapshot ? "bg-green-900 text-green-400" : "bg-neutral-700 text-neutral-300"}>
                  {modelRouter.require_research_snapshot ? "强制" : "宽松"}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-neutral-400">合格策略</span>
                <span className="text-green-400 font-bold">{modelRouter.eligible_strategies}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-neutral-400">阻塞策略</span>
                <span className="text-red-400 font-bold">{modelRouter.blocked_strategies}</span>
              </div>
            </CardContent>
          </Card>
        )}

        {researchWindow && (
          <Card className="bg-neutral-900 border-neutral-700">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-neutral-300">研究窗口</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-neutral-400">窗口时间</span>
                <span className="text-neutral-200 text-sm">{researchWindow.start} ~ {researchWindow.end}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-neutral-400">时区</span>
                <span className="text-neutral-200 text-sm">{researchWindow.timezone}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-neutral-400">当前状态</span>
                <Badge className={researchWindow.is_open ? "bg-green-900 text-green-400" : "bg-red-900 text-red-400"}>
                  {researchWindow.is_open ? "开放中" : "已关闭"}
                </Badge>
              </div>
              <p className="text-xs text-neutral-500">{researchWindow.rule}</p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* 服务集成 */}
      {integrations.length > 0 && (
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">服务集成</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {integrations.map((svc, idx) => (
                <div key={idx} className="border border-neutral-700 rounded p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-white">{svc.name}</span>
                    <Badge className={svc.status === "configured" ? "bg-green-900 text-green-400" : "bg-neutral-700 text-neutral-300"}>
                      {svc.status}
                    </Badge>
                  </div>
                  <p className="text-xs text-neutral-400">{svc.note}</p>
                  {svc.timeout_seconds && (
                    <p className="text-xs text-neutral-500 mt-1">超时：{svc.timeout_seconds}s</p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 运行时状态摘要 */}
      {runtime?.runtime_status && (
        <Card className="bg-neutral-900 border-green-600/50">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-green-400">运行时状态摘要</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-xs text-green-300/80">
            <p>✓ 状态存储：{runtime.runtime_status.state_store_exists ? "已加载" : "未找到"} ({runtime.runtime_status.state_store_path})</p>
            <p>✓ 策略总数：{runtime.runtime_status.strategies_total}</p>
            <p>✓ 审批总数：{runtime.runtime_status.approvals_total}</p>
            <p>✓ 回测证书：{runtime.runtime_status.backtest_certs_total}</p>
            <p>✓ 研究快照：{runtime.runtime_status.research_snapshots_total}</p>
            <p>✓ 决策记录：{runtime.runtime_status.decision_records_total}</p>
            <p>✓ 派发器：{runtime.runtime_status.dispatcher_state}</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
