"use client"

import { useState, useEffect } from "react"
import api from '@/src/utils/api'
import { formatTimeframeValue, resolveFieldLabel } from '@/src/utils/strategyPresentation'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  TrendingUp,
  TrendingDown,
  BarChart3,
  Percent,
  RefreshCw,
  Activity,
  Hash,
  AlertTriangle,
  Lightbulb,
  ChevronDown,
  ChevronRight,
  Square,
} from "lucide-react"
import {
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  Bar,
  BarChart,
  Cell,
  ReferenceLine,
} from "recharts"

// ─── 调优建议生成（规则引擎）────────────────────────────────────────
type Suggestion = { level: 'critical' | 'warning' | 'info' | 'suggestion'; icon: string; title: string; detail: string }

function generateOptimizationSuggestions(
  result: any,
  kpis: { totalReturn: number | null; maxDrawdown: number | null; sharpeRatio: number | null; winRate: number | null; totalTrades: number | null },
  tradeDetails: any[]
): Suggestion[] {
  const suggestions: Suggestion[] = []
  const { totalReturn, maxDrawdown, sharpeRatio, winRate, totalTrades } = kpis

  if (result?.status === 'failed') {
    suggestions.push({
      level: 'critical', icon: '❌',
      title: '回测执行失败 / Backtest Failed',
      detail: `错误：${String(result.error_message ?? '未知错误').split('\n')[0]}。请检查策略合约配置、数据可用性与参数边界。`,
    })
  }

  if (totalTrades !== null && totalTrades === 0) {
    suggestions.push({
      level: 'critical', icon: '⚠️',
      title: '零成交 / Zero Trades',
      detail: '回测期间没有任何成交。可能原因：①合约代码不匹配；②信号逻辑未触发；③时间窗口在数据空档期。建议检查合约选择和 YAML 定义的 symbols。',
    })
    return suggestions
  }

  if (totalTrades !== null && totalTrades < 10) {
    suggestions.push({
      level: 'warning', icon: '📊',
      title: `样本量不足 / Insufficient Samples (${totalTrades} 笔)`,
      detail: '交易笔数 < 10，统计可靠性极低。建议：延长回测时间至 3 年以上 / Try backtesting over 3+ years to improve statistical confidence.',
    })
  }

  if (sharpeRatio !== null && sharpeRatio < 0.3) {
    suggestions.push({
      level: 'warning', icon: '📉',
      title: `夏普比率偏低 / Low Sharpe (${sharpeRatio.toFixed(2)})`,
      detail: '风险调整后收益不佳。建议：①增加止损降低尾部亏损；②优化信号进入质量（减少低质信号）；③尝试缩短持仓周期 / Add stop-loss rules and filter low-quality signals.',
    })
  } else if (sharpeRatio !== null && sharpeRatio >= 2.5 && totalTrades !== null && totalTrades < 30) {
    suggestions.push({
      level: 'warning', icon: '🔍',
      title: `可能过拟合 / Possible Overfitting (Sharpe=${sharpeRatio.toFixed(2)})`,
      detail: '夏普极高但样本量少，存在数据挖掘偏差风险。建议使用样本外数据验证（Walk-Forward Analysis），并在多个品种上测试参数稳健性。',
    })
  }

  if (maxDrawdown !== null && maxDrawdown > 30) {
    suggestions.push({
      level: 'warning', icon: '🔽',
      title: `最大回撤过大 / High Drawdown (${maxDrawdown.toFixed(1)}%)`,
      detail: `回撤 ${maxDrawdown.toFixed(1)}% 超过 30% 危险线。建议：①降低 positionSize（当前可适当减少 20-30%）；②添加追踪止损（trailing_stop）；③限制单日最大损失 / Reduce positionSize and add trailing_stop parameter.',`,
    })
  }

  if (winRate !== null && winRate < 35) {
    const closeTrades = tradeDetails.filter(t => (t.offset ?? '').toUpperCase() === 'CLOSE' && t.profit != null)
    const avgWin = closeTrades.filter(t => t.profit > 0).reduce((s, t) => s + t.profit, 0) / Math.max(closeTrades.filter(t => t.profit > 0).length, 1)
    const avgLoss = Math.abs(closeTrades.filter(t => t.profit < 0).reduce((s, t) => s + t.profit, 0) / Math.max(closeTrades.filter(t => t.profit < 0).length, 1))
    const plRatio = avgLoss > 0 ? (avgWin / avgLoss) : null
    suggestions.push({
      level: 'suggestion', icon: '🎯',
      title: `胜率偏低 / Low Win Rate (${winRate.toFixed(1)}%)`,
      detail: `盈亏比约 ${plRatio ? plRatio.toFixed(2) : '--'}。低胜率策略需要更高的盈亏比（建议 > 2.0）才能盈利。检查：信号过滤条件是否太宽松 / Win rate is low. Ensure profit-loss ratio > 2.0 to compensate.`,
    })
  }

  if (totalReturn !== null && maxDrawdown !== null && maxDrawdown > 0) {
    const calmar = totalReturn / maxDrawdown
    if (calmar < 0.3 && totalReturn > 0) {
      suggestions.push({
        level: 'suggestion', icon: '⚖️',
        title: `卡尔马比率低 / Low Calmar (${calmar.toFixed(2)})`,
        detail: '收益相对于承担的最大回撤风险偏低（< 0.3）。建议通过风控参数优化（止损线、仓位管理）提升风险效率 / Improve risk efficiency by tightening stop-loss.',
      })
    }
  }

  if (totalTrades !== null && totalTrades > 300) {
    const totalComm = tradeDetails.reduce((s: number, t: any) => s + (t.commission ?? 0), 0)
    const finalBalance = result?.finalCapital ?? 0
    const initBalance = result?.initialCapital ?? result?.payload?.params?.initialCapital ?? 200000
    const commPct = initBalance > 0 ? (totalComm / initBalance * 100) : 0
    if (commPct > 5) {
      suggestions.push({
        level: 'info', icon: '💸',
        title: `手续费侵蚀严重 / High Commission Cost (${commPct.toFixed(1)}%)`,
        detail: `累计手续费占初始资金 ${commPct.toFixed(1)}%，显著侵蚀收益。建议增加信号过滤降低换手频率，或调整 commission 参数确认假设正确 / Reduce trade frequency to lower commission drag.`,
      })
    }
  }

  if (winRate !== null && winRate > 65 && totalReturn !== null && totalReturn < 3) {
    suggestions.push({
      level: 'suggestion', icon: '🔀',
      title: '高胜率低收益 / High Win Rate but Low Return',
      detail: '胜率高但盈利总额低，可能止盈设置过保守。建议适当放宽 take_profit 或降低信号过滤阈值，使获利单能跑更远 / Consider loosening take_profit to let winners run.',
    })
  }

  if (suggestions.length === 0 && result?.status === 'completed') {
    suggestions.push({
      level: 'info', icon: '✅',
      title: '策略指标正常 / Strategy Metrics Normal',
      detail: '未发现明显风险异常，建议进行：①多品种 Walk-Forward 验证；②蒙特卡洛模拟检验稳健性；③压力测试（高波动/熔断市场）；④逐步增加 initialCapital 测试容量 / Run out-of-sample tests and Monte Carlo simulation.',
    })
  }

  return suggestions
}

// ─── 异常检测（用于弹窗提示）────────────────────────────────────────
type Anomaly = { code: string; severity: 'critical' | 'warning'; message: string }

function detectAnomalies(
  result: any,
  kpis: { totalReturn: number | null; maxDrawdown: number | null; totalTrades: number | null },
): Anomaly[] {
  const anomalies: Anomaly[] = []
  if (result?.status === 'failed') {
    anomalies.push({ code: 'FAILED', severity: 'critical', message: `回测执行失败 / Failed: ${String(result.error_message ?? '').split('\n')[0] || '未知错误'}` })
  }
  if (kpis.totalTrades === 0) {
    anomalies.push({ code: 'ZERO_TRADES', severity: 'critical', message: '零成交 / Zero trades — 请检查合约配置与策略信号逻辑' })
  }
  if (kpis.maxDrawdown !== null && kpis.maxDrawdown > 50) {
    anomalies.push({ code: 'EXTREME_DD', severity: 'critical', message: `极端回撤 ${kpis.maxDrawdown.toFixed(1)}% / Extreme drawdown — 请检查止损设置` })
  }
  if (kpis.totalReturn !== null && kpis.totalReturn < -40) {
    anomalies.push({ code: 'LARGE_LOSS', severity: 'critical', message: `重大亏损 ${kpis.totalReturn.toFixed(1)}% / Major loss — 策略方向或参数可能严重错误` })
  }
  return anomalies
}

type ParamGroupKey = 'basic' | 'strategy' | 'signal' | 'risk'
type DetailSectionKey = 'batchGroup' | 'executionSource' | 'runtimeParams'

type RuntimeParamItem = {
  path: string
  key: string
  value: unknown
}

const BASIC_PARAM_KEYS = new Set([
  'strategy_id', 'symbol', 'symbols', 'contract', 'start', 'end', 'start_date', 'end_date', 'timeframe', 'timeframe_minutes', 'category', 'template_id', 'version', 'description', 'initialcapital', 'initial_capital', 'position_ratio', 'initial_position',
])
const SIGNAL_PARAM_KEYS = new Set([
  'signal', 'threshold', 'long_entry_threshold', 'long_exit_threshold', 'short_entry_threshold', 'short_exit_threshold', 'lookback', 'window', 'period', 'adx_threshold', 'p2_health_threshold', 'p3_momentum_threshold', 'volume_ratio_threshold', 'cooldown_bars',
])
const RISK_PARAM_KEYS = new Set([
  'risk_per_trade', 'max_position_size', 'max_positions', 'stop_loss_pct', 'take_profit_pct', 'trailing_stop_pct', 'max_drawdown_limit', 'daily_loss_limit', 'slippage_per_contract', 'commission_per_contract', 'atr_multiplier_sl', 'atr_multiplier_tp1', 'atr_multiplier_tp2', 'atr_volatility_threshold', 'trailing_stop_trigger', 'trailing_stop_distance',
])
const PERCENT_RUNTIME_KEYS = new Set([
  'position_fraction', 'position_ratio', 'max_drawdown', 'max_drawdown_limit', 'stop_loss_pct', 'take_profit_pct', 'trailing_stop_pct', 'commission_rate', 'per_trade_stop_loss_pct', 'per_trade_take_profit_pct',
])
const MULTI_RUN_BATCH_WINDOW_SECONDS = 30

// 合约乘数映射 (品种代码 → 每手吨数)
const CONTRACT_MULTIPLIER: Record<string, number> = {
  p: 10, OI: 10, y: 10, m: 10, RM: 10, a: 10, b: 10, c: 10, cs: 10, jd: 10,
  l: 5, v: 5, pp: 5, eb: 5, eg: 5, CF: 5, SR: 5, TA: 5, MA: 5, SA: 5,
  rb: 10, hc: 10, i: 100, j: 100, jm: 60,
  cu: 5, al: 5, zn: 5, ni: 1, sn: 1, au: 1000, ag: 15,
  fu: 10, bu: 10, sp: 10, ru: 10, nr: 10, ss: 5, bc: 5,
  IF: 300, IH: 300, IC: 200, IM: 200, TF: 10000, T: 10000, TS: 20000,
}
function getContractMultiplier(symbolOrContract: string): number {
  // symbol 格式: DCE.l2605 / CZCE.CF605 / l2605 / CF605 / 12605
  const base = symbolOrContract.includes('.') ? symbolOrContract.split('.')[1] : symbolOrContract
  const code = base.replace(/\d+$/, '')
  return CONTRACT_MULTIPLIER[code] ?? 10
}

function getLeafParamKey(path: string): string {
  const normalized = path.replace(/\[(\d+)\]/g, '.$1')
  const segments = normalized.split('.').filter(Boolean)
  return segments[segments.length - 1] ?? path
}

function flattenRuntimeParams(value: unknown, prefix = ''): RuntimeParamItem[] {
  if (value == null || value === '') return []
  if (Array.isArray(value)) {
    if (value.length === 0) return []
    const containsObject = value.some((item) => item && typeof item === 'object')
    if (!containsObject) {
      return prefix ? [{ path: prefix, key: getLeafParamKey(prefix), value }] : []
    }
    return value.flatMap((item, index) => flattenRuntimeParams(item, `${prefix}[${index}]`))
  }
  if (typeof value === 'object') {
    return Object.entries(value as Record<string, unknown>).flatMap(([key, nested]) => {
      const nextPrefix = prefix ? `${prefix}.${key}` : key
      return flattenRuntimeParams(nested, nextPrefix)
    })
  }
  return prefix ? [{ path: prefix, key: getLeafParamKey(prefix), value }] : []
}

function formatParamValue(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map((item) => String(item)).join(', ')}]`
  if (typeof value === 'boolean') return value ? 'true' : 'false'
  if (value == null || value === '') return '--'
  return String(value)
}

function formatRuntimeParamValue(item: RuntimeParamItem): string {
  if (item.key === 'timeframe' || item.key === 'timeframe_minutes') {
    return formatTimeframeValue(item.value as string | number | null | undefined)
  }
  const numeric = Number(item.value)
  const normalizedKey = item.key.toLowerCase()
  const normalizedPath = item.path.toLowerCase()
  const shouldFormatAsPercent = Number.isFinite(numeric) && (
    PERCENT_RUNTIME_KEYS.has(normalizedKey) ||
    normalizedPath.includes('position_fraction') ||
    normalizedPath.includes('position_ratio') ||
    normalizedPath.includes('max_drawdown') ||
    ((normalizedKey === 'daily_loss_limit' || normalizedPath.includes('daily_loss_limit')) && Math.abs(numeric) <= 1)
  )
  if (shouldFormatAsPercent) {
    const percent = Math.abs(numeric) <= 1 ? numeric * 100 : numeric
    return `${Number(percent.toFixed(Math.abs(percent) < 1 ? 2 : 1))}%`
  }
  return formatParamValue(item.value)
}

function humanizeRuntimeParamSourceLabel(sourceLabel: string): string {
  if (sourceLabel === 'payload.params') return '本次提交参数 / payload.params'
  if (sourceLabel === 'payload') return '结果负载 / payload'
  if (sourceLabel === 'selectedBacktest') return '结果回退字段 / selectedBacktest'
  return sourceLabel
}

function getExecutionProfile(result: any): Record<string, any> | null {
  const profile = result?.execution_profile
  if (profile && typeof profile === 'object') return profile

  const strategyProfile = result?.payload?.strategy?.execution_profile
  if (strategyProfile && typeof strategyProfile === 'object') return strategyProfile

  return null
}

function buildFallbackRuntimeParams(result: any, tradeDetails: any[]) {
  const payload = result?.payload && typeof result.payload === 'object' ? result.payload : {}
  const strategy = payload?.strategy && typeof payload.strategy === 'object' ? payload.strategy : {}
  const symbols = Array.from(new Set([
    ...(Array.isArray(payload?.symbols) ? payload.symbols : []),
    ...(Array.isArray(result?.symbols) ? result.symbols : []),
    ...tradeDetails.map((trade: any) => trade.symbol).filter(Boolean),
    result?.contract,
    payload?.contract,
  ].filter(Boolean)))

  return {
    strategy_id: strategy.id ?? result?.strategy ?? result?.name ?? result?.id,
    symbols,
    start: payload?.start ?? result?.start ?? result?.tqsdk_stat?.start_date,
    end: payload?.end ?? result?.end ?? result?.tqsdk_stat?.end_date,
    timeframe: payload?.timeframe ?? result?.timeframe ?? result?.tqsdk_stat?.timeframe,
    category: payload?.category ?? strategy.category ?? result?.category,
    template_id: payload?.template_id ?? strategy.template_id ?? result?.template_id,
    version: payload?.version ?? strategy.version ?? result?.version,
    description: strategy.description ?? result?.description,
    initialCapital: result?.initialCapital ?? payload?.initialCapital ?? result?.tqsdk_stat?.init_balance,
    strategy: result?.strategy_params ?? payload?.strategy_params,
    signal: result?.signal ?? payload?.signal,
    risk: result?.risk ?? payload?.risk,
  }
}

function resolveParamGroup(path: string, key: string): ParamGroupKey {
  const normalizedPath = path.toLowerCase()
  const normalizedKey = key.toLowerCase()

  if (normalizedPath.startsWith('risk.') || normalizedPath.startsWith('parameters.risk.') || RISK_PARAM_KEYS.has(normalizedKey)) return 'risk'
  if (normalizedPath.startsWith('signal.') || normalizedPath.startsWith('parameters.signal.') || SIGNAL_PARAM_KEYS.has(normalizedKey)) return 'signal'
  if (
    normalizedPath.startsWith('strategy.') ||
    normalizedPath.startsWith('parameters.') ||
    normalizedPath.startsWith('indicators[') ||
    normalizedPath.includes('.indicators[') ||
    normalizedPath.startsWith('factors[') ||
    normalizedPath.includes('.factors[')
  ) {
    return 'strategy'
  }
  if (
    BASIC_PARAM_KEYS.has(normalizedKey) ||
    normalizedPath === 'strategy.name' ||
    normalizedPath.startsWith('strategy_id') ||
    normalizedPath.startsWith('symbols') ||
    normalizedPath.startsWith('start') ||
    normalizedPath.startsWith('end') ||
    normalizedPath.startsWith('timeframe') ||
    normalizedPath.startsWith('category') ||
    normalizedPath.startsWith('template_id') ||
    normalizedPath.startsWith('version') ||
    normalizedPath.startsWith('description')
  ) {
    return 'basic'
  }
  return 'strategy'
}

function buildGroupedRuntimeParams(result: any, tradeDetails: any[]) {
  const payloadParams = result?.payload?.params
  const payload = result?.payload && typeof result.payload === 'object' ? result.payload : null
  const source = payloadParams && typeof payloadParams === 'object' && Object.keys(payloadParams).length > 0
    ? payloadParams
    : payload && Object.keys(payload).length > 0
      ? payload
      : buildFallbackRuntimeParams(result, tradeDetails)
  const sourceLabel = payloadParams && typeof payloadParams === 'object' && Object.keys(payloadParams).length > 0
    ? 'payload.params'
    : payload && Object.keys(payload).length > 0
      ? 'payload'
      : 'selectedBacktest'

  const grouped: Record<ParamGroupKey, RuntimeParamItem[]> = {
    basic: [],
    strategy: [],
    signal: [],
    risk: [],
  }

  flattenRuntimeParams(source)
    .filter((item) => item.path !== 'params')
    .forEach((item) => {
      const group = resolveParamGroup(item.path, item.key)
      grouped[group].push(item)
    })

  return { grouped, sourceLabel }
}

function resolveResultStrategyId(result: any): string {
  return String(result?.strategy ?? result?.payload?.strategy?.id ?? result?.name ?? result?.id ?? '').trim()
}

function resolveResultStart(result: any): string {
  return String(result?.payload?.start ?? result?.tqsdk_stat?.start_date ?? '').trim()
}

function resolveResultEnd(result: any): string {
  return String(result?.payload?.end ?? result?.tqsdk_stat?.end_date ?? '').trim()
}

function resolveResultTemplateId(result: any): string {
  return String(result?.template_id ?? result?.execution_profile?.template_id ?? result?.payload?.template_id ?? result?.payload?.strategy?.template_id ?? '').trim()
}

function resolveResultInitialCapital(result: any): number | null {
  const raw = result?.initialCapital ?? result?.payload?.initialCapital ?? result?.payload?.params?.initialCapital ?? result?.payload?.params?.initial_capital ?? null
  const numeric = Number(raw)
  return Number.isFinite(numeric) ? numeric : null
}

function resolveResultSubmittedAt(result: any): number {
  const numeric = Number(result?.submitted_at ?? 0)
  return Number.isFinite(numeric) ? numeric : 0
}

function resolveResultContractLabel(result: any): string {
  const contracts = Array.isArray(result?.contracts) ? result.contracts.filter(Boolean) : []
  if (contracts.length > 0) return contracts.join(', ')
  const symbols = Array.isArray(result?.payload?.symbols) ? result.payload.symbols.filter(Boolean) : []
  if (symbols.length > 0) return symbols.join(', ')
  if (result?.payload?.contract) return String(result.payload.contract)
  if (result?.contract) return String(result.contract)
  return '--'
}

function belongToSameRunBatch(anchor: any, candidate: any): boolean {
  if (!anchor || !candidate) return false
  if (resolveResultStrategyId(anchor) !== resolveResultStrategyId(candidate)) return false

  const anchorStart = resolveResultStart(anchor)
  const candidateStart = resolveResultStart(candidate)
  if (anchorStart && candidateStart && anchorStart !== candidateStart) return false

  const anchorEnd = resolveResultEnd(anchor)
  const candidateEnd = resolveResultEnd(candidate)
  if (anchorEnd && candidateEnd && anchorEnd !== candidateEnd) return false

  const anchorTemplate = resolveResultTemplateId(anchor)
  const candidateTemplate = resolveResultTemplateId(candidate)
  if (anchorTemplate && candidateTemplate && anchorTemplate !== candidateTemplate) return false

  const anchorCapital = resolveResultInitialCapital(anchor)
  const candidateCapital = resolveResultInitialCapital(candidate)
  if (anchorCapital != null && candidateCapital != null && Math.abs(anchorCapital - candidateCapital) > 0.01) return false

  const anchorSubmittedAt = resolveResultSubmittedAt(anchor)
  const candidateSubmittedAt = resolveResultSubmittedAt(candidate)
  if (anchorSubmittedAt > 0 && candidateSubmittedAt > 0 && Math.abs(anchorSubmittedAt - candidateSubmittedAt) > MULTI_RUN_BATCH_WINDOW_SECONDS) return false

  return true
}

export default function BacktestDetailPage() {
  const [selectedBacktest, setSelectedBacktest] = useState<any | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(new Date())
  const [equityCurveData, setEquityCurveData] = useState<any[]>([])
  const [apiError, setApiError] = useState<string | null>(null)
  const [backtests, setBacktests] = useState<any[]>([])
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [isBatchDeleting, setIsBatchDeleting] = useState(false)
  const [computedKPIs, setComputedKPIs] = useState<{ totalReturn: number | null; maxDrawdown: number | null; sharpeRatio: number | null; winRate: number | null; totalTrades: number | null }>({
    totalReturn: null, maxDrawdown: null, sharpeRatio: null, winRate: null, totalTrades: null,
  })
  // 进度表：task_id -> { progress: 0-100, current_date: string }
  const [progressMap, setProgressMap] = useState<Record<string, { progress: number; current_date: string | null }>>({})
  // ─── 新增状态 ──────────────────────────────────────────────────────
  const [anomalyModal, setAnomalyModal] = useState<Anomaly[] | null>(null)
  const [optimizationSuggestions, setOptimizationSuggestions] = useState<Suggestion[]>([])
  const [cancellingId, setCancellingId] = useState<string | null>(null)
  const [runtimeSectionOpen, setRuntimeSectionOpen] = useState<Record<ParamGroupKey, boolean>>({
    basic: false,
    strategy: false,
    signal: false,
    risk: false,
  })
  const [detailSectionOpen, setDetailSectionOpen] = useState<Record<DetailSectionKey, boolean>>({
    batchGroup: false,
    executionSource: false,
    runtimeParams: false,
  })
  const computeKPIs = (equity: any[], trades: any[]) => {
    if (!Array.isArray(equity) || equity.length < 2) {
      setComputedKPIs({ totalReturn: null, maxDrawdown: null, sharpeRatio: null, winRate: null, totalTrades: null })
      return
    }
    const first = equity[0].nav ?? equity[0].equity ?? equity[0].value ?? 0
    const last = equity[equity.length - 1].nav ?? equity[equity.length - 1].equity ?? equity[equity.length - 1].value ?? 0
    const totalReturn = first > 0 ? ((last - first) / first) * 100 : null
    let peak = first, maxDD = 0
    for (const p of equity) {
      const v = p.nav ?? p.equity ?? p.value ?? 0
      if (v > peak) peak = v
      const dd = peak > 0 ? (peak - v) / peak * 100 : 0
      if (dd > maxDD) maxDD = dd
    }
    const navs = equity.map(p => p.nav ?? p.equity ?? p.value ?? 0)
    let sharpeRatio: number | null = null
    if (navs.length > 10) {
      const rets = navs.slice(1).map((v, i) => navs[i] > 0 ? (v - navs[i]) / navs[i] : 0)
      const mean = rets.reduce((a, b) => a + b, 0) / rets.length
      const variance = rets.reduce((a, b) => a + (b - mean) ** 2, 0) / (rets.length - 1)
      const std = Math.sqrt(variance)
      if (std > 0) sharpeRatio = parseFloat((mean / std * Math.sqrt(252)).toFixed(2))
    }
    const closedTrades = Array.isArray(trades) ? trades.filter(t => t.profit != null) : []
    const winRate = closedTrades.length > 0
      ? parseFloat((closedTrades.filter(t => t.profit > 0).length / closedTrades.length * 100).toFixed(1))
      : null
    const totalTrades = closedTrades.length > 0 ? closedTrades.length : (Array.isArray(trades) ? trades.length : null)
    setComputedKPIs({ totalReturn, maxDrawdown: maxDD, sharpeRatio, winRate, totalTrades: totalTrades || null })
  }

  const load = async () => {
    setIsLoading(true)
    setApiError(null)
    try {
      const [results] = await Promise.allSettled([api.getResults()])
      if (results.status === 'fulfilled') {
        setBacktests(Array.isArray(results.value) ? results.value : [])
      } else {
        setApiError(api.friendlyError ? api.friendlyError(results.reason) : String(results.reason))
      }
      const now = new Date()
      setLastUpdate(now)
      try { window.dispatchEvent(new CustomEvent('backtest:lastUpdate', { detail: now.toISOString() })) } catch (_) {}
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    load()
    const onRefresh = () => load()
    window.addEventListener('backtest:refresh', onRefresh)
    return () => window.removeEventListener('backtest:refresh', onRefresh)
  }, [])

  // 进度轮询：每 2 秒拉取所有 running 任务的进度
  useEffect(() => {
    const pollProgress = async () => {
      const runningTasks = backtests.filter((b: any) => b.status === 'running' || b.status === 'submitted' || b.status === 'pending')
      if (runningTasks.length === 0) return
      const updates: Record<string, { progress: number; current_date: string | null }> = {}
      let anyCompleted = false
      await Promise.allSettled(
        runningTasks.map(async (b: any) => {
          try {
            const p = await api.getProgress(b.id)
            updates[b.id] = { progress: p.progress ?? 0, current_date: p.current_date ?? null }
            if (p.status === 'completed') anyCompleted = true
          } catch (_) {}
        })
      )
      setProgressMap(prev => ({ ...prev, ...updates }))
      if (anyCompleted) load()
    }
    if (backtests.length === 0) return
    const timer = setInterval(pollProgress, 2000)
    return () => clearInterval(timer)
  }, [backtests])

  // 导出报告
  const handleExportReport = async () => {
    const bt = selectedBacktest
    if (!bt) { alert('请先点击一条回测记录'); return }
    const strategyName = bt.strategy ?? (bt as any).payload?.strategy?.id ?? bt.name ?? bt.id
    const executionProfile = getExecutionProfile(bt)
    // 允许本地回测（local engine）和正式回测都可导出报告
    const hasReport = !!(bt.report_path) ||
      executionProfile?.executed_formal === true ||
      executionProfile?.executed_mode === 'local'
    if (!hasReport) {
      alert('当前结果没有可下载的报告，请先执行回测后再导出')
      return
    }

    try {
      await api.downloadBacktestReport(String(bt.id ?? bt.task_id), String(strategyName))
    } catch (err) {
      alert(`报告导出失败：${api.friendlyError(err)}`)
    }
  }

  // 使用集中式 API 工具

  const [tradeDetails, setTradeDetails] = useState<any[]>([])

  const fetchBacktestDetails = async (id: string) => {
    try {
      setIsLoading(true)
      setApiError(null)
      setOptimizationSuggestions([])
      setAnomalyModal(null)
      setRuntimeSectionOpen({ basic: false, strategy: false, signal: false, risk: false })
      setDetailSectionOpen({
        batchGroup: false,
        executionSource: false,
        runtimeParams: false,
      })
      const data = await api.getResultById(id)
      setSelectedBacktest(data || null)
      const [tradesRes, equityRes] = await Promise.allSettled([
        api.getResultTrades(id),
        api.getResultEquity(id),
      ])
      const tradesData = tradesRes.status === 'fulfilled' ? tradesRes.value : null
      const tradesArr = Array.isArray(tradesData) ? tradesData :
        Array.isArray(data?.trades) ? data.trades : []
      setTradeDetails(tradesArr)
      const equityRaw = equityRes.status === 'fulfilled' ? equityRes.value : null
      const equityArr = Array.isArray(equityRaw) ? equityRaw :
        Array.isArray(data?.equity_curve) ? data.equity_curve : []
      setEquityCurveData(equityArr)

      // 从 equity_curve 和 trades 计算 KPI
      computeKPIs(equityArr, tradesArr)

      // ─── 异常检测（回测完成后立即扫描）───────────────────────────
      // 注：computeKPIs 是异步设置，这里直接计算临时 kpi 用于检测
      const tmpKPIs = (() => {
        if (!Array.isArray(equityArr) || equityArr.length < 2) return { totalReturn: null, maxDrawdown: null, totalTrades: tradesArr.length || 0 }
        const first = equityArr[0].nav ?? equityArr[0].equity ?? equityArr[0].value ?? 0
        const last = equityArr[equityArr.length - 1].nav ?? equityArr[equityArr.length - 1].equity ?? equityArr[equityArr.length - 1].value ?? 0
        const totalReturn = first > 0 ? ((last - first) / first) * 100 : null
        let peak = first, maxDD = 0
        for (const p of equityArr) {
          const v = p.nav ?? p.equity ?? p.value ?? 0
          if (v > peak) peak = v
          const dd = peak > 0 ? (peak - v) / peak * 100 : 0
          if (dd > maxDD) maxDD = dd
        }
        const closedTrades = tradesArr.filter((t: any) => t.profit != null)
        const winRate = closedTrades.length > 0 ? closedTrades.filter((t: any) => t.profit > 0).length / closedTrades.length * 100 : null
        const totalTrades = closedTrades.length || tradesArr.length || data?.totalTrades || data?.total_trades || 0
        const navs = equityArr.map((p: any) => p.nav ?? p.equity ?? p.value ?? 0)
        let sharpeRatio: number | null = null
        if (navs.length > 10) {
          const rets = navs.slice(1).map((v: number, i: number) => navs[i] > 0 ? (v - navs[i]) / navs[i] : 0)
          const mean = rets.reduce((a: number, b: number) => a + b, 0) / rets.length
          const variance = rets.reduce((a: number, b: number) => a + (b - mean) ** 2, 0) / (rets.length - 1)
          const std = Math.sqrt(variance)
          if (std > 0) sharpeRatio = parseFloat((mean / std * Math.sqrt(252)).toFixed(2))
        }
        return { totalReturn, maxDrawdown: maxDD, sharpeRatio, winRate, totalTrades }
      })()

      const anomalies = detectAnomalies(data, tmpKPIs)
      if (anomalies.length > 0) {
        setAnomalyModal(anomalies)
      }

      // 生成优化建议（仅对 completed 状态有意义）
      if (data?.status === 'completed' || data?.status === 'done' || data?.status === 'failed') {
        const suggestions = generateOptimizationSuggestions(data, tmpKPIs as any, tradesArr)
        setOptimizationSuggestions(suggestions)
      }

      setLastUpdate(new Date())
      try { window.dispatchEvent(new CustomEvent('backtest:lastUpdate', { detail: new Date().toISOString() })) } catch (e) {}
    } catch (err) {
      console.error(err)
      setApiError(String(err))
    } finally {
      setIsLoading(false)
    }
  }

  const handleRefresh = () => { load() }

  const handleCancelResult = async (taskId: string) => {
    setCancellingId(taskId)
    try {
      await api.cancelBacktest(taskId)
      await load()
      if (selectedBacktest?.id) {
        await fetchBacktestDetails(selectedBacktest.id)
      }
    } catch (err) {
      setApiError(api.friendlyError(err))
    } finally {
      setCancellingId(null)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-white/20 text-white"
      case "running":
        return "bg-orange-500/20 text-orange-500"
      case "failed":
        return "bg-red-500/20 text-red-500"
      default:
        return "bg-neutral-500/20 text-neutral-300"
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case "completed":
        return "已完成"
      case "running":
        return "运行中"
      case "failed":
        return "失败"
      default:
        return status
    }
  }

  const formatErrorMessage = (raw: any) => {
    if (!raw) return '--'
    const msg = String(raw)
    const m = msg.match(/RuntimeError:\s*([^\n]+)/)
    if (m?.[1]) return m[1]
    return msg.split('\n')[0] || '--'
  }

  // KPI 数据：优先用从 equity_curve 计算的值，其次用选中回测的字段
  const kpiSource = selectedBacktest ?? (backtests.length > 0 ? backtests[0] : null)
  const kpiTotalReturn = computedKPIs.totalReturn ?? kpiSource?.totalReturn ?? kpiSource?.result?.totalReturn ?? null
  const kpiMaxDrawdown = computedKPIs.maxDrawdown ?? kpiSource?.maxDrawdown ?? kpiSource?.result?.maxDrawdown ?? null
  const kpiSharpe = computedKPIs.sharpeRatio ?? kpiSource?.sharpeRatio ?? kpiSource?.result?.sharpeRatio ?? null
  const kpiWinRate = computedKPIs.winRate ?? kpiSource?.winRate ?? kpiSource?.result?.winRate ?? null
  const kpiAnnualReturn = selectedBacktest?.annualReturn ?? kpiSource?.annualReturn ?? kpiSource?.result?.annualReturn ?? null
  const kpiTotalTrades = computedKPIs.totalTrades ?? selectedBacktest?.totalTrades ?? kpiSource?.totalTrades ?? kpiSource?.result?.totalTrades ?? (tradeDetails.length > 0 ? tradeDetails.length : null)
  const runtimeParamView = selectedBacktest ? buildGroupedRuntimeParams(selectedBacktest, tradeDetails) : null
  const executionProfile = selectedBacktest ? getExecutionProfile(selectedBacktest) : null
  const selectedBatchResults = selectedBacktest
    ? (() => {
        const selectedId = String(selectedBacktest.id ?? selectedBacktest.task_id ?? '')
        const batchItems = [
          selectedBacktest,
          ...backtests.filter((item) => String(item.id ?? item.task_id ?? '') !== selectedId && belongToSameRunBatch(selectedBacktest, item)),
        ]
        const deduped = Array.from(new Map(batchItems.map((item) => [String(item.id ?? item.task_id ?? `${resolveResultStrategyId(item)}-${resolveResultContractLabel(item)}`), item])).values())
        return deduped.sort((left, right) => {
          const contractCompare = resolveResultContractLabel(left).localeCompare(resolveResultContractLabel(right), 'zh-CN')
          if (contractCompare !== 0) return contractCompare
          return resolveResultSubmittedAt(right) - resolveResultSubmittedAt(left)
        })
      })()
    : []
  const selectedBatchSummary = selectedBatchResults.reduce(
    (summary, item) => {
      summary.total += 1
      if (item.status === 'completed' || item.status === 'done') summary.completed += 1
      else if (item.status === 'running' || item.status === 'submitted' || item.status === 'pending') summary.running += 1
      else if (item.status === 'failed') summary.failed += 1
      else summary.other += 1
      return summary
    },
    { total: 0, completed: 0, running: 0, failed: 0, other: 0 },
  )

  const toggleRuntimeSection = (group: ParamGroupKey) => {
    setRuntimeSectionOpen((prev) => ({ ...prev, [group]: !prev[group] }))
  }

  const toggleDetailSection = (section: DetailSectionKey) => {
    setDetailSectionOpen((prev) => ({ ...prev, [section]: !prev[section] }))
  }

  const renderDetailSectionHeader = (section: DetailSectionKey, title: string, extra?: string) => {
    const isOpen = detailSectionOpen[section]
    return (
      <button type="button" className="w-full flex items-center justify-between gap-3 text-left" onClick={() => toggleDetailSection(section)}>
        <div>
          <p className="text-sm font-medium text-neutral-300 tracking-wider">{title}</p>
          {extra ? <p className="text-[10px] text-neutral-600 mt-0.5">{extra}</p> : null}
        </div>
        {isOpen ? <ChevronDown className="w-4 h-4 text-neutral-500" /> : <ChevronRight className="w-4 h-4 text-neutral-500" />}
      </button>
    )
  }

  const renderParamGroup = (group: ParamGroupKey, titleZh: string, titleEn: string, items: RuntimeParamItem[], accentClass: string) => {
    const isOpen = runtimeSectionOpen[group]
    return (
      <div className="rounded-lg border border-neutral-700/60 bg-neutral-800/50 p-2.5 space-y-2.5">
        <button type="button" className="w-full flex items-center justify-between gap-3 text-left" onClick={() => toggleRuntimeSection(group)}>
          <div className="flex items-center gap-3 flex-wrap">
            <p className={`text-xs tracking-wider ${accentClass}`}>{titleZh} / {titleEn}</p>
            <span className="text-[10px] text-neutral-600">{items.length} 项</span>
          </div>
          {isOpen ? <ChevronDown className="w-4 h-4 text-neutral-500" /> : <ChevronRight className="w-4 h-4 text-neutral-500" />}
        </button>
        {isOpen && (
          items.length === 0 ? (
            <p className="text-xs text-neutral-600">当前回测结果未返回该分组参数</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
              {items.map((item) => {
                const meta = resolveFieldLabel(item.path, item.key)
                const factorIndexMatch = item.path.match(/([a-zA-Z_]+)\[(\d+)\]/i)
                const sectionLabel = factorIndexMatch?.[1]?.toLowerCase() === 'indicators' ? '指标' : '因子'
                return (
                  <div key={item.path} className="rounded-md border border-neutral-700/50 bg-neutral-900/80 p-2.5">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="text-xs text-neutral-300">
                        {meta.zh}
                        {meta.en ? <span className="text-neutral-500"> / {meta.en}</span> : null}
                        {meta.unit ? <span className="text-neutral-500"> ({meta.unit})</span> : null}
                      </p>
                      {factorIndexMatch && (
                        <span className="text-[10px] px-2 py-0.5 rounded bg-neutral-700 text-neutral-300">
                          {sectionLabel} {Number(factorIndexMatch[2]) + 1}
                        </span>
                      )}
                    </div>
                    <p className="text-[10px] text-neutral-600 font-mono mt-0.5 break-all">{item.path}</p>
                    <p className="text-[10px] text-neutral-500 mt-0.5 leading-relaxed">{meta.desc}</p>
                    <p className="text-[13px] text-white font-mono mt-1.5 break-all leading-relaxed">{formatRuntimeParamValue(item)}</p>
                  </div>
                )
              })}
            </div>
          )
        )}
      </div>
    )
  }

  return (
    <div className="p-5 space-y-5">
      {apiError && (
        <div className="text-sm text-red-400 bg-neutral-900 border border-red-800 p-3 rounded">
          API 错误: {apiError}
        </div>
      )}

      {/* ─── 异常检测弹窗 ──────────────────────────────────────────── */}
      {anomalyModal && anomalyModal.length > 0 && (
        <div className="fixed inset-0 bg-black/75 z-50 flex items-center justify-center p-4" onClick={() => setAnomalyModal(null)}>
          <div className="bg-neutral-900 border border-red-600/60 rounded-xl w-full max-w-xl shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center gap-3 px-5 py-4 border-b border-neutral-700">
              <AlertTriangle className="w-6 h-6 text-red-400 flex-shrink-0" />
              <div>
                <p className="text-sm font-bold text-red-300">回测异常告警 / Backtest Anomaly Alert</p>
                <p className="text-xs text-neutral-500 mt-0.5">以下问题需要关注，请检查策略配置</p>
              </div>
              <button onClick={() => setAnomalyModal(null)} className="ml-auto text-neutral-500 hover:text-neutral-300">✕</button>
            </div>
            <div className="p-5 space-y-3">
              {anomalyModal.map((a, i) => (
                <div key={i} className={`rounded-lg p-3 border flex items-start gap-3 ${a.severity === 'critical' ? 'bg-red-900/20 border-red-700/50' : 'bg-amber-900/20 border-amber-700/50'}`}>
                  <span className="text-lg flex-shrink-0">{a.severity === 'critical' ? '🚨' : '⚠️'}</span>
                  <div>
                    <p className={`text-sm font-semibold ${a.severity === 'critical' ? 'text-red-300' : 'text-amber-300'}`}>{a.code}</p>
                    <p className="text-xs text-neutral-300 mt-0.5">{a.message}</p>
                  </div>
                </div>
              ))}
            </div>
            <div className="px-5 pb-4">
              <Button className="w-full bg-red-700 hover:bg-red-800 text-white" onClick={() => { setAnomalyModal(null); document.getElementById('optimization-suggestions')?.scrollIntoView({ behavior: 'smooth', block: 'start' }) }}>
                查看调优建议 / View Optimization Hints
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* 头部 */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wider">回测详情</h1>
          <p className="text-sm text-neutral-400">点击回测记录查看结果、权益曲线和交易明细</p>
        </div>
        <div className="flex gap-2">
          <Button className="bg-orange-500 hover:bg-orange-600 text-white" onClick={handleExportReport} disabled={!selectedBacktest}>导出报告</Button>
        </div>
      </div>

      {/* 更新时间戳 */}
      <div className="text-xs text-neutral-500 text-right">
        最后更新: {lastUpdate.toLocaleString("zh-CN")}
      </div>

      {/* 选中回测详情面板 */}
      {selectedBacktest && (
        <Card className="bg-neutral-900 border-orange-500/40">
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <div>
                <p className="text-orange-400 font-semibold text-sm tracking-wider">
                  {selectedBacktest?.name ?? selectedBacktest?.strategy ?? selectedBacktest?.payload?.strategy?.id ?? selectedBacktest?.id?.slice(0, 16) ?? '--'}
                </p>
                <p className="text-neutral-500 text-xs font-mono mt-0.5">{selectedBacktest?.payload?.start ?? ''}{selectedBacktest?.payload?.start ? ' ~ ' : ''}{selectedBacktest?.payload?.end ?? ''}</p>
              </div>
              <div className="flex items-center gap-2">
                <Badge className={getStatusColor(selectedBacktest.status)}>
                  {getStatusText(selectedBacktest.status)}
                </Badge>
                {(selectedBacktest.status === 'running' || selectedBacktest.status === 'submitted' || selectedBacktest.status === 'pending') && (
                  <Button
                    className="bg-red-700 hover:bg-red-600 text-white h-8 px-3"
                    disabled={cancellingId === selectedBacktest.id}
                    onClick={() => handleCancelResult(selectedBacktest.id)}
                  >
                    <Square className="w-3.5 h-3.5 mr-1.5" />{cancellingId === selectedBacktest.id ? '终止中...' : '终止'}
                  </Button>
                )}
              </div>
            </div>
            {/* 运行中进度条 */}
            {(selectedBacktest.status === 'running' || selectedBacktest.status === 'submitted' || selectedBacktest.status === 'pending') && (
              <div className="mb-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-orange-400 font-mono">
                    回测进度 {progressMap[selectedBacktest.id]?.progress ?? 0}%
                  </span>
                  {progressMap[selectedBacktest.id]?.current_date && (
                    <span className="text-xs text-neutral-400">当前日期：{progressMap[selectedBacktest.id]?.current_date}</span>
                  )}
                </div>
                <div className="h-2 w-full bg-neutral-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-orange-500 rounded-full transition-all duration-500"
                    style={{ width: `${progressMap[selectedBacktest.id]?.progress ?? 0}%` }}
                  />
                </div>
              </div>
            )}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-2">
              <div className="bg-neutral-800 rounded p-2">
                <p className="text-neutral-500 text-xs mb-0.5">合约</p>
                <p className="text-white text-sm font-mono">
                  {tradeDetails.length > 0
                    ? [...new Set(tradeDetails.map((t: any) => t.symbol).filter(Boolean))].join(', ')
                    : selectedBacktest?.contract ?? selectedBacktest?.payload?.contract ?? '--'}
                </p>
              </div>
              <div className="bg-neutral-800 rounded p-2">
                <p className="text-neutral-500 text-xs mb-0.5">回测周期</p>
                <p className="text-white text-xs font-mono">
                  {(selectedBacktest as any)?.payload?.start ?? (selectedBacktest as any)?.tqsdk_stat?.start_date ?? '--'}
                  {' → '}
                  {(selectedBacktest as any)?.payload?.end ?? (selectedBacktest as any)?.tqsdk_stat?.end_date ?? '--'}
                </p>
              </div>
              <div className="bg-neutral-800 rounded p-2">
                <p className="text-neutral-500 text-xs mb-0.5">初始资金</p>
                <p className="text-white text-sm font-mono">
                  {selectedBacktest?.initialCapital != null
                    ? '¥ ' + Number(selectedBacktest.initialCapital).toLocaleString()
                    : selectedBacktest?.payload?.params?.initialCapital != null
                    ? '¥ ' + Number(selectedBacktest.payload.params.initialCapital).toLocaleString()
                    : '--'}
                </p>
              </div>
              <div className="bg-neutral-800 rounded p-2">
                <p className="text-neutral-500 text-xs mb-0.5">最终资金</p>
                <p className={`text-sm font-mono ${
                  selectedBacktest?.finalCapital != null && selectedBacktest?.initialCapital != null
                    ? (selectedBacktest.finalCapital >= selectedBacktest.initialCapital ? 'text-red-400' : 'text-green-400')
                    : 'text-white'
                }`}>
                  {selectedBacktest?.finalCapital != null ? '¥ ' + Number(selectedBacktest.finalCapital).toLocaleString() : '--'}
                </p>
              </div>
            </div>
            {executionProfile && (
              <div className="mb-2 rounded-lg border border-neutral-700/60 bg-neutral-800/50 p-2.5 space-y-2">
                {renderDetailSectionHeader('executionSource', '执行来源 / Execution Source', executionProfile.executed_label ?? executionProfile.label ?? '未知来源')}
                {detailSectionOpen.executionSource && (
                  <>
                    <div className="flex items-start justify-between gap-3 flex-wrap">
                      <div>
                        <div className="flex items-center gap-2 mt-1 flex-wrap">
                          <span className={`text-xs px-2 py-0.5 rounded-full border ${executionProfile.executed_formal ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300' : 'border-amber-500/40 bg-amber-500/10 text-amber-300'}`}>
                            {executionProfile.executed_label ?? executionProfile.label ?? '未知来源'}
                          </span>
                          {(() => {
                            const sk = (selectedBacktest as any)?.source_kind ?? (selectedBacktest as any)?.payload?.source_kind
                            const src = (selectedBacktest as any)?.source
                            if (!sk && !src) return null
                            const isRealLocal = src === 'local_backtest_engine'
                            const isContinuous = sk === 'continuous' || sk === 'api'
                            return (
                              <span className={`text-xs px-2 py-0.5 rounded-full border font-mono ${isRealLocal && isContinuous ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300' : isRealLocal ? 'border-blue-500/40 bg-blue-500/10 text-blue-300' : 'border-neutral-600 bg-neutral-800 text-neutral-400'}`}>
                                {isRealLocal ? '✓ 真实本地回测' : '兼容模式'}{sk ? ` · ${sk}` : ''}
                              </span>
                            )
                          })()}
                          <span className={`text-xs px-2 py-0.5 rounded-full border ${executionProfile.formal_supported ? 'border-cyan-500/40 bg-cyan-500/10 text-cyan-300' : 'border-neutral-600 bg-neutral-800 text-neutral-300'}`}>
                            {executionProfile.formal_supported ? '该策略具备正式引擎条件' : '该策略当前不具备正式引擎条件'}
                          </span>
                        </div>
                      </div>
                      {executionProfile.template_id ? (
                        <span className="text-xs text-neutral-400 font-mono">template_id: {executionProfile.template_id}</span>
                      ) : null}
                    </div>
                    <p className="text-xs text-neutral-300 leading-relaxed">{executionProfile.executed_reason ?? executionProfile.reason ?? '--'}</p>
                    {selectedBacktest?.report_path ? (
                      <p className="text-[11px] text-neutral-500 font-mono break-all">report_path: {selectedBacktest.report_path}</p>
                    ) : (selectedBacktest as any)?.source === 'local_backtest_engine' ? (
                      <p className="text-[11px] text-emerald-600">✓ 本地回测报告存于内存，可直接导出。</p>
                    ) : (
                      <p className="text-[11px] text-neutral-500">当前结果未生成正式报告文件。</p>
                    )}
                    {(() => {
                      const hash = (selectedBacktest as any)?.formal_report?.yaml_snapshot_hash
                        ?? (selectedBacktest as any)?.formal_report?.job?.yaml_snapshot_hash
                      return hash && typeof hash === 'string' && hash.length === 64 ? (
                        <p className="text-[11px] text-neutral-500 font-mono break-all">yaml_hash: {hash.slice(0, 16)}…</p>
                      ) : null
                    })()}
                    {Array.isArray(executionProfile.evidence) && executionProfile.evidence.length > 0 && (
                      <div className="space-y-1">
                        <p className="text-[11px] text-neutral-500 tracking-wider">证据链 / Evidence</p>
                        {executionProfile.evidence.map((item: string, index: number) => (
                          <p key={`${index}-${item}`} className="text-[11px] text-neutral-400 leading-relaxed">{index + 1}. {item}</p>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
            {runtimeParamView && (
              <div className="border-t border-neutral-700 pt-2.5">
                <div className="space-y-2.5">
                  {renderDetailSectionHeader('runtimeParams', '运行参数 / Runtime Parameters', `来源: ${humanizeRuntimeParamSourceLabel(runtimeParamView.sourceLabel)}`)}
                  {detailSectionOpen.runtimeParams && (
                    <div className="space-y-2.5">
                      {renderParamGroup('basic', '基本信息', 'Basic Info', runtimeParamView.grouped.basic, 'text-neutral-300')}
                      {renderParamGroup('strategy', '策略参数', 'Strategy Params', runtimeParamView.grouped.strategy, 'text-orange-300')}
                      {renderParamGroup('signal', '信号参数', 'Signal Params', runtimeParamView.grouped.signal, 'text-purple-300')}
                      {renderParamGroup('risk', '风控参数', 'Risk Params', runtimeParamView.grouped.risk, 'text-amber-300')}
                    </div>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {selectedBacktest && selectedBatchResults.length > 1 && (
        <Card className="bg-neutral-900 border-cyan-600/30">
          <CardHeader className="px-4 pt-4 pb-2">
            {renderDetailSectionHeader('batchGroup', `同批多品种任务 / Multi-Contract Batch (${selectedBatchSummary.total})`, `完成 ${selectedBatchSummary.completed} / 运行中 ${selectedBatchSummary.running} / 失败 ${selectedBatchSummary.failed}`)}
          </CardHeader>
          {detailSectionOpen.batchGroup && (
            <CardContent className="px-4 pb-4 pt-0 space-y-3">
              <div className="flex flex-wrap gap-2">
                <span className="text-xs px-2 py-1 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">策略 {resolveResultStrategyId(selectedBacktest)}</span>
                <span className="text-xs px-2 py-1 rounded-full bg-neutral-800 text-neutral-300 border border-neutral-700">区间 {resolveResultStart(selectedBacktest)} ~ {resolveResultEnd(selectedBacktest)}</span>
                <span className="text-xs px-2 py-1 rounded-full bg-neutral-800 text-neutral-300 border border-neutral-700">模板 {resolveResultTemplateId(selectedBacktest) || '--'}</span>
              </div>
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-2.5">
                {selectedBatchResults.map((item) => {
                  const itemId = String(item.id ?? item.task_id ?? '')
                  const isCurrent = itemId === String(selectedBacktest.id ?? selectedBacktest.task_id ?? '')
                  const isRunning = item.status === 'running' || item.status === 'submitted' || item.status === 'pending'
                  const progress = progressMap[itemId] ?? { progress: 0, current_date: null }
                  return (
                    <div key={itemId} className={`rounded-lg border p-2.5 space-y-2.5 ${isCurrent ? 'border-cyan-500/50 bg-cyan-500/10' : 'border-neutral-700/60 bg-neutral-800/50'}`}>
                      <div className="flex items-start justify-between gap-3 flex-wrap">
                        <div>
                          <p className="text-sm text-white font-mono">{resolveResultContractLabel(item)}</p>
                          <p className="text-[11px] text-neutral-500 mt-1">提交时间 {item.submitted_at ? new Date(item.submitted_at * 1000).toLocaleString('zh-CN') : '--'}</p>
                        </div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <Badge className={getStatusColor(item.status)}>{getStatusText(item.status)}</Badge>
                          {isCurrent ? <span className="text-[11px] px-2 py-0.5 rounded-full bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">当前查看</span> : null}
                        </div>
                      </div>
                      {isRunning && (
                        <div>
                          <div className="flex items-center justify-between mb-1 text-xs">
                            <span className="text-orange-300 font-mono">进度 {progress.progress}%</span>
                            <span className="text-neutral-500">{progress.current_date ? `当前日期 ${progress.current_date}` : '等待后端返回进度'}</span>
                          </div>
                          <div className="h-2 w-full bg-neutral-700 rounded-full overflow-hidden">
                            <div className="h-full bg-orange-500 rounded-full transition-all duration-500" style={{ width: `${progress.progress}%` }} />
                          </div>
                        </div>
                      )}
                      <div className="grid grid-cols-2 gap-3 text-xs">
                        <div className="rounded-md bg-neutral-900/70 border border-neutral-700/50 p-2">
                          <p className="text-neutral-500 mb-1">收益率</p>
                          <p className={`font-mono ${(item.totalReturn ?? 0) >= 0 ? 'text-red-400' : 'text-green-400'}`}>{item.totalReturn != null ? `${item.totalReturn >= 0 ? '+' : ''}${Number(item.totalReturn).toFixed(1)}%` : '--'}</p>
                        </div>
                        <div className="rounded-md bg-neutral-900/70 border border-neutral-700/50 p-2">
                          <p className="text-neutral-500 mb-1">最大回撤</p>
                          <p className="font-mono text-green-400">{item.maxDrawdown != null ? `-${Math.abs(Number(item.maxDrawdown)).toFixed(1)}%` : '--'}</p>
                        </div>
                      </div>
                      <div className="flex gap-2 flex-wrap">
                        {!isCurrent && (
                          <Button className="bg-cyan-700 hover:bg-cyan-600 text-white h-8 px-3" onClick={() => fetchBacktestDetails(itemId)}>
                            查看此合约
                          </Button>
                        )}
                        {isRunning && (
                          <Button className="bg-red-700 hover:bg-red-600 text-white h-8 px-3" disabled={cancellingId === itemId} onClick={() => handleCancelResult(itemId)}>
                            {cancellingId === itemId ? '终止中...' : '终止'}
                          </Button>
                        )}
                        {item.status === 'failed' && item.error_message ? (
                          <span className="text-[11px] text-red-300 leading-relaxed">{formatErrorMessage(item.error_message)}</span>
                        ) : null}
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          )}
        </Card>
      )}

      {/* 关键指标统计 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader className="px-4 pt-4 pb-2">
          <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">关键指标 / KPI Summary</CardTitle>
        </CardHeader>
        <CardContent className="px-4 pb-4 pt-0">
          <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-6 gap-3 items-stretch">
            <Card className="bg-neutral-900 border-neutral-700 h-full">
              <CardContent className="p-3 h-full">
                <div className="flex items-center justify-between h-full gap-2">
                  <div className="space-y-0.5">
                    <p className="text-xs text-neutral-400 tracking-wider">总收益率</p>
                    <p className={`text-xl leading-tight font-bold font-mono ${kpiTotalReturn == null ? 'text-neutral-500' : (kpiTotalReturn >= 0 ? 'text-red-400' : 'text-green-400')}`}>
                      {kpiTotalReturn != null ? `${kpiTotalReturn >= 0 ? '+' : ''}${Number(kpiTotalReturn).toFixed(1)}%` : isLoading ? '…' : '--'}
                    </p>
                  </div>
                  <TrendingUp className={`w-6 h-6 flex-shrink-0 ${kpiTotalReturn != null && kpiTotalReturn >= 0 ? 'text-red-400' : 'text-neutral-600'}`} />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-neutral-900 border-neutral-700 h-full">
              <CardContent className="p-3 h-full">
                <div className="flex items-center justify-between h-full gap-2">
                  <div className="space-y-0.5">
                    <p className="text-xs text-neutral-400 tracking-wider">最大回撤</p>
                    <p className={`text-xl leading-tight font-bold font-mono ${kpiMaxDrawdown == null ? 'text-neutral-500' : 'text-green-400'}`}>
                      {kpiMaxDrawdown != null ? `-${Math.abs(Number(kpiMaxDrawdown)).toFixed(1)}%` : isLoading ? '…' : '--'}
                    </p>
                  </div>
                  <TrendingDown className={`w-6 h-6 flex-shrink-0 ${kpiMaxDrawdown != null ? 'text-green-400' : 'text-neutral-600'}`} />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-neutral-900 border-neutral-700 h-full">
              <CardContent className="p-3 h-full">
                <div className="flex items-center justify-between h-full gap-2">
                  <div className="space-y-0.5">
                    <p className="text-xs text-neutral-400 tracking-wider">夏普比率</p>
                    <p className={`text-xl leading-tight font-bold font-mono ${kpiSharpe == null ? 'text-neutral-500' : 'text-white'}`}>
                      {kpiSharpe != null ? Number(kpiSharpe).toFixed(2) : isLoading ? '…' : '--'}
                    </p>
                  </div>
                  <BarChart3 className={`w-6 h-6 flex-shrink-0 ${kpiSharpe != null ? 'text-white' : 'text-neutral-600'}`} />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-neutral-900 border-neutral-700 h-full">
              <CardContent className="p-3 h-full">
                <div className="flex items-center justify-between h-full gap-2">
                  <div className="space-y-0.5">
                    <p className="text-xs text-neutral-400 tracking-wider">胜率</p>
                    <p className={`text-xl leading-tight font-bold font-mono ${kpiWinRate == null ? 'text-neutral-500' : 'text-orange-500'}`}>
                      {kpiWinRate != null ? `${kpiWinRate}%` : isLoading ? '…' : '--'}
                    </p>
                  </div>
                  <Percent className={`w-6 h-6 flex-shrink-0 ${kpiWinRate != null ? 'text-orange-500' : 'text-neutral-600'}`} />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-neutral-900 border-neutral-700 h-full">
              <CardContent className="p-3 h-full">
                <div className="flex items-center justify-between h-full gap-2">
                  <div className="space-y-0.5">
                    <p className="text-xs text-neutral-400 tracking-wider">年化收益</p>
                    <p className={`text-xl leading-tight font-bold font-mono ${kpiAnnualReturn == null ? 'text-neutral-500' : (kpiAnnualReturn >= 0 ? 'text-red-400' : 'text-green-400')}`}>
                      {kpiAnnualReturn != null ? `${kpiAnnualReturn >= 0 ? '+' : ''}${Number(kpiAnnualReturn).toFixed(1)}%` : isLoading ? '…' : '--'}
                    </p>
                  </div>
                  <Activity className={`w-6 h-6 flex-shrink-0 ${kpiAnnualReturn != null ? 'text-red-400' : 'text-neutral-600'}`} />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-neutral-900 border-neutral-700 h-full">
              <CardContent className="p-3 h-full">
                <div className="flex items-center justify-between h-full gap-2">
                  <div className="space-y-0.5">
                    <p className="text-xs text-neutral-400 tracking-wider">总交易数</p>
                    <p className={`text-xl leading-tight font-bold font-mono ${kpiTotalTrades == null ? 'text-neutral-500' : 'text-blue-400'}`}>
                      {kpiTotalTrades != null ? kpiTotalTrades : isLoading ? '…' : '--'}
                    </p>
                  </div>
                  <Hash className={`w-6 h-6 flex-shrink-0 ${kpiTotalTrades != null ? 'text-blue-400' : 'text-neutral-600'}`} />
                </div>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>

      {/* 权益曲线 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader className="px-4 pt-4 pb-2">
          <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">
            权益曲线{selectedBacktest ? ` — ${selectedBacktest?.strategy ?? selectedBacktest?.name ?? ''}` : ''}
          </CardTitle>
        </CardHeader>
        <CardContent className="px-4 pb-4 pt-0">
          <div className="h-64 lg:h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={equityCurveData}>
                <defs>
                  <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
                <XAxis dataKey="date" stroke="#737373" />
                <YAxis stroke="#737373" />
                <Tooltip contentStyle={{ backgroundColor: "#1f2937", border: "1px solid #404040", borderRadius: "4px" }} labelStyle={{ color: "#fff" }} />
                <Area type="monotone" dataKey="equity" stroke="#f97316" fillOpacity={1} fill="url(#equityGradient)" isAnimationActive={true} />
                <Line type="monotone" dataKey="benchmark" stroke="#6b7280" strokeDasharray="5 5" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* 月度收益率柱状图 */}
      {selectedBacktest && equityCurveData.length > 1 && (() => {
        // 按月聚合：取每月最后一条 equity 值，计算月度涨跌幅
        const monthMap: Record<string, number> = {}
        equityCurveData.forEach((d: any) => {
          const date = String(d.date ?? '')
          if (date.length >= 7) {
            const ym = date.slice(0, 7)
            monthMap[ym] = d.equity ?? d.value ?? 0
          }
        })
        const months = Object.keys(monthMap).sort()
        const initCap = (selectedBacktest as any).initialCapital ?? (equityCurveData[0] as any)?.equity ?? 200000
        const monthlyData = months.map((ym, i) => {
          const prev = i === 0 ? initCap : monthMap[months[i - 1]]
          const curr = monthMap[ym]
          const ret = prev > 0 ? ((curr - prev) / prev) * 100 : 0
          return { month: ym.slice(5), fullMonth: ym, ret: parseFloat(ret.toFixed(2)) }
        })
        if (monthlyData.length < 2) return null
        return (
          <Card className="bg-neutral-900 border-neutral-700">
            <CardHeader className="px-4 pt-4 pb-2">
              <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">月度收益率 / Monthly Returns</CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-4 pt-0">
              <div className="h-40 lg:h-44">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={monthlyData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="month" tick={{ fill: '#9CA3AF', fontSize: 11 }} />
                    <YAxis tickFormatter={(v) => `${v}%`} tick={{ fill: '#9CA3AF', fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: 6, color: '#fff' }}
                      cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                      formatter={(v: any) => [`${v}%`, '月收益']}
                      labelFormatter={(l) => `${monthlyData.find(d => d.month === l)?.fullMonth ?? l}`}
                    />
                    <ReferenceLine y={0} stroke="#6B7280" strokeDasharray="4 4" />
                    <Bar dataKey="ret" radius={[3, 3, 0, 0]}>
                      {monthlyData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.ret >= 0 ? '#ef4444' : '#22c55e'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        )
      })()}

      {/* 买卖盈亏统计 */}
      {selectedBacktest && tradeDetails.length > 0 && (() => {
        const stat = (selectedBacktest as any).tqsdk_stat ?? {}
        const openTrades  = tradeDetails.filter((t: any) => (t.offset ?? '').toUpperCase() === 'OPEN')
        const closeTrades = tradeDetails.filter((t: any) => (t.offset ?? '').toUpperCase() === 'CLOSE')
        const buyOpen  = openTrades.filter((t: any) => (t.direction ?? '').toUpperCase() === 'BUY').length
        const sellOpen = openTrades.filter((t: any) => (t.direction ?? '').toUpperCase() === 'SELL').length
        // 配对计算盈亏 (兼容后端 profit=null 的情况)
        const statSlippage = parseFloat(
          (selectedBacktest as any)?.transaction_cost_summary?.slippage_per_unit
          ?? (selectedBacktest as any)?.payload?.params?.slippage
          ?? 0
        ) || 0
        const statOpenStack: Record<string, Array<{price: number; volume: number; isBuy: boolean; commission: number}>> = {}
        const closeProfits: number[] = []
        tradeDetails.forEach((trade: any) => {
          const isBuy  = (trade.direction ?? '').toUpperCase() === 'BUY'
          const isOpen = (trade.offset ?? '').toUpperCase() === 'OPEN'
          const price  = parseFloat(trade.price) || 0
          const vol    = parseInt(trade.volume) || 1
          const comm   = parseFloat(trade.commission) || 0
          const sym    = trade.symbol || ''
          const mult   = getContractMultiplier(sym)
          const slip   = parseFloat((statSlippage * vol).toFixed(2))
          if (isOpen) {
            if (!statOpenStack[sym]) statOpenStack[sym] = []
            statOpenStack[sym].push({ price, volume: vol, isBuy, commission: comm })
          } else {
            let profit = trade.profit != null ? Number(trade.profit) : null
            if (profit === null) {
              const stack = statOpenStack[sym] || []
              if (stack.length > 0) {
                const opener = stack.shift()!
                const raw = opener.isBuy ? (price - opener.price) : (opener.price - price)
                profit = parseFloat((raw * vol * mult - opener.commission - comm - slip * 2).toFixed(2))
              }
            }
            if (profit != null) closeProfits.push(profit)
          }
        })
        const profitTrades = closeProfits.filter(p => p > 0)
        const lossTrades   = closeProfits.filter(p => p < 0)
        const totalProfit  = profitTrades.reduce((s, p) => s + p, 0)
        const totalLoss    = lossTrades.reduce((s, p) => s + p, 0)
        const totalComm    = tradeDetails.reduce((s: number, t: any) => s + (t.commission ?? 0), 0)
        return (
          <Card className="bg-neutral-900 border-neutral-700">
            <CardHeader className="px-4 pt-4 pb-2">
              <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">交易统计 / Trade Stats — {(selectedBacktest as any).strategy ?? (selectedBacktest as any).payload?.strategy?.id ?? ''}</CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-4 pt-0">
              <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-6 gap-2">
                <div className="bg-neutral-800 rounded p-2.5">
                  <p className="text-xs text-neutral-400 mb-0.5">开仓次数</p>
                  <p className="text-white font-bold font-mono text-base">{stat.open_times ?? openTrades.length}</p>
                  <p className="text-xs text-neutral-500 mt-0.5">多 {buyOpen} / 空 {sellOpen}</p>
                </div>
                <div className="bg-neutral-800 rounded p-2.5">
                  <p className="text-xs text-neutral-400 mb-0.5">平仓次数</p>
                  <p className="text-white font-bold font-mono text-base">{stat.close_times ?? closeTrades.length}</p>
                  <p className="text-xs text-neutral-500 mt-0.5">共 {tradeDetails.length} 笔成交</p>
                </div>
                <div className="bg-neutral-800 rounded p-2.5">
                  <p className="text-xs text-neutral-400 mb-0.5">盈利笔数</p>
                  <p className="text-red-400 font-bold font-mono text-base">{stat.profit_volumes ?? profitTrades.length}</p>
                  <p className="text-xs text-neutral-500 mt-0.5">共 +¥{Number(totalProfit).toLocaleString()}</p>
                </div>
                <div className="bg-neutral-800 rounded p-2.5">
                  <p className="text-xs text-neutral-400 mb-0.5">亏损笔数</p>
                  <p className="text-green-400 font-bold font-mono text-base">{stat.loss_volumes ?? lossTrades.length}</p>
                  <p className="text-xs text-neutral-500 mt-0.5">共 ¥{Number(totalLoss).toLocaleString()}</p>
                </div>
                <div className="bg-neutral-800 rounded p-2.5">
                  <p className="text-xs text-neutral-400 mb-0.5">净盈亏</p>
                  <p className={`font-bold font-mono text-base ${(totalProfit + totalLoss) >= 0 ? 'text-red-400' : 'text-green-400'}`}>
                    {(totalProfit + totalLoss) >= 0 ? '+' : ''}¥{Number(totalProfit + totalLoss).toLocaleString()}
                  </p>
                  <p className="text-xs text-neutral-500 mt-0.5">手续费 ¥{Number(stat.commission ?? totalComm).toLocaleString()}</p>
                  {(() => {
                    const cs = (selectedBacktest as any)?.transaction_cost_summary
                    const totalSlip = cs?.total_slippage_estimated
                    if (totalSlip == null || Number(totalSlip) === 0) return null
                    return <p className="text-xs text-neutral-500">滑点 ¥{Number(totalSlip).toLocaleString()}</p>
                  })()}
                </div>
                <div className="bg-neutral-800 rounded p-2.5">
                  <p className="text-xs text-neutral-400 mb-0.5">交易天数</p>
                  <p className="text-white font-bold font-mono text-base">{stat.trading_days ?? (selectedBacktest as any).ticks ?? '--'}</p>
                  <p className="text-xs text-neutral-500 mt-0.5">盈{stat.cum_profit_days ?? '--'} / 亏{stat.cum_loss_days ?? '--'} 天</p>
                </div>
              </div>
              {(selectedBacktest as any).error_message && (
                <div className="mt-2 p-2.5 bg-red-900/20 border border-red-800/40 rounded text-xs text-red-400">
                  <span className="font-semibold mr-2">失败原因：</span>
                  {String((selectedBacktest as any).error_message).split('\n')[0]}
                </div>
              )}
            </CardContent>
          </Card>
        )
      })()}

      {/* ─── 交易成本统计 ──────────────────────────────────────────── */}
      {selectedBacktest && (() => {
        const costSummary = (selectedBacktest as any)?.transaction_cost_summary || {}
        const hasCost = costSummary && (costSummary.total_cost_estimated != null || costSummary.slippage_per_unit != null || costSummary.commission_per_lot_round_turn != null)
        if (!hasCost) return null
        return (
          <Card className="bg-neutral-900 border-neutral-700">
            <CardHeader className="px-4 pt-4 pb-2">
              <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">交易成本统计 / Transaction Costs</CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-4 pt-0">
              <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-2">
                <div className="bg-neutral-800 rounded p-2.5">
                  <p className="text-xs text-neutral-400 mb-0.5">每点滑点</p>
                  <p className="text-white font-mono text-sm font-bold">{costSummary.slippage_per_unit ?? '—'}</p>
                </div>
                <div className="bg-neutral-800 rounded p-2.5">
                  <p className="text-xs text-neutral-400 mb-0.5">每手回合手续费</p>
                  <p className="text-white font-mono text-sm font-bold">{costSummary.commission_per_lot_round_turn ?? '—'}</p>
                </div>
                <div className="bg-neutral-800 rounded p-2.5">
                  <p className="text-xs text-neutral-400 mb-0.5">估算总滑点</p>
                  <p className="text-amber-400 font-mono text-sm font-bold">{costSummary.total_slippage_estimated != null ? `¥${Number(costSummary.total_slippage_estimated).toLocaleString()}` : '—'}</p>
                </div>
                <div className="bg-neutral-800 rounded p-2.5">
                  <p className="text-xs text-neutral-400 mb-0.5">估算总手续费</p>
                  <p className="text-amber-400 font-mono text-sm font-bold">{costSummary.total_commission_estimated != null ? `¥${Number(costSummary.total_commission_estimated).toLocaleString()}` : '—'}</p>
                </div>
                <div className="bg-neutral-800 rounded p-2.5">
                  <p className="text-xs text-neutral-400 mb-0.5">估算总成本</p>
                  <p className="text-red-400 font-mono text-sm font-bold">{costSummary.total_cost_estimated != null ? `¥${Number(costSummary.total_cost_estimated).toLocaleString()}` : '—'}</p>
                </div>
                <div className="bg-neutral-800 rounded p-2.5">
                  <p className="text-xs text-neutral-400 mb-0.5">均摊每笔成本</p>
                  <p className="text-neutral-300 font-mono text-sm font-bold">{costSummary.avg_cost_per_trade_estimated != null ? `¥${Number(costSummary.avg_cost_per_trade_estimated).toLocaleString()}` : '—'}</p>
                </div>
              </div>
              {costSummary.note && (
                <p className="text-xs text-neutral-600 mt-1.5">{costSummary.note}</p>
              )}
            </CardContent>
          </Card>
        )
      })()}

      {/* ─── 调优建议面板 ──────────────────────────────────────────── */}
      {optimizationSuggestions.length > 0 && (
        <div id="optimization-suggestions">
        <Card className="border-2 border-blue-600/40 bg-neutral-900">
          <CardHeader className="px-4 pt-4 pb-2">
            <CardTitle className="text-sm font-medium text-blue-400 tracking-wider flex items-center gap-2">
              <Lightbulb className="w-4 h-4" />
              调优建议 / Optimization Suggestions ({optimizationSuggestions.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4 pt-0 space-y-2.5">
            <p className="text-[11px] text-neutral-500 border-b border-neutral-700 pb-1.5">
              基于当前回测数据自动分析 / Auto-generated from backtest results — 供参考，需结合市场判断
            </p>
            {optimizationSuggestions.map((s, i) => (
              <div key={i} className={`rounded-lg p-2.5 border flex items-start gap-2.5 ${s.level === 'critical' ? 'bg-red-900/15 border-red-700/40' : s.level === 'warning' ? 'bg-amber-900/15 border-amber-700/40' : s.level === 'suggestion' ? 'bg-blue-900/15 border-blue-700/40' : 'bg-neutral-800/50 border-neutral-700/40'}`}>
                <span className="text-lg flex-shrink-0 mt-0.5">{s.icon}</span>
                <div>
                  <p className={`text-sm font-semibold ${s.level === 'critical' ? 'text-red-300' : s.level === 'warning' ? 'text-amber-300' : s.level === 'suggestion' ? 'text-blue-300' : 'text-neutral-300'}`}>{s.title}</p>
                  <p className="text-xs text-neutral-400 mt-0.5 leading-relaxed">{s.detail}</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
        </div>
      )}

      {/* 回测记录 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader className="px-4 pt-4 pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">回测记录</CardTitle>
            {selectedIds.size > 0 && (
              <Button
                onClick={async () => {
                  if (!confirm(`确认删除选中的 ${selectedIds.size} 条回测记录？`)) return
                  setIsBatchDeleting(true)
                  try {
                    await api.batchDeleteBacktests(Array.from(selectedIds))
                    setSelectedIds(new Set())
                    setComputedKPIs({ totalReturn: null, maxDrawdown: null, sharpeRatio: null, winRate: null, totalTrades: null })
                    await load()
                  } catch (err) {
                    setApiError(api.friendlyError(err))
                  } finally {
                    setIsBatchDeleting(false)
                  }
                }}
                className="bg-red-600 hover:bg-red-700 text-white text-xs px-3 py-1 h-7"
                disabled={isBatchDeleting}
              >
                {isBatchDeleting ? '删除中…' : `删除选中 (${selectedIds.size})`}
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent className="px-4 pb-4 pt-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-neutral-700">
                  <th className="py-2 px-2 w-8">
                    <input
                      type="checkbox"
                      className="accent-orange-500"
                      checked={backtests.length > 0 && selectedIds.size === backtests.length}
                      onChange={e => {
                        if (e.target.checked) setSelectedIds(new Set(backtests.map((b: any) => b.id).filter(Boolean)))
                        else setSelectedIds(new Set())
                      }}
                    />
                  </th>
                  <th className="text-left py-2 px-3 text-xs font-medium text-neutral-400">策略</th>
                  <th className="text-left py-2 px-3 text-xs font-medium text-neutral-400">合约</th>
                  <th className="text-left py-2 px-3 text-xs font-medium text-neutral-400">测试区间</th>
                  <th className="text-left py-2 px-3 text-xs font-medium text-neutral-400">提交时间</th>
                  <th className="text-left py-2 px-3 text-xs font-medium text-neutral-400">状态</th>
                  <th className="text-left py-2 px-3 text-xs font-medium text-neutral-400">总收益</th>
                  <th className="text-left py-2 px-3 text-xs font-medium text-neutral-400">最大回撤</th>
                  <th className="text-left py-2 px-3 text-xs font-medium text-neutral-400">夏普比率</th>
                  <th className="text-left py-2 px-3 text-xs font-medium text-neutral-400">胜率</th>
                </tr>
              </thead>
              <tbody>
                {backtests.length === 0 ? (
                  <tr>
                    <td colSpan={10} className="py-6 px-3 text-center text-neutral-400">暂无数据</td>
                  </tr>
                ) : (
                  [...backtests].sort((a: any, b: any) => (b.submitted_at ?? 0) - (a.submitted_at ?? 0)).map((backtest: any, index: number) => (
                    <tr
                      key={backtest.id ?? index}
                      className={`border-b border-neutral-800 hover:bg-neutral-800 transition-colors cursor-pointer ${
                        selectedIds.has(backtest.id) ? 'bg-neutral-800/60' : index % 2 === 0 ? "bg-neutral-900" : "bg-neutral-850"
                      }`}
                      onClick={() => fetchBacktestDetails(backtest.id)}
                    >
                      <td className="py-2 px-2" onClick={e => e.stopPropagation()}>
                        <input
                          type="checkbox"
                          className="accent-orange-500"
                          checked={selectedIds.has(backtest.id)}
                          onChange={e => {
                            const next = new Set(selectedIds)
                            if (e.target.checked) next.add(backtest.id)
                            else next.delete(backtest.id)
                            setSelectedIds(next)
                          }}
                        />
                      </td>
                      <td className="py-2 px-3 text-white text-xs">{backtest.name ?? backtest.strategy ?? backtest.payload?.strategy?.id ?? '--'}</td>
                      <td className="py-2 px-3 text-neutral-300 text-xs">{backtest.contracts ?? (backtest.payload?.symbols?.[0]) ?? '--'}</td>
                      <td className="py-2 px-3 text-neutral-400 text-xs whitespace-nowrap">
                        {backtest.payload?.start ?? '--'} ~ {backtest.payload?.end ?? '--'}
                      </td>
                      <td className="py-2 px-3 text-neutral-400 text-xs whitespace-nowrap">
                        {backtest.submitted_at ? new Date(backtest.submitted_at * 1000).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '--'}
                      </td>
                      <td className="py-2 px-3">
                        {(backtest.status === 'running' || backtest.status === 'submitted' || backtest.status === 'pending') && progressMap[backtest.id] != null ? (
                          <div className="min-w-[120px]">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-xs text-orange-400 font-mono">
                                {progressMap[backtest.id].progress}%
                              </span>
                              {progressMap[backtest.id].current_date && (
                                <span className="text-xs text-neutral-500">{progressMap[backtest.id].current_date}</span>
                              )}
                            </div>
                            <div className="h-1.5 w-full bg-neutral-700 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-orange-500 rounded-full transition-all duration-500"
                                style={{ width: `${progressMap[backtest.id].progress}%` }}
                              />
                            </div>
                          </div>
                        ) : (
                          <div className="flex flex-col gap-1">
                            <Badge className={getStatusColor(backtest.status)}>
                              {getStatusText(backtest.status)}
                            </Badge>
                            {backtest.status === 'failed' && (backtest as any).error_message && (
                              <span className="text-[10px] text-red-400 leading-tight max-w-[260px] break-all" title={String((backtest as any).error_message)}>
                                {formatErrorMessage((backtest as any).error_message)}
                              </span>
                            )}
                          </div>
                        )}
                      </td>
                      <td className={`py-2 px-3 font-mono text-xs ${(backtest.totalReturn ?? 0) >= 0 ? "text-red-400" : "text-green-400"}`}>
                        {backtest.totalReturn != null ? `${backtest.totalReturn >= 0 ? '+' : ''}${Number(backtest.totalReturn).toFixed(1)}%` : '--'}
                      </td>
                      <td className="py-2 px-3 text-green-400 font-mono text-xs">{backtest.maxDrawdown != null ? `-${Number(backtest.maxDrawdown).toFixed(1)}%` : '--'}</td>
                      <td className="py-2 px-3 text-white font-mono text-xs">{backtest.sharpeRatio != null ? Number(backtest.sharpeRatio).toFixed(2) : '--'}</td>
                      <td className="py-2 px-3 text-white font-mono text-xs">{backtest.winRate != null ? `${backtest.winRate}%` : '--'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* 交易明细 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader className="px-4 pt-4 pb-2">
          <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">
            交易明细 / Trade Details ({tradeDetails.length})
          </CardTitle>
        </CardHeader>
        <CardContent className="px-4 pb-4 pt-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-neutral-700">
                  <th className="text-left py-2 px-3 text-xs font-medium text-neutral-400">时间</th>
                  <th className="text-left py-2 px-3 text-xs font-medium text-neutral-400">合约</th>
                  <th className="text-left py-2 px-3 text-xs font-medium text-neutral-400">方向</th>
                  <th className="text-left py-2 px-3 text-xs font-medium text-neutral-400">操作</th>
                  <th className="text-left py-2 px-3 text-xs font-medium text-neutral-400">价格</th>
                  <th className="text-left py-2 px-3 text-xs font-medium text-neutral-400">数量</th>
                  <th className="text-left py-2 px-3 text-xs font-medium text-neutral-400">手续费</th>
                  <th className="text-left py-2 px-3 text-xs font-medium text-neutral-400">滑点</th>
                  <th className="text-left py-2 px-3 text-xs font-medium text-neutral-400">净盈亏</th>
                </tr>
              </thead>
              <tbody>
                {tradeDetails.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="py-6 px-3 text-center text-neutral-400">暂无数据</td>
                  </tr>
                ) : (
                  (() => {
                    // 前端配对计算：为 profit=null 的平仓交易计算盈亏
                    const slippagePerLot = parseFloat(
                      (selectedBacktest as any)?.transaction_cost_summary?.slippage_per_unit
                      ?? (selectedBacktest as any)?.payload?.params?.slippage
                      ?? 0
                    ) || 0
                    const mult = getContractMultiplier(
                      (selectedBacktest as any)?.contracts?.[0] ?? (selectedBacktest as any)?.payload?.symbols?.[0] ?? tradeDetails[0]?.symbol ?? ''
                    )
                    const openStack: Record<string, Array<{price: number; volume: number; isBuy: boolean; commission: number}>> = {}
                    const computed = tradeDetails.map((trade: any) => {
                      const isBuy   = (trade.direction ?? '').toUpperCase() === 'BUY'
                      const isOpen  = (trade.offset ?? '').toUpperCase() === 'OPEN'
                      const price   = parseFloat(trade.price) || 0
                      const vol     = parseInt(trade.volume) || 1
                      const comm    = parseFloat(trade.commission) || 0
                      const slip    = parseFloat((slippagePerLot * vol).toFixed(2))
                      const sym     = trade.symbol || ''
                      let profit    = trade.profit != null ? trade.profit : null
                      if (isOpen) {
                        if (!openStack[sym]) openStack[sym] = []
                        openStack[sym].push({ price, volume: vol, isBuy, commission: comm })
                      } else if (profit === null) {
                        const stack = openStack[sym] || []
                        if (stack.length > 0) {
                          const opener = stack.shift()!
                          const raw = opener.isBuy ? (price - opener.price) : (opener.price - price)
                          profit = parseFloat((raw * vol * mult - opener.commission - comm - slip * 2).toFixed(2))
                        }
                      }
                      return { ...trade, _computedProfit: profit, _slip: slip, _isOpen: isOpen, _isBuy: isBuy }
                    })
                    return computed.map((trade: any, index: number) => (
                    <tr
                      key={trade.trade_id ?? index}
                      className={`border-b border-neutral-800 ${index % 2 === 0 ? "bg-neutral-900" : "bg-neutral-850"}`}
                    >
                      <td className="py-1.5 px-3 text-neutral-300 font-mono text-xs">{trade.date ?? '--'}</td>
                      <td className="py-1.5 px-3 text-white font-mono text-xs">{trade.symbol ?? '--'}</td>
                      <td className="py-1.5 px-3 text-xs">
                        <span className={trade._isBuy ? 'text-red-400 font-mono' : 'text-green-400 font-mono'}>
                          {trade._isBuy ? '买' : '卖'}
                        </span>
                      </td>
                      <td className="py-1.5 px-3 text-xs">
                        <span className={trade._isOpen ? 'text-orange-400' : 'text-neutral-300'}>{trade._isOpen ? '开仓' : '平仓'}</span>
                      </td>
                      <td className="py-1.5 px-3 text-white font-mono text-xs">{trade.price ?? '--'}</td>
                      <td className="py-1.5 px-3 text-white font-mono text-xs">{trade.volume ?? '--'}</td>
                      <td className="py-1.5 px-3 text-neutral-400 font-mono text-xs">{trade.commission ?? '--'}</td>
                      <td className="py-1.5 px-3 text-neutral-400 font-mono text-xs">
                        {trade.slippage != null
                          ? trade.slippage
                          : slippagePerLot > 0 ? trade._slip : <span className="text-neutral-600">—</span>}
                      </td>
                      <td className={`py-1.5 px-3 font-mono text-xs ${trade._computedProfit != null ? (trade._computedProfit >= 0 ? 'text-red-400' : 'text-green-400') : 'text-neutral-600'}`}>
                        {trade._isOpen
                          ? <span className="text-neutral-600">—</span>
                          : trade._computedProfit != null
                            ? (trade._computedProfit >= 0 ? '+' : '') + Number(trade._computedProfit).toLocaleString()
                            : '–'
                        }
                      </td>
                    </tr>
                    ))
                  })()
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>


    </div>
  )
}
