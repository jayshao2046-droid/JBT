"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Clock, AlertTriangle } from "lucide-react"

const kpiData = [
  { label: "Ollama 状态", value: "运行中", status: "pass", color: "green" },
  { label: "在线模型供应商", value: "正常", status: "pass", color: "blue" },
  { label: "因子同步状态", value: "就绪", status: "pass", color: "green" },
  { label: "回测链路状态", value: "正常", status: "pass", color: "green" },
  { label: "发布门禁状态", value: "启用", status: "pass", color: "orange" },
  { label: "通知服务状态", value: "正常", status: "pass", color: "green" },
]

const localModels = [
  { name: "Qwen3 14B", status: "running", latency: "2.3ms", memory: "24GB", capacity: "主用" },
  { name: "DeepSeek-R1 14B", status: "ready", latency: "2.8ms", memory: "24GB", capacity: "兼容" },
  { name: "XGBoost", status: "running", latency: "1.2ms", memory: "4GB", capacity: "研究" },
]

const onlineModels = [
  {
    name: "Qwen3.6-Plus",
    provider: "Alibaba",
    status: "default",
    latency: "45ms",
    capacity: "默认 L3",
  },
  {
    name: "Qwen3-Max",
    provider: "Alibaba",
    status: "upgrade",
    latency: "60ms",
    capacity: "升级复核",
  },
  {
    name: "DeepSeek-V3.2",
    provider: "DeepSeek",
    status: "standby",
    latency: "50ms",
    capacity: "在线备援",
  },
]

const configChangeLog = [
  { time: "2024-04-05 18:32", event: "模型切换", detail: "Qwen3 14B 主用模型就绪", user: "系统自动" },
  { time: "2024-04-05 14:15", event: "门禁变更", detail: "启用 L3 在线模型复核", user: "admin@jbot" },
  { time: "2024-04-04 22:00", event: "研究窗口调整", detail: "非交易时段研究启用", user: "系统自动" },
  { time: "2024-04-04 09:00", event: "模型激活", detail: "XGBoost 研究模型启用", user: "admin@jbot" },
]

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

export default function ConfigRuntime() {
  return (
    <div className="p-6 space-y-6 bg-neutral-950 min-h-screen">
      {/* KPI 卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
        {kpiData.map((kpi, idx) => (
          <Card key={idx} className="bg-neutral-900 border-neutral-700">
            <CardContent className="p-3">
              <p className="text-xs text-neutral-400 mb-1 truncate">{kpi.label}</p>
              <div className="flex items-end justify-between">
                <p className={`text-sm font-bold ${kpi.color === "green" ? "text-green-400" : kpi.color === "blue" ? "text-blue-400" : "text-orange-400"}`}>
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

      {/* 本地模型运行卡 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-300">本地模型运行卡组</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {localModels.map((model, idx) => (
              <Card key={idx} className="bg-neutral-800 border-neutral-700">
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-sm text-white">{model.name}</CardTitle>
                      <p className="text-xs text-neutral-400 mt-1">{model.capacity}</p>
                    </div>
                    <Badge className={getModelStatusColor(model.status)}>
                      {model.status === "running" ? "运行" : "就绪"}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <p className="text-neutral-500">延迟</p>
                      <p className="text-neutral-200 font-medium">{model.latency}</p>
                    </div>
                    <div>
                      <p className="text-neutral-500">内存</p>
                      <p className="text-neutral-200 font-medium">{model.memory}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          <div className="mt-4 p-3 bg-blue-900/20 border border-blue-600/50 rounded">
            <p className="text-xs text-blue-400 font-medium">🔧 默认本地模型组合</p>
            <p className="text-xs text-blue-300 mt-1">
              Qwen3 14B 主模型 + DeepSeek-R1 14B 兼容 + Qwen2.5 L1 审查 + XGBoost 研究
            </p>
          </div>
        </CardContent>
      </Card>

      {/* 在线模型路由卡 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-300">在线模型路由卡组</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {onlineModels.map((model, idx) => (
              <Card key={idx} className="bg-neutral-800 border-neutral-700">
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-sm text-white">{model.name}</CardTitle>
                      <p className="text-xs text-neutral-400 mt-1">{model.provider}</p>
                    </div>
                    <Badge className={getModelStatusColor(model.status)}>
                      {model.status === "default" ? "默认" : model.status === "upgrade" ? "升级" : "备援"}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <p className="text-neutral-500">延迟</p>
                      <p className="text-neutral-200 font-medium">{model.latency}</p>
                    </div>
                    <div>
                      <p className="text-neutral-500">角色</p>
                      <p className="text-neutral-200 font-medium">{model.capacity}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          <div className="mt-4 p-3 bg-purple-900/20 border border-purple-600/50 rounded">
            <p className="text-xs text-purple-400 font-medium">☁️ 在线 L3 默认与升级路径</p>
            <p className="text-xs text-purple-300 mt-1">
              Qwen3.6-Plus (默认) → Qwen3-Max (升级复核) / DeepSeek-V3.2 (备援)
            </p>
          </div>
        </CardContent>
      </Card>

      {/* 研究调度与交易时段规则 + 发布门禁 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 研究调度与交易时段规则 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">研究调度与交易时段规则</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="border border-neutral-700 rounded p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-white">XGBoost 激活状态</span>
                <Badge className="bg-green-900 text-green-400">启用</Badge>
              </div>
              <p className="text-xs text-neutral-400">研究主线模型已激活</p>
            </div>

            <div className="border border-neutral-700 rounded p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-white">LightGBM 预留状态</span>
                <Badge className="bg-neutral-700 text-neutral-400">禁用</Badge>
              </div>
              <p className="text-xs text-neutral-400">灰态保留，后端抽象预留</p>
            </div>

            <div className="border border-neutral-700 rounded p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-white">非交易时段研究</span>
                <div className="flex items-center gap-2">
                  <Switch defaultChecked={true} />
                </div>
              </div>
              <p className="text-xs text-neutral-400">21:00 - 09:30 启用自动调参</p>
            </div>

            <div className="border border-red-600/50 bg-red-900/20 rounded p-3">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-xs font-medium text-red-400">交易时段禁令</p>
                  <p className="text-xs text-red-300 mt-1">09:30 - 15:00 期货交易时段禁止自动调参和重训练</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 发布门禁卡 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">发布门禁卡组</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="border border-neutral-700 rounded p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-white">模拟交易</span>
                <Badge className="bg-green-900 text-green-400">开启</Badge>
              </div>
              <p className="text-xs text-neutral-400">所有策略允许推送到模拟交易</p>
            </div>

            <div className="border border-neutral-700 rounded p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-white">实盘执行</span>
                <Badge className="bg-red-900 text-red-400">锁定</Badge>
              </div>
              <p className="text-xs text-neutral-400">实盘入口可见但已锁定</p>
            </div>

            <div className="border border-neutral-700 rounded p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-white">因子同步验证</span>
                <Badge className="bg-blue-900 text-blue-400">启用</Badge>
              </div>
              <p className="text-xs text-neutral-400">所有因子必须完成回测并与策略同步</p>
            </div>

            <div className="border border-neutral-700 rounded p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-white">回测有效期验证</span>
                <Badge className="bg-blue-900 text-blue-400">启用</Badge>
              </div>
              <p className="text-xs text-neutral-400">回测超过 7 天将禁用执行</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 配置变更留痕视图 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-300">配置变更留痕视图</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {configChangeLog.map((log, idx) => (
              <div key={idx} className="border border-neutral-700 rounded p-3 flex items-start gap-4">
                <div className="flex-shrink-0">
                  <Clock className="w-4 h-4 text-neutral-500 mt-0.5" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <div>
                      <p className="text-sm font-medium text-white">{log.event}</p>
                      <p className="text-xs text-neutral-400 mt-0.5">{log.detail}</p>
                    </div>
                    <span className="text-xs text-neutral-500 whitespace-nowrap">{log.time}</span>
                  </div>
                  <p className="text-xs text-neutral-500">操作人: {log.user}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 系统状态摘要 */}
      <Card className="bg-neutral-900 border-green-600/50">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-green-400">系统状态摘要</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-xs text-green-300/80">
          <p>✓ 本地模型组合就绪：Qwen3 14B + DeepSeek-R1 14B + Qwen2.5 + XGBoost</p>
          <p>✓ 在线 L3 连接正常：Qwen3.6-Plus (默认) + Qwen3-Max (升级) + DeepSeek-V3.2 (备援)</p>
          <p>✓ 研究调度正常运行，交易时段自动禁用调参</p>
          <p>✓ 因子同步验证启用，所有策略需完成回测对齐</p>
          <p>✓ 发布门禁启用，模拟交易开放，实盘锁定</p>
          <p>✓ 所有通知通道正常，飞书和邮件服务就绪</p>
        </CardContent>
      </Card>
    </div>
  )
}
