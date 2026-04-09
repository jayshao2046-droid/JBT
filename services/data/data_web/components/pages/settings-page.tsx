"use client"

import { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Server,
  Database,
  Clock,
  CheckCircle,
  XCircle,
  Settings,
  HardDrive,
  Link2,
  RefreshCw,
  AlertCircle,
} from "lucide-react"

interface ServiceInfo {
  name: string
  version: string
  python_version: string
  runtime: string
  data_root: string
  api_port: number
  environment: string
}

interface EnvEntry {
  key: string
  configured: boolean
}

interface ConnectionEntry {
  name: string
  status: string
  configured: boolean
}

interface ScheduleEntry {
  name: string
  expr?: string
  schedule_expr?: string
  type?: string
  schedule_type?: string
  next_run?: string
}

interface StorageDirectory {
  name: string
  path: string
  type: string
  size_human: string
  file_count: number
  dir_count: number
  last_modified: string | null
}

interface StorageTotals {
  size_bytes: number
  size_human: string
  files: number
  directories: number
  last_modified: string | null
  truncated: boolean
}

interface SystemResponse {
  service: ServiceInfo
  settings: {
    env: EnvEntry[]
    connections: ConnectionEntry[]
    schedules: ScheduleEntry[]
  }
}

interface StorageResponse {
  totals: StorageTotals
  directories: StorageDirectory[]
}

export default function SettingsPage({ refreshNonce }: { refreshNonce?: number }) {
  const [isLoading, setIsLoading] = useState(true)
  const [fetchError, setFetchError] = useState(false)
  const [service, setService] = useState<ServiceInfo | null>(null)
  const [envList, setEnvList] = useState<EnvEntry[]>([])
  const [connections, setConnections] = useState<ConnectionEntry[]>([])
  const [schedules, setSchedules] = useState<ScheduleEntry[]>([])
  const [storageTotals, setStorageTotals] = useState<StorageTotals | null>(null)
  const [storageDirectories, setStorageDirectories] = useState<StorageDirectory[]>([])

  const fetchData = useCallback(async () => {
    setIsLoading(true)
    setFetchError(false)
    try {
      const [sysRes, storeRes] = await Promise.all([
        fetch("/api/data/api/v1/dashboard/system"),
        fetch("/api/data/api/v1/dashboard/storage"),
      ])
      if (!sysRes.ok || !storeRes.ok) throw new Error("fetch failed")
      const sysData: SystemResponse = await sysRes.json()
      const storeData: StorageResponse = await storeRes.json()
      setService(sysData.service ?? null)
      setEnvList(sysData.settings?.env ?? [])
      setConnections(sysData.settings?.connections ?? [])
      setSchedules(sysData.settings?.schedules ?? [])
      setStorageTotals(storeData.totals ?? null)
      setStorageDirectories((storeData.directories ?? []).slice(0, 10))
    } catch {
      setFetchError(true)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [refreshNonce, fetchData])

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-12 w-64 bg-neutral-800" />
        <Skeleton className="h-40 bg-neutral-800" />
        <Skeleton className="h-96 bg-neutral-800" />
      </div>
    )
  }

  if (fetchError) {
    return (
      <div className="flex flex-col items-center justify-center h-full py-24 text-neutral-500">
        <AlertCircle className="w-10 h-10 mb-3 text-red-500/60" />
        <p className="text-sm mb-4">数据加载失败，请稍后重试</p>
        <Button variant="outline" size="sm" onClick={fetchData} className="border-neutral-700 text-neutral-400">
          重新加载
        </Button>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* 页面头部 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">配置与设置</h1>
          <p className="text-sm text-neutral-400 mt-1">
            只读展示当前运行配置和系统结构，帮助快速排查问题
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchData} className="border-neutral-700 text-neutral-300">
          <RefreshCw className="w-4 h-4 mr-2" />
          刷新
        </Button>
      </div>

      {/* 服务信息卡 */}
      <Card className="bg-neutral-900 border-neutral-800">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider flex items-center gap-2">
            <Server className="w-4 h-4 text-orange-500" />
            服务信息
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-neutral-500 mb-1">服务名称</p>
              <p className="text-sm text-white font-medium">{service?.name ?? "—"}</p>
            </div>
            <div>
              <p className="text-xs text-neutral-500 mb-1">版本号</p>
              <p className="text-sm text-orange-400 font-mono">{service?.version ?? "—"}</p>
            </div>
            <div>
              <p className="text-xs text-neutral-500 mb-1">Python 版本</p>
              <p className="text-sm text-white font-mono">{service?.python_version ?? "—"}</p>
            </div>
            <div>
              <p className="text-xs text-neutral-500 mb-1">运行时</p>
              <p className="text-sm text-white">{service?.runtime ?? "—"}</p>
            </div>
            <div>
              <p className="text-xs text-neutral-500 mb-1">数据目录</p>
              <p className="text-sm text-white font-mono truncate">{service?.data_root ?? "—"}</p>
            </div>
            <div>
              <p className="text-xs text-neutral-500 mb-1">API 端口</p>
              <p className="text-sm text-orange-400 font-mono">{service?.api_port ?? "—"}</p>
            </div>
            <div>
              <p className="text-xs text-neutral-500 mb-1">运行环境</p>
              <Badge
                variant="outline"
                className={service?.environment === "production"
                  ? "border-green-500/30 text-green-400"
                  : "border-yellow-500/30 text-yellow-400"}
              >
                {service?.environment ?? "—"}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 2列：调度计划 + 环境变量 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 调度计划 */}
        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider flex items-center gap-2">
              <Clock className="w-4 h-4 text-orange-500" />
              调度计划
              <span className="ml-auto text-xs text-neutral-500 font-normal">{schedules.length} 个任务</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {schedules.length === 0 ? (
              <p className="text-sm text-neutral-500 text-center py-6">暂无调度数据</p>
            ) : (
              <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                {schedules.map((sched, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-3 bg-neutral-800/50 rounded-lg"
                  >
                    <div>
                      <p className="text-sm text-white">{sched.name}</p>
                      <p className="text-xs text-neutral-500 font-mono">
                        {sched.expr ?? sched.schedule_expr ?? "—"}
                      </p>
                    </div>
                    <div className="text-right">
                      {sched.next_run && (
                        <p className="text-xs text-neutral-400 font-mono">{sched.next_run}</p>
                      )}
                      <Badge variant="outline" className="mt-1 text-xs border-blue-500/30 text-blue-400">
                        {sched.type ?? sched.schedule_type ?? "cron"}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* 环境变量 */}
        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider flex items-center gap-2">
              <Settings className="w-4 h-4 text-orange-500" />
              环境变量
              <span className="ml-auto text-xs text-neutral-500 font-normal">{envList.length} 项</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {envList.length === 0 ? (
              <p className="text-sm text-neutral-500 text-center py-6">暂无环境变量数据</p>
            ) : (
              <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                {envList.map((env, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-3 bg-neutral-800/50 rounded-lg"
                  >
                    <p className="text-sm text-white font-mono">{env.key}</p>
                    {env.configured ? (
                      <div className="flex items-center gap-1.5 text-green-400">
                        <CheckCircle className="w-4 h-4" />
                        <span className="text-xs">已配置</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-1.5 text-neutral-500">
                        <XCircle className="w-4 h-4" />
                        <span className="text-xs">未配置</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 数据源连接 */}
      <Card className="bg-neutral-900 border-neutral-800">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider flex items-center gap-2">
            <Link2 className="w-4 h-4 text-orange-500" />
            数据源连接状态
          </CardTitle>
        </CardHeader>
        <CardContent>
          {connections.length === 0 ? (
            <p className="text-sm text-neutral-500 text-center py-6">暂无连接数据</p>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {connections.map((conn, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-3 bg-neutral-800/50 rounded-lg border border-neutral-800"
                >
                  <div className="flex items-center gap-2">
                    <Database className="w-4 h-4 text-blue-400" />
                    <span className="text-sm text-white">{conn.name}</span>
                  </div>
                  {conn.configured && conn.status === "connected" ? (
                    <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                  ) : conn.configured ? (
                    <Badge variant="outline" className="text-xs border-yellow-500/30 text-yellow-400">
                      {conn.status}
                    </Badge>
                  ) : (
                    <XCircle className="w-4 h-4 text-neutral-500 flex-shrink-0" />
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 存储统计 */}
      <Card className="bg-neutral-900 border-neutral-800">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider flex items-center gap-2">
              <HardDrive className="w-4 h-4 text-orange-500" />
              存储概览
            </CardTitle>
            {storageTotals && (
              <div className="flex items-center gap-4 text-xs text-neutral-400">
                <span>总计: <span className="text-white font-mono">{storageTotals.size_human}</span></span>
                <span>文件: <span className="text-white font-mono">{storageTotals.files.toLocaleString()}</span></span>
                <span>目录: <span className="text-white font-mono">{storageTotals.directories}</span></span>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {storageDirectories.length === 0 ? (
            <p className="text-sm text-neutral-500 text-center py-6">暂无存储数据</p>
          ) : (
            <div className="space-y-2">
              {storageDirectories.map((dir, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-3 bg-neutral-800/50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <HardDrive className="w-4 h-4 text-neutral-500 flex-shrink-0" />
                    <div>
                      <p className="text-sm text-white font-mono">{dir.path || dir.name}</p>
                      <p className="text-xs text-neutral-500">
                        {dir.file_count} 文件
                        {dir.dir_count > 0 ? ` · ${dir.dir_count} 目录` : ""}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-white font-mono">{dir.size_human}</p>
                    {dir.last_modified && (
                      <p className="text-xs text-neutral-500">
                        {dir.last_modified.slice(11, 19)}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
