"use client"

import { useEffect, useRef, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { dataApi, LogEntry } from "@/lib/api/data"
import { Clock, RotateCw, AlertCircle } from "lucide-react"

export function LogsViewer() {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [lastUpdate, setLastUpdate] = useState<string>("")
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const [autoScroll, setAutoScroll] = useState(true)

  const fetchLogs = async () => {
    try {
      setLoading(true)
      setError("")
      const res = await dataApi.getLogs(200)
      // 按时间倒序排列（最新的在最上面）
      const sorted = [...res.logs].reverse()
      setLogs(sorted)
      setLastUpdate(new Date().toLocaleTimeString("zh-CN"))
      setLoading(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取日志失败")
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLogs()
    const interval = setInterval(fetchLogs, 30000) // 每 30 秒刷新一次
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (autoScroll && scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = 0
    }
  }, [logs, autoScroll])

  const handleScroll = () => {
    if (!scrollContainerRef.current) return
    const { scrollTop } = scrollContainerRef.current
    if (scrollTop > 100) {
      setAutoScroll(false)
    }
  }

  const getLogLevelColor = (level: string) => {
    switch (level) {
      case "ERROR":
        return "bg-red-500/10 border-red-500/20 text-red-400"
      case "WARNING":
        return "bg-yellow-500/10 border-yellow-500/20 text-yellow-400"
      default:
        return "bg-blue-500/10 border-blue-500/20 text-blue-400"
    }
  }

  return (
    <Card className="col-span-1 md:col-span-3">
      <CardHeader className="pb-3 flex flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock className="h-5 w-5 text-muted-foreground" />
          <div>
            <CardTitle className="text-base">采集日志</CardTitle>
            <p className="text-xs text-muted-foreground mt-1">
              显示最后 200 条采集日志 • 更新于 {lastUpdate}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {autoScroll && (
            <span className="text-xs px-2 py-1 bg-green-500/10 text-green-400 rounded border border-green-500/20">
              自动滚动
            </span>
          )}
          <button
            onClick={() => {
              fetchLogs()
              setAutoScroll(true)
            }}
            className="p-2 hover:bg-muted rounded transition-colors"
            title="刷新日志"
          >
            <RotateCw className="h-4 w-4" />
          </button>
        </div>
      </CardHeader>

      <CardContent>
        {error && (
          <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded text-red-400 text-sm mb-3">
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            {error}
          </div>
        )}

        {loading ? (
          <div className="h-96 flex items-center justify-center text-muted-foreground text-sm">
            加载日志中...
          </div>
        ) : logs.length === 0 ? (
          <div className="h-96 flex items-center justify-center text-muted-foreground text-sm">
            无日志数据
          </div>
        ) : (
          <div
            ref={scrollContainerRef}
            onScroll={handleScroll}
            className="h-96 overflow-y-auto bg-muted/20 rounded border border-border/50 p-2 space-y-1 font-mono text-xs"
          >
            {logs.map((log, idx) => (
              <div
                key={idx}
                className={`flex items-start gap-2 p-2 rounded hover:bg-muted/40 transition-colors ${getLogLevelColor(
                  log.level
                )}`}
              >
                {/* 时间戳 */}
                {log.timestamp && (
                  <span className="text-muted-foreground flex-shrink-0 whitespace-nowrap">
                    [{log.timestamp.slice(11, 19)}]
                  </span>
                )}

                {/* 日志级别 */}
                <Badge
                  variant="outline"
                  className={`text-[10px] px-1 py-0 flex-shrink-0 ${getLogLevelColor(log.level)}`}
                >
                  {log.level}
                </Badge>

                {/* 日志消息 */}
                <span className="text-foreground/80 break-words flex-1">
                  {log.message.replace(/^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}[,.]\d+\s+-\s+\S+\s+-\s+\w+\s+-\s+/, "")}
                </span>
              </div>
            ))}
          </div>
        )}

        <div className="mt-3 flex items-center justify-between">
          <div className="text-xs text-muted-foreground">
            显示 {logs.length} 条日志 • 数据来源：采集调度器
          </div>
          <button
            onClick={() => {
              setAutoScroll(true)
              if (scrollContainerRef.current) {
                scrollContainerRef.current.scrollTop = 0
              }
            }}
            className="text-xs px-2 py-1 hover:bg-muted rounded transition-colors"
          >
            回到顶部
          </button>
        </div>
      </CardContent>
    </Card>
  )
}
