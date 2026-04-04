"use client"

import { useEffect, useState } from "react"
import api from '@/src/utils/api'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import EmptyState from '@/components/ui/empty-state'

// 将任意格式的权益曲线数据归一化为 SVG viewBox(0 0 400 192) 的 polyline points
function normalizeEquity(data: any[]): string {
  if (!data || data.length < 2) return ""
  const values = data.map((p: any) =>
    typeof p === 'number' ? p : (p.value ?? p.equity ?? p.y ?? p.close ?? 0)
  )
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const W = 400, H = 192
  return values
    .map((v, i) => {
      const x = (i / (values.length - 1)) * W
      const y = H - ((v - min) / range) * H * 0.8 - H * 0.1
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
}

export default function CommandCenterPage() {
  const [loading, setLoading] = useState(false)
  const [apiError, setApiError] = useState<string | null>(null)
  const [summary, setSummary] = useState<any>({})
  const [results, setResults] = useState<any[]>([])
  const [equityCurve, setEquityCurve] = useState<any[]>([])
  const [marketQuotes, setMarketQuotes] = useState<any[] | null>(null)
  const [systemStatus, setSystemStatus] = useState<any>({})

  useEffect(() => {
    const load = async () => {
      try { window.dispatchEvent(new CustomEvent('backtest:loading', { detail: true })) } catch (_) {}
      setLoading(true)
      setApiError(null)
      // 全部端点并发，任意 404 静默降级不阻塞其他卡片
      const [sRes, rRes, eqRes, mqRes, syRes] = await Promise.allSettled([
        api.getSummary(),
        api.getResults(),
        api.getEquityCurve(),
        api.getMarketQuotes(),
        api.getSystemStatus(),
      ])
      if (sRes.status === 'fulfilled') setSummary(sRes.value || {})
      else setApiError(api.friendlyError(sRes.reason))
      if (rRes.status === 'fulfilled') setResults(Array.isArray(rRes.value) ? rRes.value : [])
      if (eqRes.status === 'fulfilled') setEquityCurve(Array.isArray(eqRes.value) ? eqRes.value : [])
      // market/quotes 返回 404 时保持 null（区分"未就绪"和"空列表"）
      if (mqRes.status === 'fulfilled') setMarketQuotes(Array.isArray(mqRes.value) ? mqRes.value : [])
      if (syRes.status === 'fulfilled') setSystemStatus(syRes.value || {})
      try {
        window.dispatchEvent(new CustomEvent('backtest:lastUpdate', { detail: new Date().toISOString() }))
      } catch (_) {}
      setLoading(false)
      try { window.dispatchEvent(new CustomEvent('backtest:loading', { detail: false })) } catch (_) {}
    }
    load()
    window.addEventListener('backtest:refresh', load)
    return () => window.removeEventListener('backtest:refresh', load)
  }, [])

  // 从 results 派生统计（后端 summary 字段如不存在则降级计算）
  const logs: any[] = summary.logs ?? []
  const validLogs = logs.filter((l: any) => l && l.strategy)
  const completedCount = results.filter(r => r.status === 'completed').length
  const failedCount = results.filter(r => r.status === 'failed').length
  const submittedCount = results.filter(r => r.status === 'submitted' || r.status === 'pending').length
  const equityPoints = normalizeEquity(equityCurve)

  return (
    <div className="p-6 space-y-6">
      {apiError && (
        <div className="text-sm text-red-400 bg-neutral-900 border border-red-800 p-3 rounded">
          API 错误: {apiError}
        </div>
      )}

      {/* 主仪表板网格 */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        {/* 策略分配概览 */}
        <Card className="lg:col-span-4 bg-neutral-900 border-neutral-700">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">策略分配</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-white font-mono">
                  {loading ? '—' : (summary.running_count ?? 0)}
                </div>
                <div className="text-xs text-neutral-500">运行中</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-white font-mono">
                  {loading ? '—' : (summary.standby_count ?? 0)}
                </div>
                <div className="text-xs text-neutral-500">待测试</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-white font-mono">
                  {loading ? '—' : (summary.archived_count ?? 0)}
                </div>
                <div className="text-xs text-neutral-500">已归档</div>
              </div>
            </div>
            <div className="space-y-2">
              {loading ? (
                Array.from({ length: 4 }).map((_, idx) => (
                  <div key={idx} className="h-8 bg-neutral-800 rounded animate-pulse" />
                ))
              ) : results.slice(0, 8).length > 0 ? (
                results.slice(0, 8).map((r: any, idx: number) => (
                  <div
                    key={r?.id ?? idx}
                    className="flex items-center justify-between p-2 bg-neutral-800 rounded hover:bg-neutral-700 transition-colors cursor-pointer"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
                        r?.status === 'running' || r?.status === 'active' ? 'bg-green-400'
                        : r?.status === 'completed' ? 'bg-white'
                        : r?.status === 'failed' ? 'bg-red-500'
                        : 'bg-neutral-500'
                      }`} />
                      <div>
                        <div className="text-xs text-white font-mono truncate max-w-[130px]">
                          {r?.payload?.strategy?.id ?? r?.name ?? '—'}
                        </div>
                        <div className="text-xs text-neutral-500">
                          {r?.status === 'running' ? '运行中'
                            : r?.status === 'completed' ? '已完成'
                            : r?.status === 'failed' ? '失败'
                            : r?.status === 'submitted' ? '已提交'
                            : r?.status ?? '—'}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <EmptyState title="暂无策略" description="当前没有策略，导入策略后会在此展示" icon="inbox" />
              )}
            </div>
          </CardContent>
        </Card>

        {/* 回测日志 */}
        <Card className="lg:col-span-4 bg-neutral-900 border-neutral-700">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">回测日志</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="h-8 bg-neutral-800 rounded animate-pulse" />
                ))
              ) : validLogs.length > 0 ? (
                validLogs.map((log: any, index: number) => (
                  <div
                    key={index}
                    className="text-xs border-l-2 border-orange-500 pl-3 hover:bg-neutral-800 p-2 rounded transition-colors"
                  >
                    <div className="text-neutral-500 font-mono">{log?.time ?? '—'}</div>
                    <div className="text-white">
                      {log?.strategy && (
                        <span>策略 <span className="text-orange-500 font-mono">{log.strategy}</span>{' '}</span>
                      )}
                      <span>{log?.action ?? '—'}</span>
                      {log?.contract && <span> <span className="font-mono">{log.contract}</span></span>}
                      {log?.result && (
                        <span>
                          {' '}结果:{' '}
                          <span className={`font-mono ${String(log.result).startsWith('+') ? 'text-red-400' : 'text-green-400'}`}>
                            {log.result}
                          </span>
                        </span>
                      )}
                    </div>
                  </div>
                ))
              ) : results.length > 0 ? (
                // 后端 logs 为空时降级：显示 results 列表作为日志
                results.slice(0, 8).map((r: any, i: number) => (
                  <div key={i} className="text-xs border-l-2 border-neutral-600 pl-3 p-2 rounded">
                    <div className="text-neutral-500 font-mono">{r?.id?.slice(0, 12) ?? '—'}</div>
                    <div className="text-white">
                      任务 <span className="text-orange-500 font-mono">{r?.payload?.strategy?.id ?? r?.name ?? '—'}</span>
                      {' '}{r?.status === 'failed' ? <span className="text-green-400">失败</span> : r?.status === 'completed' ? <span className="text-red-400">完成</span> : <span className="text-neutral-400">{r?.status}</span>}
                    </div>
                  </div>
                ))
              ) : (
                <EmptyState title="暂无日志" description="暂无回测日志记录" icon="inbox" />
              )}
            </div>
          </CardContent>
        </Card>

        {/* 实时行情监控 */}
        <Card className="lg:col-span-4 bg-neutral-900 border-neutral-700">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">实时行情监控</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center">
            <div className="relative w-32 h-32 mb-4">
              <div className="absolute inset-0 border-2 border-white rounded-full opacity-60 animate-pulse"></div>
              <div className="absolute inset-2 border border-white rounded-full opacity-40"></div>
              <div className="absolute inset-4 border border-white rounded-full opacity-20"></div>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-full h-px bg-white opacity-30"></div>
              </div>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-px h-full bg-white opacity-30"></div>
              </div>
            </div>
            <div className="text-xs text-neutral-500 space-y-1 w-full font-mono">
              {loading ? (
                <div className="text-neutral-400 text-center">正在加载行情数据...</div>
              ) : marketQuotes === null ? (
                // null = 端点 404，接口未就绪
                <div className="text-neutral-600 text-center py-2">行情接口暂未就绪</div>
              ) : marketQuotes.length === 0 ? (
                <div className="text-neutral-600 text-center py-2">暂无行情数据</div>
              ) : (
                marketQuotes.slice(0, 5).map((q: any, i: number) => (
                  <div key={i} className="flex justify-between">
                    <span className="text-orange-500">{q.symbol ?? q.code ?? '—'}</span>
                    <span className={typeof q.change === 'number'
                      ? (q.change >= 0 ? 'text-red-400' : 'text-green-400')
                      : 'text-white'}>
                      {q.price ?? q.last ?? '—'}
                      {typeof q.change === 'number'
                        ? ` (${q.change >= 0 ? '+' : ''}${q.change.toFixed(2)}%)`
                        : ''}
                    </span>
                  </div>
                ))
              )}
              {summary.market_time && (
                <div className="text-neutral-600 mt-1 text-center">{summary.market_time}</div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* 收益曲线图表 */}
        <Card className="lg:col-span-8 bg-neutral-900 border-neutral-700">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">收益曲线概览</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-48 relative">
              {/* 背景网格 */}
              <div className="absolute inset-0 grid grid-cols-8 grid-rows-6 opacity-20">
                {Array.from({ length: 48 }).map((_, i) => (
                  <div key={i} className="border border-neutral-700"></div>
                ))}
              </div>
              {/* SVG 曲线 */}
              <svg
                className="absolute inset-0 w-full h-full"
                viewBox="0 0 400 192"
                preserveAspectRatio="none"
              >
                {equityPoints ? (
                  <polyline
                    points={equityPoints}
                    fill="none"
                    stroke="#f97316"
                    strokeWidth="2"
                  />
                ) : (
                  // 无数据：虚线占位曲线
                  <polyline
                    points="0,140 50,120 100,130 150,110 200,115 250,105 300,120 350,100 400,92"
                    fill="none"
                    stroke="#374151"
                    strokeWidth="2"
                    strokeDasharray="6,4"
                  />
                )}
              </svg>
              {!equityPoints && !loading && (
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <span className="text-xs text-neutral-600">暂无收益曲线数据</span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* 回测统计 */}
        <Card className="lg:col-span-4 bg-neutral-900 border-neutral-700">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">回测统计</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-2 h-2 bg-white rounded-full"></div>
                  <span className="text-xs text-white font-medium">完成情况</span>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-neutral-400">已完成</span>
                    <span className="text-red-400 font-bold font-mono">{loading ? '—' : completedCount}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-neutral-400">已失败</span>
                    <span className="text-green-400 font-bold font-mono">{loading ? '—' : failedCount}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-neutral-400">待执行</span>
                    <span className="text-white font-bold font-mono">{loading ? '—' : submittedCount}</span>
                  </div>
                  <div className="flex justify-between text-xs border-t border-neutral-700 pt-2 mt-2">
                    <span className="text-neutral-400">合计</span>
                    <span className="text-white font-bold font-mono">{loading ? '—' : results.length}</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 系统状态行（来自 /api/system/status）*/}
      {(systemStatus.cpu !== undefined || loading) && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'CPU 使用率', value: systemStatus.cpu, unit: '%', warn: 80 },
            { label: '内存使用率', value: systemStatus.memory, unit: '%', warn: 85 },
            { label: '磁盘使用率', value: systemStatus.disk, unit: '%', warn: 90 },
            { label: '网络延迟', value: systemStatus.latency, unit: 'ms', warn: 200 },
          ].map(({ label, value, unit, warn }) => (
            <Card key={label} className="bg-neutral-900 border-neutral-700">
              <CardContent className="p-4">
                <p className="text-xs text-neutral-400 tracking-wider mb-1">{label}</p>
                <p className={`text-xl font-bold font-mono ${
                  loading ? 'text-neutral-500'
                  : value !== undefined && value > warn ? 'text-red-400'
                  : 'text-white'
                }`}>
                  {loading ? '—'
                   : value !== undefined
                     ? `${typeof value === 'number' ? value.toFixed(1) : value}${unit}`
                     : '--'}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
