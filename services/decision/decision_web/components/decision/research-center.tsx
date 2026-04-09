"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { fetchStrategyOverview, fetchRuntimeOverview, type StrategyOverviewResponse, type ModelRuntimeOverview } from "@/lib/api"

export default function ResearchCenter({ refreshToken }: { refreshToken?: number }) {
  const [strategyOv, setStrategyOv] = useState<StrategyOverviewResponse | null>(null)
  const [runtime, setRuntime] = useState<ModelRuntimeOverview | null>(null)

  useEffect(() => {
    fetchStrategyOverview().then(setStrategyOv).catch(() => {})
    fetchRuntimeOverview().then(setRuntime).catch(() => {})
  }, [refreshToken])

  const rr = strategyOv?.research_readiness
  const rw = runtime?.research_window

  const kpiData = rr
    ? [
        { label: "研究就绪", value: String(rr.research_ready), status: rr.research_ready > 0 ? "pass" : "neutral" },
        { label: "研究缺失", value: String(rr.research_missing), status: rr.research_missing > 0 ? "warning" : "pass" },
        { label: "回测就绪", value: String(rr.backtest_ready), status: rr.backtest_ready > 0 ? "pass" : "neutral" },
        { label: "回测缺失", value: String(rr.backtest_missing), status: rr.backtest_missing > 0 ? "warning" : "pass" },
        { label: "因子对齐", value: String(rr.factor_aligned), status: "pass" },
        { label: "因子失配", value: String(rr.factor_mismatch), status: rr.factor_mismatch > 0 ? "alert" : "pass" },
      ]
    : []

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case "pass": return "bg-green-900 text-green-400"
      case "warning": return "bg-yellow-900 text-yellow-400"
      case "alert": return "bg-red-900 text-red-400"
      default: return "bg-neutral-700 text-neutral-300"
    }
  }

  return (
    <div className="p-6 space-y-6 bg-neutral-950 min-h-screen">
      {/* KPI 卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {kpiData.map((kpi, idx) => (
          <Card key={idx} className="bg-neutral-900 border-neutral-700">
            <CardContent className="p-3">
              <p className="text-xs text-neutral-400 mb-1">{kpi.label}</p>
              <div className="flex items-end justify-between">
                <p className="text-lg font-bold text-white">{kpi.value}</p>
                <Badge className={getStatusBadgeColor(kpi.status)} style={{ height: "20px" }}>
                  {kpi.status === "pass" ? "✓" : kpi.status === "warning" ? "⚠" : "!"}
                </Badge>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 研究窗口 + 生命周期管道 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 研究窗口 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">研究调度窗口</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {rw ? (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <div className="border border-neutral-700 rounded p-3">
                    <p className="text-xs text-neutral-400 mb-1">窗口时间</p>
                    <p className="text-sm font-medium text-white">{rw.start} ~ {rw.end}</p>
                    <p className="text-xs text-neutral-500 mt-1">{rw.timezone}</p>
                  </div>
                  <div className="border border-neutral-700 rounded p-3">
                    <p className="text-xs text-neutral-400 mb-1">当前状态</p>
                    <Badge className={rw.is_open ? "bg-green-900 text-green-400" : "bg-red-900 text-red-400"}>
                      {rw.is_open ? "研究窗口开放" : "研究窗口关闭"}
                    </Badge>
                    <p className="text-xs text-neutral-500 mt-1">当前 {rw.current_time}</p>
                  </div>
                </div>
                <div className="p-3 bg-orange-900/20 border border-orange-600/50 rounded">
                  <p className="text-xs text-orange-300 font-medium">⏰ 调度规则</p>
                  <p className="text-xs text-orange-400/70 mt-1">{rw.rule}</p>
                </div>
              </>
            ) : (
              <p className="text-sm text-neutral-500 text-center py-8">加载中…</p>
            )}
          </CardContent>
        </Card>

        {/* 策略生命周期管道 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">策略生命周期管道</CardTitle>
          </CardHeader>
          <CardContent>
            {strategyOv?.pipeline && strategyOv.pipeline.length > 0 ? (
              <div className="space-y-2">
                {strategyOv.pipeline.map((stage, idx) => {
                  const stageDesc: Record<string, string> = {
                    imported: "已导入，待编辑",
                    draft: "草稿编辑中",
                    backtesting: "回测验证中",
                    confirmed: "已确认，待审批",
                    pending_execution: "待执行推送",
                    sim_running: "模拟盘运行中",
                    live_running: "实盘运行中",
                    retired: "已退役",
                  }
                  return (
                    <div key={idx} className="flex items-center gap-3">
                      <div className="w-24 text-xs text-neutral-400 text-right">{stage.label}</div>
                      <div className="flex-1 h-6 bg-neutral-800 rounded overflow-hidden relative">
                        <div
                          className="h-full bg-orange-500 rounded flex items-center justify-center text-xs text-white font-bold"
                          style={{ width: `${strategyOv.kpis.total > 0 ? Math.max((stage.count / strategyOv.kpis.total) * 100, 8) : 0}%` }}
                        >
                          {stage.count}
                        </div>
                      </div>
                      <div className="w-28 text-[10px] text-neutral-500 truncate">{stageDesc[stage.key] ?? ""}</div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <p className="text-sm text-neutral-500 text-center py-8">暂无策略数据</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 阻塞项 + 待处理动作 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 阻塞项 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">研究阻塞项</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {strategyOv?.blockers && strategyOv.blockers.length > 0 ? (
              strategyOv.blockers.map((b, idx) => (
                <div key={idx} className={`border rounded p-2 ${b.severity === "error" ? "border-red-600/50 bg-red-900/20" : "border-yellow-600/50 bg-yellow-900/20"}`}>
                  <div className="flex items-center justify-between">
                    <p className={`text-xs font-medium ${b.severity === "error" ? "text-red-400" : "text-yellow-400"}`}>{b.label}</p>
                    <Badge className={b.severity === "error" ? "bg-red-900 text-red-400" : "bg-yellow-900 text-yellow-400"}>
                      {b.count}
                    </Badge>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-neutral-500 text-center py-4">无阻塞项</p>
            )}
          </CardContent>
        </Card>

        {/* 待处理动作 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">研究待处理</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 max-h-80 overflow-y-auto">
            {strategyOv?.pending_actions && strategyOv.pending_actions.length > 0 ? (
              strategyOv.pending_actions.map((pa, idx) => (
                <div key={idx} className="border border-neutral-700 rounded p-3">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="text-sm font-medium text-white">{pa.strategy_name}</p>
                      <p className="text-xs text-neutral-400 mt-1">{pa.detail}</p>
                    </div>
                    <Badge className="bg-orange-900 text-orange-400">{pa.type}</Badge>
                  </div>
                  <p className="text-xs text-neutral-500 mt-2">{pa.updated_at}</p>
                </div>
              ))
            ) : (
              <p className="text-sm text-neutral-500 text-center py-4">无待处理动作</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 因子同步摘要 */}
      {runtime?.factor_sync && (
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">因子同步摘要</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-4 bg-green-900/20 border border-green-600/30 rounded-lg">
                <p className="text-2xl font-bold text-green-400">{runtime.factor_sync.aligned}</p>
                <p className="text-xs text-neutral-400 mt-1">已对齐</p>
              </div>
              <div className="text-center p-4 bg-yellow-900/20 border border-yellow-600/30 rounded-lg">
                <p className="text-2xl font-bold text-yellow-400">{runtime.factor_sync.mismatch}</p>
                <p className="text-xs text-neutral-400 mt-1">失配</p>
              </div>
              <div className="text-center p-4 bg-neutral-800 border border-neutral-700 rounded-lg">
                <p className="text-2xl font-bold text-neutral-400">{runtime.factor_sync.unknown}</p>
                <p className="text-xs text-neutral-400 mt-1">未知</p>
              </div>
            </div>
            <p className="text-xs text-neutral-500 mt-3">{runtime.factor_sync.note}</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
