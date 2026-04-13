"use client"

import { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Switch } from "@/components/ui/switch"
import {
  Server, Database, Clock, CheckCircle, XCircle, Settings, HardDrive,
  Link2, RefreshCw, AlertCircle,
} from "lucide-react"

interface ServiceInfo { name: string; version: string; python_version: string; runtime: string; data_root: string; api_port: number; environment: string }
interface EnvEntry { key: string; configured: boolean }
interface ConnEntry { name: string; status: string; configured: boolean }
interface SchedEntry { collector_key?: string; name: string; schedule?: string; type?: string; endpoint_count?: number }
interface StorageTotals { size_bytes: number; size_human: string; files: number; directories: number; last_modified: string|null }
interface StorageDir { name: string; path: string; size_human: string; file_count: number; dir_count: number; last_modified: string|null }

export default function SettingsPage({ refreshNonce }: { refreshNonce?: number }) {
  const [isLoading, setIsLoading] = useState(true)
  const [fetchError, setFetchError] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [lastUpdate, setLastUpdate] = useState("")
  const [service, setService] = useState<ServiceInfo|null>(null)
  const [envList, setEnvList] = useState<EnvEntry[]>([])
  const [connections, setConnections] = useState<ConnEntry[]>([])
  const [schedules, setSchedules] = useState<SchedEntry[]>([])
  const [totals, setTotals] = useState<StorageTotals|null>(null)
  const [dirs, setDirs] = useState<StorageDir[]>([])

  const fetchData = useCallback(async () => {
    try {
      const [sysR, stoR] = await Promise.all([
        fetch("/api/data/api/v1/dashboard/system"),
        fetch("/api/data/api/v1/dashboard/storage"),
      ])
      if (!sysR.ok || !stoR.ok) throw new Error("fail")
      const sys = await sysR.json()
      const sto = await stoR.json()
      setService(sys.service ?? null)
      setEnvList(sys.settings?.env ?? [])
      setConnections(sys.settings?.connections ?? [])
      setSchedules(sys.settings?.schedules ?? [])
      setTotals(sto.totals ?? null)
      setDirs((sto.directories ?? []).slice(0, 12))
      setLastUpdate(new Date().toLocaleTimeString("zh-CN"))
      setFetchError(false)
    } catch { setFetchError(true) }
    finally { setIsLoading(false) }
  }, [])

  useEffect(() => { fetchData() }, [refreshNonce, fetchData])
  useEffect(() => { if (!autoRefresh) return; const t=setInterval(fetchData,30000); return ()=>clearInterval(t) }, [autoRefresh, fetchData])

  if (isLoading) return <div className="p-6 space-y-6"><Skeleton className="h-12 w-64 bg-neutral-800" /><Skeleton className="h-40 bg-neutral-800" /><Skeleton className="h-96 bg-neutral-800" /></div>
  if (fetchError) return <div className="flex flex-col items-center justify-center h-full py-24 text-neutral-500"><AlertCircle className="w-10 h-10 mb-3 text-red-500/60" /><p className="text-sm mb-4">数据加载失败</p><Button variant="outline" size="sm" onClick={fetchData} className="border-neutral-700 text-neutral-400">重新加载</Button></div>

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold text-white">配置与设置</h1><p className="text-sm text-neutral-400 mt-1">只读展示当前运行配置和系统结构</p></div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2"><span className="text-xs text-neutral-500">自动刷新</span><Switch checked={autoRefresh} onCheckedChange={setAutoRefresh} /></div>
          {lastUpdate && <span className="text-xs text-neutral-500 flex items-center gap-1"><Clock className="w-3 h-3" />{lastUpdate}</span>}
          <Button variant="outline" size="sm" onClick={fetchData} className="border-neutral-700 text-neutral-300"><RefreshCw className="w-4 h-4 mr-2" />刷新</Button>
        </div>
      </div>

      {/* Service Info */}
      <Card className="bg-neutral-900 border-neutral-800">
        <CardHeader className="pb-3"><CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider flex items-center gap-2"><Server className="w-4 h-4 text-orange-500" />服务信息</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { l: "服务名称", v: service?.name },
              { l: "版本号", v: service?.version, c: "text-orange-400 font-mono" },
              { l: "Python 版本", v: service?.python_version, c: "font-mono" },
              { l: "运行时", v: service?.runtime },
              { l: "数据目录", v: service?.data_root, c: "font-mono truncate" },
              { l: "API 端口", v: service?.api_port, c: "text-orange-400 font-mono" },
              { l: "运行环境", v: service?.environment },
            ].map((item, i) => (
              <div key={i}><p className="text-xs text-neutral-500 mb-1">{item.l}</p><p className={`text-sm text-white ${item.c || ""}`}>{item.v ?? "\u2014"}</p></div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Schedules + Env */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-3"><CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider flex items-center gap-2"><Clock className="w-4 h-4 text-orange-500" />调度计划 <span className="ml-auto text-xs text-neutral-500 font-normal">{schedules.length} 个</span></CardTitle></CardHeader>
          <CardContent>
            {schedules.length === 0 ? <p className="text-sm text-neutral-500 text-center py-6">暂无调度</p> : (
              <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                {schedules.map((s, i) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-neutral-800/50 rounded-lg">
                    <div>
                      <p className="text-sm text-white">{s.name}</p>
                      <p className="text-xs text-neutral-500 font-mono">{s.schedule ?? "\u2014"}</p>
                    </div>
                    <div className="text-right flex items-center gap-2">
                      {s.collector_key && <span className="text-xs text-orange-400 font-mono">{s.collector_key.toUpperCase()}</span>}
                      {s.endpoint_count != null && <Badge variant="outline" className="text-xs border-blue-500/30 text-blue-400">{s.endpoint_count} 端点</Badge>}
                      <Badge variant="outline" className="text-xs border-neutral-600 text-neutral-400">{s.type ?? "cron"}</Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-3"><CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider flex items-center gap-2"><Settings className="w-4 h-4 text-orange-500" />环境变量 <span className="ml-auto text-xs text-neutral-500 font-normal">{envList.length} 项</span></CardTitle></CardHeader>
          <CardContent>
            {envList.length === 0 ? <p className="text-sm text-neutral-500 text-center py-6">暂无</p> : (
              <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                {envList.map((e, i) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-neutral-800/50 rounded-lg">
                    <p className="text-sm text-white font-mono">{e.key}</p>
                    {e.configured ? <div className="flex items-center gap-1.5 text-green-400"><CheckCircle className="w-4 h-4" /><span className="text-xs">已配置</span></div> : <div className="flex items-center gap-1.5 text-neutral-500"><XCircle className="w-4 h-4" /><span className="text-xs">未配置</span></div>}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Connections */}
      <Card className="bg-neutral-900 border-neutral-800">
        <CardHeader className="pb-3"><CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider flex items-center gap-2"><Link2 className="w-4 h-4 text-orange-500" />数据源连接</CardTitle></CardHeader>
        <CardContent>
          {connections.length === 0 ? <p className="text-sm text-neutral-500 text-center py-6">暂无</p> : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
              {connections.map((c, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-neutral-800/50 rounded-lg border border-neutral-800">
                  <div className="flex items-center gap-2"><Database className="w-4 h-4 text-blue-400" /><span className="text-sm text-white">{c.name}</span></div>
                  {c.configured && c.status === "connected" ? <CheckCircle className="w-4 h-4 text-green-500" /> : c.status === "disabled" ? <XCircle className="w-4 h-4 text-neutral-500" /> : <Badge variant="outline" className="text-xs border-yellow-500/30 text-yellow-400">{c.status}</Badge>}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Storage */}
      <Card className="bg-neutral-900 border-neutral-800">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider flex items-center gap-2"><HardDrive className="w-4 h-4 text-orange-500" />存储概览</CardTitle>
            {totals && <div className="flex items-center gap-4 text-xs text-neutral-400"><span>总计: <span className="text-white font-mono">{totals.size_human}</span></span><span>文件: <span className="text-white font-mono">{totals.files.toLocaleString()}</span></span><span>目录: <span className="text-white font-mono">{totals.directories}</span></span></div>}
          </div>
        </CardHeader>
        <CardContent>
          {dirs.length === 0 ? <p className="text-sm text-neutral-500 text-center py-6">暂无</p> : (
            <div className="space-y-2">
              {dirs.map((d, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-neutral-800/50 rounded-lg">
                  <div className="flex items-center gap-3"><HardDrive className="w-4 h-4 text-neutral-500" /><div><p className="text-sm text-white font-mono">{d.path || d.name}</p><p className="text-xs text-neutral-500">{d.file_count} 文件{d.dir_count > 0 ? ` · ${d.dir_count} 目录` : ""}</p></div></div>
                  <div className="text-right"><p className="text-sm text-white font-mono">{d.size_human}</p>{d.last_modified && <p className="text-xs text-neutral-500">{d.last_modified.slice(11,19)}</p>}</div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
