"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { AlertTriangle } from "lucide-react"
import { fetchModelStatus, type ModelStatus } from "@/lib/api"

const getHeatmapColor = (value: number) => {
  if (value >= 0.9) return "bg-green-800 text-green-300"
  if (value >= 0.8) return "bg-cyan-800 text-cyan-300"
  if (value >= 0.7) return "bg-yellow-800 text-yellow-300"
  return "bg-red-800 text-red-300"
}

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
      return "bg-green-900 text-green-400"
    case "ready":
      return "bg-blue-900 text-blue-400"
    case "standby":
      return "bg-yellow-900 text-yellow-400"
    case "disabled":
      return "bg-neutral-800 text-neutral-500"
    default:
      return "bg-neutral-700 text-neutral-300"
  }
}

export default function ModelsFactors() {
  const [activeTab, setActiveTab] = useState("validity")
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null)

  useEffect(() => {
    fetchModelStatus()
      .then(setModelStatus)
      .catch(() => {})
  }, [])

  const kpiData = [
    { label: "执行门禁状态", value: modelStatus ? (modelStatus.execution_gate_enabled ? "启用" : "关闭") : "—", status: modelStatus?.execution_gate_enabled ? "pass" : "warning", color: "green" },
    { label: "实盘门禁", value: modelStatus ? (modelStatus.live_trading_gate_locked ? "锁定" : "开放") : "—", status: modelStatus?.live_trading_gate_locked ? "pass" : "alert", color: "blue" },
    { label: "回测证书要求", value: modelStatus ? (modelStatus.model_router_require_backtest_cert ? "强制" : "宽松") : "—", status: "pass", color: "orange" },
    { label: "研究快照要求", value: modelStatus ? (modelStatus.model_router_require_research_snapshot ? "强制" : "宽松") : "—", status: "pass", color: "purple" },
    { label: "执行目标", value: modelStatus?.execution_gate_target ?? "—", status: "pass", color: "yellow" },
    { label: "因子数据", value: "—", status: "pass", color: "red" },
  ]

  const factorValidityData: { name: string; validity: number; stability: number; recent: number }[] = []
  const factorSyncData: { name: string; synced: number; expired: number; missing: number; waiting: number }[] = []
  const models: { name: string; type: string; status: string; latency: string; accuracy: number; capacity: string }[] = []

  return (
    <div className="p-6 space-y-6 bg-neutral-950 min-h-screen">
      {/* KPI 卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
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

      {/* 因子热力图 + 排行榜 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 因子热力图 */}
        <Card className="bg-neutral-900 border-neutral-700 lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-neutral-300">因子热力图</CardTitle>
              <Tabs value={activeTab} onValueChange={setActiveTab} className="w-auto">
                <TabsList className="bg-neutral-800 border border-neutral-700 h-8">
                  <TabsTrigger value="validity" className="text-xs data-[state=active]:bg-orange-500 data-[state=active]:text-white data-[state=inactive]:text-neutral-400 h-7 px-3">因子有效性</TabsTrigger>
                  <TabsTrigger value="sync" className="text-xs data-[state=active]:bg-orange-500 data-[state=active]:text-white data-[state=inactive]:text-neutral-400 h-7 px-3">同步状态</TabsTrigger>
                </TabsList>
              </Tabs>
            </div>
          </CardHeader>
          <CardContent>
            {activeTab === "validity" && (
              <div className="space-y-3">
                <div className="flex gap-2 mb-4 pb-2 border-b border-neutral-800">
                  <div className="w-20"></div>
                  <div className="w-20 text-center text-xs text-neutral-400 font-medium">贡献度</div>
                  <div className="w-20 text-center text-xs text-neutral-400 font-medium">稳定性</div>
                  <div className="w-20 text-center text-xs text-neutral-400 font-medium">近阶段</div>
                </div>
                <div className="space-y-2 max-h-80 overflow-y-auto pr-2">
                  {factorValidityData.map((factor, idx) => (
                    <div key={idx} className="flex items-center gap-2 py-1 hover:bg-neutral-800/50 rounded px-1 transition-colors">
                      <div className="w-20 text-sm font-mono text-neutral-300">{factor.name}</div>
                      <div className={`w-20 h-8 flex items-center justify-center text-xs font-medium rounded-md ${getHeatmapColor(factor.validity)}`}>
                        {(factor.validity * 100).toFixed(0)}%
                      </div>
                      <div className={`w-20 h-8 flex items-center justify-center text-xs font-medium rounded-md ${getHeatmapColor(factor.stability)}`}>
                        {(factor.stability * 100).toFixed(0)}%
                      </div>
                      <div className={`w-20 h-8 flex items-center justify-center text-xs font-medium rounded-md ${getHeatmapColor(factor.recent)}`}>
                        {(factor.recent * 100).toFixed(0)}%
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {activeTab === "sync" && (
              <div className="space-y-3">
                <div className="flex gap-2 mb-4 pb-2 border-b border-neutral-800">
                  <div className="w-20"></div>
                  <div className="w-20 text-center text-xs text-neutral-400 font-medium">已同步</div>
                  <div className="w-20 text-center text-xs text-neutral-400 font-medium">已过期</div>
                  <div className="w-20 text-center text-xs text-neutral-400 font-medium">缺失回测</div>
                  <div className="w-20 text-center text-xs text-neutral-400 font-medium">待同步</div>
                </div>
                <div className="space-y-2 max-h-80 overflow-y-auto pr-2">
                  {factorSyncData.map((factor, idx) => (
                    <div key={idx} className="flex items-center gap-2 py-1 hover:bg-neutral-800/50 rounded px-1 transition-colors">
                      <div className="w-20 text-sm font-mono text-neutral-300">{factor.name}</div>
                      <div className={`w-20 h-8 flex items-center justify-center text-xs font-medium rounded-md ${factor.synced ? "bg-green-900/80 text-green-400" : "bg-neutral-800 text-neutral-600"}`}>
                        {factor.synced ? "✓" : "-"}
                      </div>
                      <div className={`w-20 h-8 flex items-center justify-center text-xs font-medium rounded-md ${factor.expired ? "bg-red-900/80 text-red-400" : "bg-neutral-800 text-neutral-600"}`}>
                        {factor.expired ? "✕" : "-"}
                      </div>
                      <div className={`w-20 h-8 flex items-center justify-center text-xs font-medium rounded-md ${factor.missing ? "bg-yellow-900/80 text-yellow-400" : "bg-neutral-800 text-neutral-600"}`}>
                        {factor.missing ? "!" : "-"}
                      </div>
                      <div className={`w-20 h-8 flex items-center justify-center text-xs font-medium rounded-md ${factor.waiting ? "bg-blue-900/80 text-blue-400" : "bg-neutral-800 text-neutral-600"}`}>
                        {factor.waiting ? "⏳" : "-"}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* 因子排行榜与告警 */}
        <div className="space-y-4">
          {/* 因子排行榜 */}
          <Card className="bg-neutral-900 border-neutral-700">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-neutral-300">因子排行榜</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {factorValidityData.slice(0, 5).map((factor, idx) => (
                  <div key={idx} className="flex items-center justify-between py-1">
                    <span className="text-sm text-neutral-300">{idx + 1}. {factor.name}</span>
                    <span className="text-sm font-bold text-orange-400">{(factor.validity * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* 漂移告警 */}
          <Card className="bg-neutral-900 border-neutral-700">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-neutral-300">漂移告警</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex items-start gap-2 p-2 bg-yellow-900/20 border border-yellow-600/50 rounded">
                <AlertTriangle className="w-4 h-4 text-yellow-400 flex-shrink-0 mt-0.5" />
                <div className="text-xs">
                  <p className="text-yellow-300 font-medium">KDJ 有效性下降</p>
                  <p className="text-yellow-400/70">近7日平均 72%</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 同步失败告警 */}
          <Card className="bg-neutral-900 border-neutral-700">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-neutral-300">同步失败</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex items-start gap-2 p-2 bg-red-900/20 border border-red-600/50 rounded">
                <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                <div className="text-xs">
                  <p className="text-red-300 font-medium">BOLL 回测数据缺失</p>
                  <p className="text-red-400/70">需要重新计算</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* 模型栈卡片 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-300">模型治理中心 - 完整模型栈</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {models.map((model, idx) => (
              <Card key={idx} className="bg-neutral-800 border-neutral-700">
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <CardTitle className="text-sm text-white">{model.name}</CardTitle>
                      <p className="text-xs text-neutral-400 mt-1">{model.type}</p>
                    </div>
                    <Badge className={getModelStatusColor(model.status)} style={{ height: "20px", fontSize: "11px" }}>
                      {model.status === "running" ? "运行" : model.status === "ready" ? "就绪" : model.status === "standby" ? "待命" : "禁用"}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div>
                      <p className="text-neutral-500">延迟</p>
                      <p className="text-neutral-200 font-medium">{model.latency}</p>
                    </div>
                    <div>
                      <p className="text-neutral-500">准确率</p>
                      <p className="text-neutral-200 font-medium">{(model.accuracy * 100).toFixed(0)}%</p>
                    </div>
                  </div>
                  <div>
                    <p className="text-neutral-500 text-xs mb-1">容量</p>
                    <p className="text-neutral-300 text-xs">{model.capacity}</p>
                  </div>
                  {model.status === "disabled" && (
                    <div className="p-2 bg-neutral-900 border border-neutral-700 rounded text-xs text-neutral-400">
                      灰态保留，预留后端抽象
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
