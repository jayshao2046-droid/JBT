"use client"

import { useState, useEffect } from "react"
import api from '@/src/utils/api'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Clock, RefreshCw, Cpu, MemoryStick, HardDrive, Network } from "lucide-react"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import EmptyState from '@/components/ui/empty-state'

export default function SystemStatusPage() {
  const [selectedSystem, setSelectedSystem] = useState(null)
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(new Date())
  const [apiError, setApiError] = useState(null)
  const [cpuHistory, setCpuHistory] = useState([])
  const [memoryHistory, setMemoryHistory] = useState([])
  const [services, setServices] = useState([])
  const [systemLogs, setSystemLogs] = useState([])
  const [statusSummary, setStatusSummary] = useState<{ cpu?: number | null; memory?: number | null; disk?: number | null; latency?: number | null }>({})

  // helper to normalize history series into {x,y} points for Recharts
  const normalizeSeries = (series: any[]) => {
    if (!Array.isArray(series) || series.length === 0) return []
    if (typeof series[0] === 'number') return series.map((v, i) => ({ x: i, y: v }))
    return series.map((p: any, i: number) => ({ x: p.time ?? i, y: p.value ?? p.v ?? p.cpu ?? p.memory ?? 0 }))
  }

  useEffect(() => {
    const load = async () => {
      setIsLoading(true)
      setApiError(null)
      try {
        // 使用 api 统一封装（BASE 已自动处理相对/绝对路径）
        const [statusJson, logsRaw] = await Promise.all([
          api.getSystemStatus(),
          api.getSystemLogs(),
        ])

        setCpuHistory((statusJson && statusJson.cpuHistory) || [])
        setMemoryHistory((statusJson && statusJson.memoryHistory) || [])
        setServices((statusJson && statusJson.services) || [])
        // logs 端点返回 JSON 字符串或数组；统一转为非空行数组
        let logsArr: string[] = []
        if (Array.isArray(logsRaw)) {
          logsArr = logsRaw.map((l: any) => String(l)).filter(Boolean)
        } else if (typeof logsRaw === 'string' && logsRaw.trim() && logsRaw.trim() !== '""') {
          logsArr = logsRaw.split('\n').map(l => l.trim()).filter(Boolean)
        }
        setSystemLogs(logsArr)
        // summary metrics (may be missing in some backends)
        setStatusSummary({
          cpu: statusJson?.cpu ?? null,
          memory: statusJson?.memory ?? null,
          disk: statusJson?.disk ?? null,
          latency: statusJson?.latency ?? null,
        })
        const now = new Date()
        setLastUpdate(now)
        try { window.dispatchEvent(new CustomEvent('backtest:lastUpdate', { detail: now.toISOString() })) } catch (err) {}
      } catch (e) {
        console.error(e)
        setApiError(api.friendlyError ? api.friendlyError(e) : String(e))
      } finally {
        setIsLoading(false)
      }
    }

    load()
    const onRefresh = () => load()
    window.addEventListener('backtest:refresh', onRefresh)
    return () => window.removeEventListener('backtest:refresh', onRefresh)
  }, [])

  // auto-refresh when enabled (every 10s)
  useEffect(() => {
    if (!autoRefresh) return
    const id = setInterval(() => {
      try { window.dispatchEvent(new CustomEvent('backtest:loading', { detail: true })) } catch (e) {}
      handleRefresh()
    }, 10000)
    return () => clearInterval(id)
  }, [autoRefresh])

  const handleRefresh = async () => {
    setIsLoading(true)
    setApiError(null)
    try {
      const [statusJson, logsRaw] = await Promise.all([
        api.getSystemStatus(),
        api.getSystemLogs(),
      ])
      setCpuHistory((statusJson && statusJson.cpuHistory) || [])
      setMemoryHistory((statusJson && statusJson.memoryHistory) || [])
      setServices((statusJson && statusJson.services) || [])
      let logsArr: string[] = []
      if (Array.isArray(logsRaw)) {
        logsArr = logsRaw.map((l: any) => String(l)).filter(Boolean)
      } else if (typeof logsRaw === 'string' && logsRaw.trim() && logsRaw.trim() !== '""') {
        logsArr = logsRaw.split('\n').map(l => l.trim()).filter(Boolean)
      }
      setSystemLogs(logsArr)
      setStatusSummary({
        cpu: statusJson?.cpu ?? null,
        memory: statusJson?.memory ?? null,
        disk: statusJson?.disk ?? null,
        latency: statusJson?.latency ?? null,
      })
      const now = new Date()
      setLastUpdate(now)
      try { window.dispatchEvent(new CustomEvent('backtest:lastUpdate', { detail: now.toISOString() })) } catch (err) {}
    } catch (e) {
      console.error(e)
      setApiError(api.friendlyError ? api.friendlyError(e) : String(e))
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusColor = (status) => {
    if (status === 'running') return 'bg-green-600 text-white'
    if (status === 'warning') return 'bg-yellow-600 text-white'
    return 'bg-red-600 text-white'
  }

  const getStatusIcon = (status) => {
    if (status === 'running') return <CheckIcon />
    if (status === 'warning') return <AlertIcon />
    return <AlertIcon />
  }

  // lightweight icon placeholders
  function CheckIcon() { return <span className="text-green-400">●</span> }
  function AlertIcon() { return <span className="text-yellow-400">●</span> }

  return (
    <div className="p-6 space-y-6">
      {apiError && <div className="text-sm text-red-400 bg-neutral-900 border border-red-800 p-3 rounded">API 错误: {apiError}</div>}
      {isLoading && <div className="text-sm text-neutral-300 bg-neutral-800 border border-neutral-700 p-3 rounded">加载中……</div>}

      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wider">系统状态</h1>
          <p className="text-sm text-neutral-400">监控本地资源使用情况和服务状态</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setAutoRefresh(!autoRefresh)} className={autoRefresh ? 'bg-green-600' : 'bg-neutral-700'}>
            <Clock className="w-4 h-4 mr-2" />{autoRefresh ? '自动刷新中' : '自动刷新关闭'}
          </Button>
          <Button onClick={handleRefresh} variant="outline"><RefreshCw className="w-4 h-4" /></Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <p className="text-xs text-neutral-400 tracking-wider">CPU 使用率</p>
            <p className="text-2xl font-bold text-white">{statusSummary.cpu !== null && statusSummary.cpu !== undefined ? `${statusSummary.cpu}%` : (isLoading ? '—' : '--')}</p>
            {Array.isArray(cpuHistory) && cpuHistory.length > 0 ? (
              <div style={{ width: '100%', height: 60 }}>
                <ResponsiveContainer width="100%" height={60}>
                  <LineChart data={normalizeSeries(cpuHistory)} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                    <XAxis dataKey="x" hide />
                    <YAxis hide domain={["dataMin", "dataMax"]} />
                    <Tooltip wrapperStyle={{ color: '#000' }} />
                    <Line type="monotone" dataKey="y" stroke="#f97316" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <Progress value={typeof statusSummary.cpu === 'number' ? Math.max(0, Math.min(100, statusSummary.cpu)) : 0} className="h-2" />
            )}
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <p className="text-xs text-neutral-400 tracking-wider">内存使用率</p>
            <p className="text-2xl font-bold text-white">{statusSummary.memory !== null && statusSummary.memory !== undefined ? `${statusSummary.memory}%` : (isLoading ? '—' : '--')}</p>
            {Array.isArray(memoryHistory) && memoryHistory.length > 0 ? (
              <div style={{ width: '100%', height: 60 }}>
                <ResponsiveContainer width="100%" height={60}>
                  <LineChart data={normalizeSeries(memoryHistory)} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                    <XAxis dataKey="x" hide />
                    <YAxis hide domain={["dataMin", "dataMax"]} />
                    <Tooltip wrapperStyle={{ color: '#000' }} />
                    <Line type="monotone" dataKey="y" stroke="#60a5fa" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <Progress value={typeof statusSummary.memory === 'number' ? Math.max(0, Math.min(100, statusSummary.memory)) : 0} className="h-2" />
            )}
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <p className="text-xs text-neutral-400 tracking-wider">磁盘使用率</p>
            <p className="text-2xl font-bold text-white">{statusSummary.disk !== null && statusSummary.disk !== undefined ? `${statusSummary.disk}%` : (isLoading ? '—' : '--')}</p>
            <Progress value={typeof statusSummary.disk === 'number' ? Math.max(0, Math.min(100, statusSummary.disk)) : 0} className="h-2" />
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <p className="text-xs text-neutral-400 tracking-wider">网络延迟</p>
            <p className="text-2xl font-bold text-white">{statusSummary.latency !== null && statusSummary.latency !== undefined ? `${statusSummary.latency}ms` : (isLoading ? '—' : '--')}</p>
            <p className={`text-xs ${typeof statusSummary.latency === 'number' && statusSummary.latency > 200 ? 'text-red-400' : 'text-green-400'}`}>{typeof statusSummary.latency === 'number' ? (statusSummary.latency > 200 ? '高延迟' : '正常') : ''}</p>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">服务状态</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-neutral-700">
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">服务名称</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">状态</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">运行时长</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">请求数</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">延迟 (ms)</th>
                </tr>
              </thead>
              <tbody>
                {services.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 px-4 text-center text-neutral-400">暂无数据</td>
                  </tr>
                ) : (
                  services.map((service, i) => (
                    <tr key={service.id || i} className={`border-b border-neutral-800 hover:bg-neutral-800 ${i % 2 === 0 ? 'bg-neutral-900' : 'bg-neutral-850'}`} onClick={() => setSelectedSystem(service)}>
                      <td className="py-3 px-4 text-white">{service.name}</td>
                      <td className="py-3 px-4"><Badge className={getStatusColor(service.status)}>{service.status}</Badge></td>
                      <td className="py-3 px-4 text-neutral-300 font-mono">{service.uptime}</td>
                      <td className="py-3 px-4 text-white font-mono">{service.requests}</td>
                      <td className={`py-3 px-4 font-mono ${service.latency > 50 ? 'text-red-400' : 'text-green-400'}`}>{service.latency}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">系统日志</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-black rounded border border-neutral-800 p-4 h-64 overflow-y-auto font-mono text-xs space-y-1">
            {isLoading ? <div className="text-neutral-400">加载中...</div> : systemLogs.length === 0 ? <EmptyState title="暂无日志" description="暂无系统日志" icon="inbox" /> : systemLogs.map((log, idx) => <div key={idx} className={log.includes('[ERROR]') ? 'text-red-400' : log.includes('[WARNING]') ? 'text-yellow-400' : 'text-green-400'}>{log}</div>)}
          </div>
        </CardContent>
      </Card>

      {selectedSystem && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onClick={() => setSelectedSystem(null)}>
          <Card className="bg-neutral-900 border-neutral-700 w-full max-w-md">
            <CardHeader>
              <div className="flex justify-between items-start">
                <CardTitle className="text-lg font-bold text-white">{selectedSystem.name}</CardTitle>
                <Button variant="ghost" onClick={() => setSelectedSystem(null)} className="text-neutral-400 hover:text-white">✕</Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-xs text-neutral-500 mb-1">服务状态</p>
                <Badge className={getStatusColor(selectedSystem.status)}>{selectedSystem.status}</Badge>
              </div>
              <div>
                <p className="text-xs text-neutral-500 mb-1">运行时长</p>
                <p className="text-sm text-white font-mono">{selectedSystem.uptime}</p>
              </div>
              <div>
                <p className="text-xs text-neutral-500 mb-1">请求数</p>
                <p className="text-sm text-white font-mono">{selectedSystem.requests}</p>
              </div>
              <div>
                <p className="text-xs text-neutral-500 mb-1">平均延迟</p>
                <p className={`text-sm font-mono ${selectedSystem.latency > 50 ? 'text-red-400' : 'text-green-400'}`}>{selectedSystem.latency}ms</p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
