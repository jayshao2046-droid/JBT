/**
 * reportExport.ts — §6.3.3 正式报告导出工具
 *
 * 提供 formal_report_v1 格式化、验证与导出功能。
 * yaml_snapshot_hash 保障 YAML→执行→报告 三段可追溯。
 */

export interface FormalReportV1Job {
  job_id: string
  engine_type: string
  strategy_id: string
  symbol: string
  timeframe: string
  start_date: string
  end_date: string
  initial_capital: number
  yaml_snapshot_hash?: string | null
}

export interface FormalReportV1Summary {
  status: string
  total_trades: number
  final_equity: number
  max_drawdown: number
  pnl: number
  win_rate: number
  sharpe: number
}

export interface FormalReportV1 {
  schema_version: string
  report_id: string
  generated_at: string
  job: FormalReportV1Job
  summary: FormalReportV1Summary
  transaction_costs: Record<string, number | null | undefined>
  risk_events: Array<Record<string, unknown>>
  artifacts: {
    equity_curve: unknown[]
    trades: unknown[]
    positions: unknown
  }
}

/**
 * 检查报告是否包含有效的 yaml_snapshot_hash（§6.3.3 可追溯性校验）。
 */
export function hasValidSnapshotHash(report: FormalReportV1): boolean {
  const hash = report.job?.yaml_snapshot_hash
  return typeof hash === 'string' && hash.length === 64
}

/**
 * 获取报告的 yaml_snapshot_hash 简短标识（前 8 位）。
 */
export function shortHash(report: FormalReportV1): string {
  const hash = report.job?.yaml_snapshot_hash
  if (typeof hash === 'string' && hash.length >= 8) {
    return hash.slice(0, 8)
  }
  return '--'
}

/**
 * 将 formal_report_v1 格式化为可读文本摘要。
 */
export function formatReportSummary(report: FormalReportV1): string {
  const { job, summary, transaction_costs } = report
  const pnl = summary.pnl ?? (summary.final_equity - job.initial_capital)
  const totalReturn = job.initial_capital > 0
    ? ((summary.final_equity - job.initial_capital) / job.initial_capital * 100).toFixed(2)
    : '0.00'

  const lines = [
    `=== 回测报告摘要 / Backtest Report Summary ===`,
    `报告ID: ${report.report_id}`,
    `生成时间: ${report.generated_at}`,
    `Schema: ${report.schema_version}`,
    ``,
    `--- 任务信息 ---`,
    `任务ID: ${job.job_id}`,
    `引擎: ${job.engine_type}`,
    `策略: ${job.strategy_id}`,
    `合约: ${job.symbol}`,
    `周期: ${job.timeframe}`,
    `区间: ${job.start_date} ~ ${job.end_date}`,
    `初始资金: ${job.initial_capital.toLocaleString()}`,
  ]

  if (hasValidSnapshotHash(report)) {
    lines.push(`YAML快照哈希: ${job.yaml_snapshot_hash}`)
  }

  lines.push(
    ``,
    `--- 绩效摘要 ---`,
    `状态: ${summary.status}`,
    `总交易数: ${summary.total_trades}`,
    `期末权益: ${summary.final_equity.toLocaleString()}`,
    `盈亏: ${pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}`,
    `收益率: ${totalReturn}%`,
    `最大回撤: ${(summary.max_drawdown * 100).toFixed(2)}%`,
    `胜率: ${(summary.win_rate * 100).toFixed(2)}%`,
    `夏普比率: ${summary.sharpe.toFixed(4)}`,
  )

  if (transaction_costs) {
    lines.push(
      ``,
      `--- 交易成本 ---`,
      `滑点: ${transaction_costs.slippage_per_unit ?? '--'}`,
      `佣金: ${transaction_costs.commission_per_lot_round_turn ?? '--'}`,
      `总成本: ${transaction_costs.total_cost ?? '--'}`,
    )
  }

  return lines.join('\n')
}

/**
 * 触发浏览器下载 formal_report_v1 的文本摘要。
 */
export function downloadReportSummaryAsText(
  report: FormalReportV1,
  filename?: string,
): void {
  if (typeof window === 'undefined') return
  const text = formatReportSummary(report)
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename ?? `${report.job.job_id}.report.txt`
  a.click()
  URL.revokeObjectURL(url)
}
