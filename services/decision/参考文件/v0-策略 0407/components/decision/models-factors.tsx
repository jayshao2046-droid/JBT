"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { AlertTriangle } from "lucide-react"

const kpiData = [
  { label: "本地主模型状态", value: "就绪", status: "pass", color: "green" },
  { label: "在线 L3 状态", value: "连接", status: "pass", color: "blue" },
  { label: "平均决策延迟", value: "2.3ms", status: "pass", color: "orange" },
  { label: "已注册因子数", value: "48", status: "pass", color: "purple" },
  { label: "已对齐回测因子", value: "45", status: "warning", color: "yellow" },
  { label: "过期因子数", value: "3", status: "alert", color: "red" },
]

// 因子有效性热力图数据
const factorValidityData = [
  { name: "MA5", validity: 0.92, stability: 0.87, recent: 0.89 },
  { name: "RSI14", validity: 0.88, stability: 0.85, recent: 0.82 },
  { name: "MACD", validity: 0.85, stability: 0.91, recent: 0.79 },
  { name: "KDJ", validity: 0.79, stability: 0.76, recent: 0.72 },
  { name: "ATR20", validity: 0.83, stability: 0.88, recent: 0.85 },
  { name: "BOLL", validity: 0.81, stability: 0.79, recent: 0.75 },
  { name: "CCI20", validity: 0.76, stability: 0.73, recent: 0.68 },
  { name: "STOCH", validity: 0.74, stability: 0.71, recent: 0.65 },
]

// 因子同步状态数据
const factorSyncData = [
  { name: "MA5", synced: 1, expired: 0, missing: 0, waiting: 0 },
  { name: "RSI14", synced: 1, expired: 0, missing: 0, waiting: 0 },
  { name: "MACD", synced: 1, expired: 0, missing: 0, waiting: 0 },
  { name: "KDJ", synced: 0, expired: 1, missing: 0, waiting: 0 },
  { name: "ATR20", synced: 1, expired: 0, missing: 0, waiting: 0 },
  { name: "BOLL", synced: 0, expired: 0, missing: 1, waiting: 0 },
  { name: "CCI20", synced: 1, expired: 0, missing: 0, waiting: 0 },
  { name: "STOCH", synced: 0, expired: 0, missing: 0, waiting: 1 },
]

const models = [
  {
    name: "Qwen3 14B",
    type: "本地主模型",
    status: "running",
    latency: "2.3ms",
    accuracy: 0.94,
    capacity: "14B参数",
  },
  {
    name: "DeepSeek-R1 14B",
    type: "兼容本地模型",
    status: "ready",
    latency: "2.8ms",
    accuracy: 0.92,
    capacity: "14B参数",
  },
  {
    name: "Qwen2.5",
    type: "L1 审查模型",
    status: "ready",
    latency: "1.8ms",
    accuracy: 0.88,
    capacity: "可切换系列",
  },
  {
    name: "Qwen3.6-Plus",
    type: "默认在线 L3",
    status: "running",
    latency: "45ms",
    accuracy: 0.96,
    capacity: "云端部署",
  },
  {
    name: "Qwen3-Max",
    type: "升级复核卡",
    status: "ready",
    latency: "60ms",
    accuracy: 0.97,
    capacity: "云端部署",
  },
  {
    name: "DeepSeek-V3.2",
    type: "在线备援卡",
    status: "standby",
    latency: "50ms",
    accuracy: 0.95,
    capacity: "云端部署",
  },
  {
    name: "DeepSeek-R1",
    type: "争议复核卡",
    status: "ready",
    latency: "55ms",
    accuracy: 0.93,
    capacity: "云端部署",
  },
  {
    name: "XGBoost",
    type: "研究主线模型",
    status: "running",
    latency: "1.2ms",
    accuracy: 0.91,
    capacity: "本地部署",
  },
  {
    name: "LightGBM",
    type: "预留后端",
    status: "disabled",
    latency: "-",
    accuracy: 0.89,
    capacity: "灰态保留",
  },
]

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
