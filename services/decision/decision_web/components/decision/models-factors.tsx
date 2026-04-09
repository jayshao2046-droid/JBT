"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { fetchModelStatus, fetchRuntimeOverview, routeModel, type ModelStatus, type ModelRuntimeOverview } from "@/lib/api"
import { Loader2 } from "lucide-react"

const getModelStatusColor = (status: string) => {
  switch (status) {
    case "running": return "bg-green-900 text-green-400"
    case "ready": return "bg-blue-900 text-blue-400"
    case "configured": return "bg-cyan-900 text-cyan-400"
    case "standby": return "bg-yellow-900 text-yellow-400"
    case "disabled": return "bg-neutral-800 text-neutral-500"
    default: return "bg-neutral-700 text-neutral-300"
  }
}

/* 决策层级定义 — 参照总计划 5.6 模型路由 */
const DECISION_LAYERS = [
  { id: "signal", label: "信号输入", desc: "因子 + 市场上下文 → 策略生成原始信号", color: "bg-blue-600" },
  { id: "L1", label: "L1 门禁审查", desc: "Qwen2.5：快速过滤，低延迟 gate/deny 决策", color: "bg-orange-500" },
  { id: "L2", label: "L2 主审", desc: "Qwen3 14B：深度分析，因子评估，置信度打分", color: "bg-purple-500" },
  { id: "L3", label: "L3 在线确认", desc: "（未来）外部大模型二次确认，高风险信号必经", color: "bg-neutral-600" },
  { id: "gate", label: "发布门禁", desc: "回测证书 + 研究快照 + 资格检查 → 允许/拒绝发布", color: "bg-cyan-600" },
  { id: "target", label: "执行目标", desc: "通过门禁后推送到模拟交易 / 实盘交易", color: "bg-green-600" },
]

/* 因子类别 — 参照 v0 策略页因子分类 */
const FACTOR_CATEGORIES = [
  { name: "动量因子", examples: ["MACD", "RSI", "KDJ", "ROC", "CMO", "WilliamsR"], color: "text-orange-400 border-orange-600/40" },
  { name: "均值回归", examples: ["Bollinger", "ZScore", "MeanDev", "Hurst", "KeltnerChannel"], color: "text-blue-400 border-blue-600/40" },
  { name: "突破因子", examples: ["DonchianBreak", "ATRBreakout", "VolExpansion", "RangeBreak"], color: "text-green-400 border-green-600/40" },
  { name: "成交量", examples: ["OBV", "VWAP", "VolumeRatio", "MFI", "ADLine", "ChaikinFlow"], color: "text-cyan-400 border-cyan-600/40" },
  { name: "波动率", examples: ["ATR", "HistVol", "Parkinson", "GarmanKlass", "YangZhang"], color: "text-yellow-400 border-yellow-600/40" },
]

export default function ModelsFactors({ refreshToken }: { refreshToken?: number }) {
  const [activeTab, setActiveTab] = useState("flow")
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null)
  const [runtime, setRuntime] = useState<ModelRuntimeOverview | null>(null)
  const [routeStrategyId, setRouteStrategyId] = useState("")
  const [routeResult, setRouteResult] = useState<{ allowed: boolean; reason: string } | null>(null)
  const [routing, setRouting] = useState(false)

  useEffect(() => {
    fetchModelStatus().then(setModelStatus).catch(() => {})
    fetchRuntimeOverview().then(setRuntime).catch(() => {})
  }, [refreshToken])

  async function handleRouteTest() {
    if (!routeStrategyId.trim()) return
    setRouting(true)
    setRouteResult(null)
    try {
      const res = await routeModel({ strategy_id: routeStrategyId.trim() })
      setRouteResult(res)
    } catch {
      setRouteResult({ allowed: false, reason: "请求失败" })
    } finally {
      setRouting(false)
    }
  }

  const localModels = runtime?.local_models ?? []
  const onlineModels = runtime?.online_models ?? []
  const allModels = [...localModels, ...onlineModels]
  const factorSync = runtime?.factor_sync
  const modelRouter = runtime?.model_router
  const researchWindow = runtime?.research_window

  return (
    <div className="p-6 space-y-6 bg-neutral-950 min-h-screen">
      {/* KPI 行 */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {[
          { label: "本地模型", value: localModels.length, color: "text-cyan-400" },
          { label: "在线模型", value: onlineModels.length, color: "text-purple-400" },
          { label: "执行门禁", value: modelStatus?.execution_gate_enabled ? "启用" : "关闭", color: modelStatus?.execution_gate_enabled ? "text-green-400" : "text-neutral-500" },
          { label: "实盘门禁", value: modelStatus?.live_trading_gate_locked ? "锁定" : "开放", color: modelStatus?.live_trading_gate_locked ? "text-red-400" : "text-green-400" },
          { label: "因子对齐", value: factorSync ? `${factorSync.aligned}` : "—", color: "text-green-400" },
          { label: "因子失配", value: factorSync ? `${factorSync.mismatch}` : "—", color: factorSync && factorSync.mismatch > 0 ? "text-yellow-400" : "text-green-400" },
        ].map((kpi, idx) => (
          <Card key={idx} className="bg-neutral-900 border-neutral-700">
            <CardContent className="p-4">
              <p className="text-xs text-neutral-400 mb-2">{kpi.label}</p>
              <p className={`text-2xl font-bold ${kpi.color}`}>{kpi.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Tab 切换：决策流 / 模型栈 / 因子 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-neutral-300">模型与因子</CardTitle>
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-auto">
              <TabsList className="bg-neutral-800 border border-neutral-700 h-8">
                <TabsTrigger value="flow" className="text-xs data-[state=active]:bg-orange-500 data-[state=active]:text-white data-[state=inactive]:text-neutral-400 h-7 px-3">决策流</TabsTrigger>
                <TabsTrigger value="models" className="text-xs data-[state=active]:bg-orange-500 data-[state=active]:text-white data-[state=inactive]:text-neutral-400 h-7 px-3">模型栈</TabsTrigger>
                <TabsTrigger value="factors" className="text-xs data-[state=active]:bg-orange-500 data-[state=active]:text-white data-[state=inactive]:text-neutral-400 h-7 px-3">因子分类</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </CardHeader>
        <CardContent>
          {/* ---- 决策流 ---- */}
          {activeTab === "flow" && (
            <div className="space-y-6">
              {/* 决策路径可视化 */}
              <div>
                <p className="text-xs text-neutral-500 mb-4 uppercase tracking-wider">决策路径 — 信号从生成到执行的全链路</p>
                <div className="flex items-stretch gap-2 overflow-x-auto pb-2">
                  {DECISION_LAYERS.map((layer, idx) => {
                    const matchedModel = allModels.find(m =>
                      (layer.id === "L1" && m.route_role === "gate_review") ||
                      (layer.id === "L2" && m.route_role === "primary_local_review")
                    )
                    return (
                      <div key={layer.id} className="flex items-center gap-2 flex-shrink-0">
                        <div className="w-36 border border-neutral-700 rounded-lg p-3 bg-neutral-800">
                          <div className={`w-full h-1 ${layer.color} rounded mb-2`} />
                          <p className="text-xs font-medium text-white mb-1">{layer.label}</p>
                          <p className="text-[10px] text-neutral-400 leading-snug">{layer.desc}</p>
                          {matchedModel && (
                            <div className="mt-2 pt-2 border-t border-neutral-700">
                              <p className="text-[10px] text-neutral-500">当前：</p>
                              <p className="text-[11px] text-cyan-400 font-medium truncate">{matchedModel.model_name}</p>
                              <Badge className={`${getModelStatusColor(matchedModel.status)} mt-1`} style={{ fontSize: "9px", height: "16px" }}>
                                {matchedModel.status}
                              </Badge>
                            </div>
                          )}
                          {layer.id === "L3" && onlineModels.length === 0 && (
                            <div className="mt-2 pt-2 border-t border-neutral-700">
                              <p className="text-[10px] text-neutral-600 italic">未配置</p>
                            </div>
                          )}
                          {layer.id === "target" && runtime?.execution_gate && (
                            <div className="mt-2 pt-2 border-t border-neutral-700">
                              <p className="text-[10px] text-neutral-500">目标：</p>
                              <p className="text-[11px] text-green-400 font-medium">{runtime.execution_gate.target}</p>
                            </div>
                          )}
                        </div>
                        {idx < DECISION_LAYERS.length - 1 && (
                          <span className="text-neutral-600 text-lg">→</span>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* 何时用哪个模型 */}
              <div>
                <p className="text-xs text-neutral-500 mb-3 uppercase tracking-wider">模型选择策略 — 何时用哪个模型</p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="border border-orange-600/40 rounded-lg p-4 bg-orange-900/10">
                    <p className="text-sm font-medium text-orange-400 mb-2">L1 门禁审查</p>
                    <ul className="text-xs text-neutral-400 space-y-1 list-disc list-inside">
                      <li>所有信号必经，延迟 &lt; 100ms</li>
                      <li>快速 gate / deny 二分决策</li>
                      <li>轻量模型（7B 级），过滤噪声信号</li>
                      <li>仅判断信号是否值得深入审查</li>
                    </ul>
                  </div>
                  <div className="border border-purple-600/40 rounded-lg p-4 bg-purple-900/10">
                    <p className="text-sm font-medium text-purple-400 mb-2">L2 主审</p>
                    <ul className="text-xs text-neutral-400 space-y-1 list-disc list-inside">
                      <li>通过 L1 后进入，延迟可达数秒</li>
                      <li>深度因子评估 + 市场上下文分析</li>
                      <li>生成置信度打分和推理摘要</li>
                      <li>本地 14B 级模型，无外部依赖</li>
                    </ul>
                  </div>
                  <div className="border border-neutral-600/40 rounded-lg p-4 bg-neutral-800/50">
                    <p className="text-sm font-medium text-neutral-400 mb-2">L3 在线确认（未来）</p>
                    <ul className="text-xs text-neutral-500 space-y-1 list-disc list-inside">
                      <li>高风险/高金额信号必经</li>
                      <li>外部大模型（DeepSeek / GPT）二次确认</li>
                      <li>联网能力：实时新闻、宏观数据</li>
                      <li>当前尚未启用，计划 Phase H</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ---- 模型栈 ---- */}
          {activeTab === "models" && (
            <div className="space-y-4">
              {allModels.length === 0 ? (
                <p className="text-sm text-neutral-500 text-center py-8">暂无已配置模型</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {allModels.map((model, idx) => (
                    <Card key={idx} className="bg-neutral-800 border-neutral-700">
                      <CardHeader className="pb-2">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <CardTitle className="text-sm text-white truncate">{model.model_name}</CardTitle>
                            <p className="text-xs text-neutral-400 mt-1">{model.deployment_class} · {model.route_role}</p>
                          </div>
                          <Badge className={getModelStatusColor(model.status)} style={{ height: "20px", fontSize: "11px" }}>
                            {model.status}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <p className="text-xs text-neutral-500 mb-2">{model.source}</p>
                        <div className="text-[10px] text-neutral-600">
                          {model.route_role === "gate_review" && "作用：门禁层快速过滤，判断信号是否值得深入审查"}
                          {model.route_role === "primary_local_review" && "作用：主审层深度分析，生成置信度与推理摘要"}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}

              {/* 模型路由统计 */}
              {modelRouter && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
                  <div className="border border-neutral-700 rounded p-3 text-center">
                    <p className="text-xs text-neutral-400 mb-1">回测证书</p>
                    <Badge className={modelRouter.require_backtest_cert ? "bg-green-900 text-green-400" : "bg-neutral-700 text-neutral-300"}>
                      {modelRouter.require_backtest_cert ? "强制" : "宽松"}
                    </Badge>
                  </div>
                  <div className="border border-neutral-700 rounded p-3 text-center">
                    <p className="text-xs text-neutral-400 mb-1">研究快照</p>
                    <Badge className={modelRouter.require_research_snapshot ? "bg-green-900 text-green-400" : "bg-neutral-700 text-neutral-300"}>
                      {modelRouter.require_research_snapshot ? "强制" : "宽松"}
                    </Badge>
                  </div>
                  <div className="border border-neutral-700 rounded p-3 text-center">
                    <p className="text-xs text-neutral-400 mb-1">合格策略</p>
                    <p className="text-lg font-bold text-green-400">{modelRouter.eligible_strategies}</p>
                  </div>
                  <div className="border border-neutral-700 rounded p-3 text-center">
                    <p className="text-xs text-neutral-400 mb-1">阻塞策略</p>
                    <p className="text-lg font-bold text-red-400">{modelRouter.blocked_strategies}</p>
                  </div>
                </div>
              )}

              {/* 路由测试 */}
              <div className="border border-neutral-700 rounded-lg p-4 bg-neutral-800/50 mt-4">
                <p className="text-xs text-neutral-500 mb-3 uppercase tracking-wider">路由资格测试</p>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    placeholder="输入策略 ID"
                    value={routeStrategyId}
                    onChange={e => setRouteStrategyId(e.target.value)}
                    className="flex-1 h-8 rounded bg-neutral-900 border border-neutral-600 px-3 text-sm text-white placeholder:text-neutral-500 outline-none focus:border-cyan-500"
                  />
                  <button
                    onClick={handleRouteTest}
                    disabled={routing || !routeStrategyId.trim()}
                    className="h-8 px-4 rounded bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 text-white text-xs font-medium flex items-center gap-1"
                  >
                    {routing && <Loader2 className="w-3 h-3 animate-spin" />}
                    测试路由
                  </button>
                </div>
                {routeResult && (
                  <div className={`mt-2 text-xs p-2 rounded ${routeResult.allowed ? "bg-green-900/30 text-green-400" : "bg-red-900/30 text-red-400"}`}>
                    {routeResult.allowed ? "✅ 允许发布" : "❌ 阻塞"} — {routeResult.reason}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ---- 因子分类 ---- */}
          {activeTab === "factors" && (
            <div className="space-y-4">
              {/* 因子同步状态 */}
              {factorSync && (
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="text-center p-4 bg-green-900/20 border border-green-600/30 rounded-lg">
                    <p className="text-2xl font-bold text-green-400">{factorSync.aligned}</p>
                    <p className="text-xs text-neutral-400 mt-1">已对齐</p>
                  </div>
                  <div className="text-center p-4 bg-yellow-900/20 border border-yellow-600/30 rounded-lg">
                    <p className="text-2xl font-bold text-yellow-400">{factorSync.mismatch}</p>
                    <p className="text-xs text-neutral-400 mt-1">失配</p>
                  </div>
                  <div className="text-center p-4 bg-neutral-800 border border-neutral-700 rounded-lg">
                    <p className="text-2xl font-bold text-neutral-400">{factorSync.unknown}</p>
                    <p className="text-xs text-neutral-400 mt-1">未知</p>
                  </div>
                </div>
              )}

              {/* 因子类别卡片 — 参照 v0 五大类 */}
              <p className="text-xs text-neutral-500 uppercase tracking-wider">因子类别参考（基于策略模板标准分类）</p>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {FACTOR_CATEGORIES.map((cat, idx) => (
                  <div key={idx} className={`border rounded-lg p-4 bg-neutral-800/50 ${cat.color}`}>
                    <p className="text-sm font-medium mb-2">{cat.name}</p>
                    <div className="flex flex-wrap gap-1">
                      {cat.examples.map((f) => (
                        <span key={f} className="text-[10px] px-2 py-0.5 rounded bg-neutral-700/50 text-neutral-300">{f}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              {factorSync && (
                <p className="text-xs text-neutral-500 mt-2">{factorSync.note}</p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 研究窗口 */}
      {researchWindow && (
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">研究窗口</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="border border-neutral-700 rounded p-3">
                <p className="text-xs text-neutral-400 mb-1">窗口时间</p>
                <p className="text-sm font-medium text-white">{researchWindow.start} ~ {researchWindow.end}</p>
              </div>
              <div className="border border-neutral-700 rounded p-3">
                <p className="text-xs text-neutral-400 mb-1">时区</p>
                <p className="text-sm font-medium text-white">{researchWindow.timezone}</p>
              </div>
              <div className="border border-neutral-700 rounded p-3">
                <p className="text-xs text-neutral-400 mb-1">当前状态</p>
                <Badge className={researchWindow.is_open ? "bg-green-900 text-green-400" : "bg-red-900 text-red-400"}>
                  {researchWindow.is_open ? "开放中" : "已关闭"}
                </Badge>
              </div>
              <div className="border border-neutral-700 rounded p-3">
                <p className="text-xs text-neutral-400 mb-1">当前时间</p>
                <p className="text-sm font-medium text-neutral-300">{researchWindow.current_time}</p>
              </div>
            </div>
            <p className="text-xs text-neutral-500 mt-3">{researchWindow.rule}</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
