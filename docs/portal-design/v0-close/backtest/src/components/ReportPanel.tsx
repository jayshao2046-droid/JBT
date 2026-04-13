"use client"

import { useCallback } from "react"

interface FormalReportV1 {
  schema_version: string
  report_id: string
  generated_at: string
  job: {
    job_id: string
    engine_type: string
    strategy_id: string
    symbol: string
    timeframe: string
    start_date: string
    end_date: string
    initial_capital: number
  }
  summary: {
    status: string
    total_trades: number
    final_equity: number
    max_drawdown: number
    pnl: number
    win_rate: number
    sharpe: number
  }
  transaction_costs: {
    slippage_per_unit?: number | null
    commission_per_lot_round_turn?: number | null
    total_cost?: number | null
  }
  risk_events: Array<{
    event_id: string
    engine_type: string
    trigger_reason: string
    threshold: any
    observed: any
    event_time: string
  }>
  artifacts: {
    equity_curve: any[]
    trades: any[]
    positions: any
  }
}

interface ReportPanelProps {
  taskId: string
  report: FormalReportV1
  strategyName?: string
  baseUrl?: string
}

function formatNumber(val: number | null | undefined, decimals = 2): string {
  if (val == null || !isFinite(val)) return "--"
  return val.toFixed(decimals)
}

function formatPercent(val: number | null | undefined, decimals = 2): string {
  if (val == null || !isFinite(val)) return "--"
  return `${(val * 100).toFixed(decimals)}%`
}

function resolveThreshold(val: any): string {
  if (val == null) return "--"
  if (typeof val === "object" && val.value != null) return `${val.name || ""} ${formatNumber(val.value, 4)}`
  return String(val)
}

function resolveObserved(val: any): string {
  if (val == null) return "--"
  if (typeof val === "object" && val.value != null) return `${val.name || ""} ${formatNumber(val.value, 4)}`
  return String(val)
}

export default function ReportPanel({ taskId, report, strategyName, baseUrl = "" }: ReportPanelProps) {
  const { summary, transaction_costs, risk_events, job } = report

  const handleDownloadJSON = useCallback(async () => {
    try {
      const resp = await fetch(`${baseUrl}/api/backtest/results/${encodeURIComponent(taskId)}/report`)
      if (!resp.ok) throw new Error(`${resp.status}`)
      const blob = await resp.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `${(strategyName || taskId).replace(/[^\w.-]+/g, "_")}_${taskId}.report.json`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      console.error("JSON download failed:", e)
    }
  }, [taskId, strategyName, baseUrl])

  const handleDownloadCSV = useCallback(async () => {
    try {
      const resp = await fetch(`${baseUrl}/api/backtest/results/${encodeURIComponent(taskId)}/report/csv`)
      if (!resp.ok) throw new Error(`${resp.status}`)
      const blob = await resp.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `${(strategyName || taskId).replace(/[^\w.-]+/g, "_")}_${taskId}.report.csv`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      console.error("CSV download failed:", e)
    }
  }, [taskId, strategyName, baseUrl])

  const totalReturn = job.initial_capital > 0
    ? ((summary.final_equity - job.initial_capital) / job.initial_capital)
    : 0
  const returnColor = totalReturn >= 0 ? "text-red-400" : "text-green-400"

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-neutral-200 tracking-wider">
            📊 回测报告 / Backtest Report
          </h3>
          <p className="text-[10px] text-neutral-500 mt-0.5">
            {report.report_id} · {job.engine_type} · {report.generated_at?.slice(0, 19)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleDownloadJSON}
            className="text-[10px] px-2.5 py-1 rounded border border-neutral-600 text-neutral-300 hover:bg-neutral-800 hover:text-white transition-colors"
          >
            ⬇ JSON
          </button>
          <button
            onClick={handleDownloadCSV}
            className="text-[10px] px-2.5 py-1 rounded border border-neutral-600 text-neutral-300 hover:bg-neutral-800 hover:text-white transition-colors"
          >
            ⬇ CSV
          </button>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
        {[
          { label: "收益率", value: formatPercent(totalReturn), color: returnColor },
          { label: "夏普比率", value: formatNumber(summary.sharpe, 4), color: "text-blue-400" },
          { label: "最大回撤", value: formatPercent(summary.max_drawdown), color: "text-amber-400" },
          { label: "胜率", value: formatPercent(summary.win_rate), color: "text-purple-400" },
          { label: "盈亏", value: formatNumber(summary.pnl), color: summary.pnl >= 0 ? "text-red-400" : "text-green-400" },
          { label: "总交易数", value: String(summary.total_trades), color: "text-neutral-300" },
        ].map((m) => (
          <div key={m.label} className="bg-neutral-800/60 rounded-lg p-2 border border-neutral-700/50 text-center">
            <p className="text-[10px] text-neutral-500">{m.label}</p>
            <p className={`text-sm font-mono font-semibold ${m.color}`}>{m.value}</p>
          </div>
        ))}
      </div>

      {/* Transaction Costs */}
      <div className="bg-neutral-800/40 rounded-lg p-2.5 border border-neutral-700/40">
        <p className="text-[10px] font-medium text-neutral-400 mb-1.5">交易成本 / Transaction Costs</p>
        <div className="grid grid-cols-3 gap-3 text-[11px]">
          <div>
            <span className="text-neutral-500">滑点/Slippage:</span>{" "}
            <span className="text-neutral-300 font-mono">{formatNumber(transaction_costs.slippage_per_unit ?? null, 2)}</span>
          </div>
          <div>
            <span className="text-neutral-500">佣金/Commission:</span>{" "}
            <span className="text-neutral-300 font-mono">{formatNumber(transaction_costs.commission_per_lot_round_turn ?? null, 2)}</span>
          </div>
          <div>
            <span className="text-neutral-500">总成本/Total:</span>{" "}
            <span className="text-neutral-300 font-mono">{formatNumber(transaction_costs.total_cost ?? null, 2)}</span>
          </div>
        </div>
      </div>

      {/* Risk Events */}
      {risk_events && risk_events.length > 0 && (
        <div className="bg-neutral-800/40 rounded-lg p-2.5 border border-amber-700/30">
          <p className="text-[10px] font-medium text-amber-400 mb-1.5">
            ⚠️ 风控事件 / Risk Events ({risk_events.length})
          </p>
          <div className="space-y-1 max-h-40 overflow-y-auto">
            {risk_events.map((evt, idx) => (
              <div key={evt.event_id || idx} className="flex items-start gap-2 text-[10px] bg-neutral-900/50 rounded p-1.5">
                <span className="text-amber-500 font-mono flex-shrink-0">{evt.event_id}</span>
                <span className="text-neutral-400">{evt.trigger_reason}</span>
                <span className="text-neutral-500 ml-auto flex-shrink-0">
                  阈值: {resolveThreshold(evt.threshold)} · 实际: {resolveObserved(evt.observed)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
      {(!risk_events || risk_events.length === 0) && (
        <div className="bg-neutral-800/40 rounded-lg p-2 border border-neutral-700/40">
          <p className="text-[10px] text-neutral-500">✅ 无风控事件 / No risk events triggered</p>
        </div>
      )}
    </div>
  )
}
