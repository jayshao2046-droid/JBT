"use client"

import { useState, useEffect } from "react"
import api from '@/src/utils/api'
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
  const [showSuggestions, setShowSuggestions] = useState(false)
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
  const handleExportReport = () => {
    const bt = selectedBacktest
    if (!bt) { alert('请先点击一条回测记录'); return }
    const stat = (bt as any).tqsdk_stat ?? {}
    const strategyName = bt.strategy ?? (bt as any).payload?.strategy?.id ?? bt.name ?? bt.id
    const startDate = (bt as any).payload?.start ?? stat.start_date ?? '--'
    const endDate = (bt as any).payload?.end ?? stat.end_date ?? '--'
    const contract = tradeDetails.length > 0 ? [...new Set(tradeDetails.map((t: any) => t.symbol).filter(Boolean))].join(', ') : '--'
    // P&L 统计
    const openTrades = tradeDetails.filter((t: any) => (t.offset ?? '').toUpperCase() === 'OPEN')
    const closeTrades = tradeDetails.filter((t: any) => (t.offset ?? '').toUpperCase() === 'CLOSE')
    const buyOpen  = openTrades.filter((t: any) => (t.direction ?? '').toUpperCase() === 'BUY').length
    const sellOpen = openTrades.filter((t: any) => (t.direction ?? '').toUpperCase() === 'SELL').length
    const totalCommission = tradeDetails.reduce((s: number, t: any) => s + (t.commission ?? 0), 0)
    const profitTrades = closeTrades.filter((t: any) => t.profit != null && t.profit > 0)
    const lossTrades  = closeTrades.filter((t: any) => t.profit != null && t.profit < 0)
    const totalProfit = profitTrades.reduce((s: number, t: any) => s + t.profit, 0)
    const totalLoss   = lossTrades.reduce((s: number, t: any) => s + t.profit, 0)

    const lines: string[] = [
      `# 回测报告 — ${strategyName}`,
      ``,
      `生成时间：${new Date().toLocaleString('zh-CN')}`,
      ``,
      `## 基本信息`,
      `| 字段 | 值 |`,
      `|------|-----|`,
      `| 策略 | ${strategyName} |`,
      `| 回测周期 | ${startDate} → ${endDate} |`,
      `| 合约 | ${contract} |`,
      `| 交易天数 | ${stat.trading_days ?? bt.ticks ?? '--'} |`,
      `| 初始资金 | ¥${Number(bt.initialCapital ?? stat.init_balance ?? 0).toLocaleString()} |`,
      `| 最终资金 | ¥${Number(bt.finalCapital ?? stat.balance ?? 0).toLocaleString()} |`,
      bt.status === 'failed' ? `| 失败原因 | ${(bt as any).error_message ?? '--'} |` : null,
      ``,
      `## 收益指标`,
      `| 指标 | 值 |`,
      `|------|-----|`,
      `| 总收益率 | ${bt.totalReturn != null ? (bt.totalReturn >= 0 ? '+' : '') + Number(bt.totalReturn).toFixed(2) + '%' : '--'} |`,
      `| 年化收益 | ${bt.annualReturn != null ? (bt.annualReturn >= 0 ? '+' : '') + Number(bt.annualReturn).toFixed(2) + '%' : '--'} |`,
      `| 最大回撤 | -${Number(bt.maxDrawdown ?? 0).toFixed(2)}% |`,
      `| 夏普比率 | ${bt.sharpeRatio != null ? Number(bt.sharpeRatio).toFixed(4) : '--'} |`,
      `| 胜率 | ${bt.winRate != null ? Number(bt.winRate).toFixed(2) + '%' : '--'} |`,
      `| 盈亏比 | ${bt.profitLossRatio != null ? Number(bt.profitLossRatio).toFixed(4) : '--'} |`,
      ``,
      `## 交易统计`,
      `| 指标 | 值 |`,
      `|------|-----|`,
      `| 开仓次数 | ${stat.open_times ?? openTrades.length} 次 |`,
      `| 平仓次数 | ${stat.close_times ?? closeTrades.length} 次 |`,
      `| 做多开仓 | ${buyOpen} 次 |`,
      `| 做空开仓 | ${sellOpen} 次 |`,
      `| 盈利笔数 | ${stat.profit_volumes ?? profitTrades.length} 笔 |`,
      `| 亏损笔数 | ${stat.loss_volumes ?? lossTrades.length} 笔 |`,
      `| 总盈利 | ¥${Number(stat.profit_value ?? totalProfit).toLocaleString()} |`,
      `| 总亏损 | ¥${Number(stat.loss_value ?? totalLoss).toLocaleString()} |`,
      `| 累计手续费 | ¥${Number(stat.commission ?? totalCommission).toLocaleString()} |`,
      ``,
      `## 交易明细 (${tradeDetails.length} 笔)`,
      `| 日期 | 合约 | 方向 | 操作 | 价格 | 数量 | 盈亏 | 手续费 |`,
      `|------|------|------|------|------|------|------|--------|`,
      ...tradeDetails.map((t: any) =>
        `| ${t.date ?? '--'} | ${t.symbol ?? '--'} | ${t.direction ?? '--'} | ${t.offset ?? '--'} | ${t.price ?? '--'} | ${t.volume ?? '--'} | ${t.profit != null ? (t.profit >= 0 ? '+' : '') + t.profit : '--'} | ${t.commission ?? '--'} |`
      ),
    ].filter(l => l !== null) as string[]

    const content = lines.join('\n')
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `backtest_${strategyName.replace(/[^\w]/g, '_')}_${startDate}_${endDate}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  // 使用集中式 API 工具

  const [tradeDetails, setTradeDetails] = useState<any[]>([])

  const fetchBacktestDetails = async (id: string) => {
    try {
      setIsLoading(true)
      setApiError(null)
      setOptimizationSuggestions([])
      setAnomalyModal(null)
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
        const totalTrades = closedTrades.length || tradesArr.length || 0
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
        setShowSuggestions(true)
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

  return (
    <div className="p-6 space-y-6">
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
              <Button className="w-full bg-red-700 hover:bg-red-800 text-white" onClick={() => { setAnomalyModal(null); setShowSuggestions(true) }}>
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
          <CardContent className="p-4">
            <div className="flex items-start justify-between mb-3">
              <div>
                <p className="text-orange-400 font-semibold text-sm tracking-wider">
                  {selectedBacktest?.name ?? selectedBacktest?.strategy ?? selectedBacktest?.payload?.strategy?.id ?? selectedBacktest?.id?.slice(0, 16) ?? '--'}
                </p>
                <p className="text-neutral-500 text-xs font-mono mt-0.5">{selectedBacktest?.payload?.start ?? ''}{selectedBacktest?.payload?.start ? ' ~ ' : ''}{selectedBacktest?.payload?.end ?? ''}</p>
              </div>
              <Badge className={getStatusColor(selectedBacktest.status)}>
                {getStatusText(selectedBacktest.status)}
              </Badge>
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
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
              <div className="bg-neutral-800 rounded p-2">
                <p className="text-neutral-500 text-xs mb-1">合约</p>
                <p className="text-white text-sm font-mono">
                  {tradeDetails.length > 0
                    ? [...new Set(tradeDetails.map((t: any) => t.symbol).filter(Boolean))].join(', ')
                    : selectedBacktest?.contract ?? selectedBacktest?.payload?.contract ?? '--'}
                </p>
              </div>
              <div className="bg-neutral-800 rounded p-2">
                <p className="text-neutral-500 text-xs mb-1">回测周期</p>
                <p className="text-white text-xs font-mono">
                  {(selectedBacktest as any)?.payload?.start ?? (selectedBacktest as any)?.tqsdk_stat?.start_date ?? '--'}
                  {' → '}
                  {(selectedBacktest as any)?.payload?.end ?? (selectedBacktest as any)?.tqsdk_stat?.end_date ?? '--'}
                </p>
              </div>
              <div className="bg-neutral-800 rounded p-2">
                <p className="text-neutral-500 text-xs mb-1">初始资金</p>
                <p className="text-white text-sm font-mono">
                  {selectedBacktest?.initialCapital != null
                    ? '¥ ' + Number(selectedBacktest.initialCapital).toLocaleString()
                    : selectedBacktest?.payload?.params?.initialCapital != null
                    ? '¥ ' + Number(selectedBacktest.payload.params.initialCapital).toLocaleString()
                    : '--'}
                </p>
              </div>
              <div className="bg-neutral-800 rounded p-2">
                <p className="text-neutral-500 text-xs mb-1">最终资金</p>
                <p className={`text-sm font-mono ${
                  selectedBacktest?.finalCapital != null && selectedBacktest?.initialCapital != null
                    ? (selectedBacktest.finalCapital >= selectedBacktest.initialCapital ? 'text-red-400' : 'text-green-400')
                    : 'text-white'
                }`}>
                  {selectedBacktest?.finalCapital != null ? '¥ ' + Number(selectedBacktest.finalCapital).toLocaleString() : '--'}
                </p>
              </div>
            </div>
            {selectedBacktest?.payload?.params && Object.keys(selectedBacktest.payload.params).length > 0 && (
              <div className="border-t border-neutral-700 pt-3">
                <p className="text-neutral-500 text-xs mb-2 tracking-wider">参数配置</p>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(selectedBacktest.payload.params).map(([k, v]) => (
                    <span key={k} className="text-xs bg-neutral-800 px-2 py-1 rounded text-neutral-400">
                      {k}: <span className="text-white font-mono">{String(v)}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 关键指标统计 */}
      <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-6 gap-4">
        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-neutral-400 tracking-wider">总收益率</p>
                <p className={`text-2xl font-bold font-mono ${
                  kpiTotalReturn == null ? 'text-neutral-500' :
                  (kpiTotalReturn >= 0 ? 'text-red-400' : 'text-green-400')
                }`}>
                  {kpiTotalReturn != null
                    ? `${kpiTotalReturn >= 0 ? '+' : ''}${Number(kpiTotalReturn).toFixed(1)}%`
                    : isLoading ? '…' : '--'}
                </p>
              </div>
              <TrendingUp className={`w-8 h-8 ${kpiTotalReturn != null && kpiTotalReturn >= 0 ? 'text-red-400' : 'text-neutral-600'}`} />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-neutral-400 tracking-wider">最大回撤</p>
                <p className={`text-2xl font-bold font-mono ${
                  kpiMaxDrawdown == null ? 'text-neutral-500' : 'text-green-400'
                }`}>
                  {kpiMaxDrawdown != null
                    ? `-${Math.abs(Number(kpiMaxDrawdown)).toFixed(1)}%`
                    : isLoading ? '…' : '--'}
                </p>
              </div>
              <TrendingDown className={`w-8 h-8 ${kpiMaxDrawdown != null ? 'text-green-400' : 'text-neutral-600'}`} />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-neutral-400 tracking-wider">夏普比率</p>
                <p className={`text-2xl font-bold font-mono ${
                  kpiSharpe == null ? 'text-neutral-500' : 'text-white'
                }`}>
                  {kpiSharpe != null ? Number(kpiSharpe).toFixed(2) : isLoading ? '…' : '--'}
                </p>
              </div>
              <BarChart3 className={`w-8 h-8 ${kpiSharpe != null ? 'text-white' : 'text-neutral-600'}`} />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-neutral-400 tracking-wider">胜率</p>
                <p className={`text-2xl font-bold font-mono ${
                  kpiWinRate == null ? 'text-neutral-500' : 'text-orange-500'
                }`}>
                  {kpiWinRate != null ? `${kpiWinRate}%` : isLoading ? '…' : '--'}
                </p>
              </div>
              <Percent className={`w-8 h-8 ${kpiWinRate != null ? 'text-orange-500' : 'text-neutral-600'}`} />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-neutral-400 tracking-wider">年化收益</p>
                <p className={`text-2xl font-bold font-mono ${
                  kpiAnnualReturn == null ? 'text-neutral-500' :
                  (kpiAnnualReturn >= 0 ? 'text-red-400' : 'text-green-400')
                }`}>
                  {kpiAnnualReturn != null
                    ? `${kpiAnnualReturn >= 0 ? '+' : ''}${Number(kpiAnnualReturn).toFixed(1)}%`
                    : isLoading ? '…' : '--'}
                </p>
              </div>
              <Activity className={`w-8 h-8 ${kpiAnnualReturn != null ? 'text-red-400' : 'text-neutral-600'}`} />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-neutral-400 tracking-wider">总交易数</p>
                <p className={`text-2xl font-bold font-mono ${
                  kpiTotalTrades == null ? 'text-neutral-500' : 'text-blue-400'
                }`}>
                  {kpiTotalTrades != null ? kpiTotalTrades : isLoading ? '…' : '--'}
                </p>
              </div>
              <Hash className={`w-8 h-8 ${kpiTotalTrades != null ? 'text-blue-400' : 'text-neutral-600'}`} />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 权益曲线 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">
            权益曲线{selectedBacktest ? ` — ${selectedBacktest?.strategy ?? selectedBacktest?.name ?? ''}` : ''}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80">
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
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1f2937",
                    border: "1px solid #404040",
                    borderRadius: "4px",
                  }}
                  labelStyle={{ color: "#fff" }}
                />
                <Area
                  type="monotone"
                  dataKey="equity"
                  stroke="#f97316"
                  fillOpacity={1}
                  fill="url(#equityGradient)"
                  isAnimationActive={true}
                />
                <Line
                  type="monotone"
                  dataKey="benchmark"
                  stroke="#6b7280"
                  strokeDasharray="5 5"
                  dot={false}
                />
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
            <CardHeader>
              <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">月度收益率</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-48">
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
        const profitTrades = closeTrades.filter((t: any) => t.profit != null && t.profit > 0)
        const lossTrades   = closeTrades.filter((t: any) => t.profit != null && t.profit < 0)
        const totalProfit  = profitTrades.reduce((s: number, t: any) => s + t.profit, 0)
        const totalLoss    = lossTrades.reduce((s: number, t: any) => s + t.profit, 0)
        const totalComm    = tradeDetails.reduce((s: number, t: any) => s + (t.commission ?? 0), 0)
        return (
          <Card className="bg-neutral-900 border-neutral-700">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">交易统计 — {(selectedBacktest as any).strategy ?? (selectedBacktest as any).payload?.strategy?.id ?? ''}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-6 gap-3">
                <div className="bg-neutral-800 rounded p-3">
                  <p className="text-xs text-neutral-400 mb-1">开仓次数</p>
                  <p className="text-white font-bold font-mono text-lg">{stat.open_times ?? openTrades.length}</p>
                  <p className="text-xs text-neutral-500 mt-1">多 {buyOpen} / 空 {sellOpen}</p>
                </div>
                <div className="bg-neutral-800 rounded p-3">
                  <p className="text-xs text-neutral-400 mb-1">平仓次数</p>
                  <p className="text-white font-bold font-mono text-lg">{stat.close_times ?? closeTrades.length}</p>
                  <p className="text-xs text-neutral-500 mt-1">共 {tradeDetails.length} 笔成交</p>
                </div>
                <div className="bg-neutral-800 rounded p-3">
                  <p className="text-xs text-neutral-400 mb-1">盈利笔数</p>
                  <p className="text-red-400 font-bold font-mono text-lg">{stat.profit_volumes ?? profitTrades.length}</p>
                  <p className="text-xs text-neutral-500 mt-1">共 +¥{Number(stat.profit_value ?? totalProfit).toLocaleString()}</p>
                </div>
                <div className="bg-neutral-800 rounded p-3">
                  <p className="text-xs text-neutral-400 mb-1">亏损笔数</p>
                  <p className="text-green-400 font-bold font-mono text-lg">{stat.loss_volumes ?? lossTrades.length}</p>
                  <p className="text-xs text-neutral-500 mt-1">共 ¥{Number(stat.loss_value ?? totalLoss).toLocaleString()}</p>
                </div>
                <div className="bg-neutral-800 rounded p-3">
                  <p className="text-xs text-neutral-400 mb-1">净盈亏</p>
                  <p className={`font-bold font-mono text-lg ${(totalProfit + totalLoss) >= 0 ? 'text-red-400' : 'text-green-400'}`}>
                    {(totalProfit + totalLoss) >= 0 ? '+' : ''}¥{Number(totalProfit + totalLoss).toLocaleString()}
                  </p>
                  <p className="text-xs text-neutral-500 mt-1">手续费 ¥{Number(stat.commission ?? totalComm).toLocaleString()}</p>
                </div>
                <div className="bg-neutral-800 rounded p-3">
                  <p className="text-xs text-neutral-400 mb-1">交易天数</p>
                  <p className="text-white font-bold font-mono text-lg">{stat.trading_days ?? (selectedBacktest as any).ticks ?? '--'}</p>
                  <p className="text-xs text-neutral-500 mt-1">盈{stat.cum_profit_days ?? '--'} / 亏{stat.cum_loss_days ?? '--'} 天</p>
                </div>
              </div>
              {(selectedBacktest as any).error_message && (
                <div className="mt-3 p-3 bg-red-900/20 border border-red-800/40 rounded text-xs text-red-400">
                  <span className="font-semibold mr-2">失败原因：</span>
                  {String((selectedBacktest as any).error_message).split('\n')[0]}
                </div>
              )}
            </CardContent>
          </Card>
        )
      })()}

      {/* ─── 调优建议面板 ──────────────────────────────────────────── */}
      {optimizationSuggestions.length > 0 && (
        <Card className={`border-2 ${showSuggestions ? 'border-blue-600/40' : 'border-neutral-700'} bg-neutral-900`}>
          <CardHeader className="cursor-pointer pb-3" onClick={() => setShowSuggestions(!showSuggestions)}>
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-blue-400 tracking-wider flex items-center gap-2">
                <Lightbulb className="w-4 h-4" />
                调优建议 / Optimization Suggestions ({optimizationSuggestions.length})
              </CardTitle>
              <span className="text-xs text-neutral-500">{showSuggestions ? '▲ 收起' : '▼ 展开'}</span>
            </div>
          </CardHeader>
          {showSuggestions && (
            <CardContent className="space-y-3">
              <p className="text-xs text-neutral-500 border-b border-neutral-700 pb-2">
                基于当前回测数据自动分析 / Auto-generated from backtest results — 供参考，需结合市场判断
              </p>
              {optimizationSuggestions.map((s, i) => (
                <div key={i} className={`rounded-lg p-3 border flex items-start gap-3 ${
                  s.level === 'critical' ? 'bg-red-900/15 border-red-700/40' :
                  s.level === 'warning' ? 'bg-amber-900/15 border-amber-700/40' :
                  s.level === 'suggestion' ? 'bg-blue-900/15 border-blue-700/40' :
                  'bg-neutral-800/50 border-neutral-700/40'
                }`}>
                  <span className="text-xl flex-shrink-0 mt-0.5">{s.icon}</span>
                  <div>
                    <p className={`text-sm font-semibold ${
                      s.level === 'critical' ? 'text-red-300' :
                      s.level === 'warning' ? 'text-amber-300' :
                      s.level === 'suggestion' ? 'text-blue-300' :
                      'text-neutral-300'
                    }`}>{s.title}</p>
                    <p className="text-xs text-neutral-400 mt-1 leading-relaxed">{s.detail}</p>
                  </div>
                </div>
              ))}
            </CardContent>
          )}
        </Card>
      )}

      {/* 回测记录 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
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
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-neutral-700">
                  <th className="py-3 px-2 w-8">
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
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">策略</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">合约</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">测试区间</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">提交时间</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">状态</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">总收益</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">最大回撤</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">夏普比率</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">胜率</th>
                </tr>
              </thead>
              <tbody>
                {backtests.length === 0 ? (
                  <tr>
                    <td colSpan={10} className="py-8 px-4 text-center text-neutral-400">暂无数据</td>
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
                      <td className="py-3 px-2" onClick={e => e.stopPropagation()}>
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
                      <td className="py-3 px-4 text-white text-xs">{backtest.name ?? backtest.strategy ?? backtest.payload?.strategy?.id ?? '--'}</td>
                      <td className="py-3 px-4 text-neutral-300 text-xs">{backtest.contracts ?? (backtest.payload?.symbols?.[0]) ?? '--'}</td>
                      <td className="py-3 px-4 text-neutral-400 text-xs whitespace-nowrap">
                        {backtest.payload?.start ?? '--'} ~ {backtest.payload?.end ?? '--'}
                      </td>
                      <td className="py-3 px-4 text-neutral-400 text-xs whitespace-nowrap">
                        {backtest.submitted_at ? new Date(backtest.submitted_at * 1000).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '--'}
                      </td>
                      <td className="py-3 px-4">
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
                          <Badge className={getStatusColor(backtest.status)}>
                            {getStatusText(backtest.status)}
                          </Badge>
                        )}
                      </td>
                      <td className={`py-3 px-4 font-mono text-xs ${(backtest.totalReturn ?? 0) >= 0 ? "text-red-400" : "text-green-400"}`}>
                        {backtest.totalReturn != null ? `${backtest.totalReturn >= 0 ? '+' : ''}${Number(backtest.totalReturn).toFixed(1)}%` : '--'}
                      </td>
                      <td className="py-3 px-4 text-green-400 font-mono text-xs">{backtest.maxDrawdown != null ? `-${Number(backtest.maxDrawdown).toFixed(1)}%` : '--'}</td>
                      <td className="py-3 px-4 text-white font-mono text-xs">{backtest.sharpeRatio != null ? Number(backtest.sharpeRatio).toFixed(2) : '--'}</td>
                      <td className="py-3 px-4 text-white font-mono text-xs">{backtest.winRate != null ? `${backtest.winRate}%` : '--'}</td>
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
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">
            交易明细 ({tradeDetails.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-neutral-700">
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">时间</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">合约</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">方向</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">操作</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">价格</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">数量</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">手续费</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">滑点</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">净盈亏</th>
                </tr>
              </thead>
              <tbody>
                {tradeDetails.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="py-8 px-4 text-center text-neutral-400">暂无数据</td>
                  </tr>
                ) : (
                  (() => {
                    // 前端配对计算：为 profit=null 的平仓交易计算盈亏
                    const slippagePerLot = parseFloat((selectedBacktest as any)?.payload?.params?.slippage ?? 0) || 0
                    const mult = 10 // default contract multiplier (palm oil)
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
                      <td className="py-2 px-4 text-neutral-300 font-mono text-xs">{trade.date ?? '--'}</td>
                      <td className="py-2 px-4 text-white font-mono text-xs">{trade.symbol ?? '--'}</td>
                      <td className="py-2 px-4 text-xs">
                        <span className={trade._isBuy ? 'text-red-400 font-mono' : 'text-green-400 font-mono'}>
                          {trade._isBuy ? '买' : '卖'}
                        </span>
                      </td>
                      <td className="py-2 px-4 text-xs">
                        <span className={trade._isOpen ? 'text-orange-400' : 'text-neutral-300'}>{trade._isOpen ? '开仓' : '平仓'}</span>
                      </td>
                      <td className="py-2 px-4 text-white font-mono text-xs">{trade.price ?? '--'}</td>
                      <td className="py-2 px-4 text-white font-mono text-xs">{trade.volume ?? '--'}</td>
                      <td className="py-2 px-4 text-neutral-400 font-mono text-xs">{trade.commission ?? '--'}</td>
                      <td className="py-2 px-4 text-neutral-400 font-mono text-xs">
                        {slippagePerLot > 0 ? trade._slip : <span className="text-neutral-600">—</span>}
                      </td>
                      <td className={`py-2 px-4 font-mono text-xs ${trade._computedProfit != null ? (trade._computedProfit >= 0 ? 'text-red-400' : 'text-green-400') : 'text-neutral-600'}`}>
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
