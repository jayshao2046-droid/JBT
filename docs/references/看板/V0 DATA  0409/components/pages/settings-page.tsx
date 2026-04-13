"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Server,
  Database,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Settings,
  Calendar,
  HardDrive,
  FileText,
  Shield,
  Link2,
  History,
  Eye,
  EyeOff,
} from "lucide-react"

// 服务信息
const serviceInfo = {
  name: "JBT Data Service",
  version: "2.4.1",
  pythonVersion: "3.11.8",
  hostname: "Mini",
  dataRoot: "/Users/jbot/JBT-data/",
  apiPort: 8105,
  logFormat: "JSON",
  environment: "production",
}

// 调度计划
const scheduleTable = [
  { name: "新闻 API", expr: "*/1 * * * *", nextRun: "10:43:00", type: "cron" },
  { name: "情绪指数", expr: "*/1 * * * *", nextRun: "10:43:30", type: "cron" },
  { name: "外盘分钟", expr: "*/5 * * * *", nextRun: "10:45:00", type: "cron" },
  { name: "期权行情", expr: "*/15 9-15 * * 1-5", nextRun: "10:45:00", type: "cron" },
  { name: "RSS 聚合", expr: "*/10 * * * *", nextRun: "10:50:00", type: "cron" },
  { name: "飞书心跳", expr: "*/5 * * * *", nextRun: "10:45:00", type: "cron" },
  { name: "波动率指数", expr: "0 * * * *", nextRun: "11:00:00", type: "cron" },
  { name: "宏观数据", expr: "0 */4 * * *", nextRun: "12:00:00", type: "cron" },
  { name: "Tushare 期货", expr: "30 15 * * 1-5", nextRun: "今日 15:30", type: "cron" },
  { name: "持仓日报", expr: "30 16 * * 1-5", nextRun: "今日 16:30", type: "cron" },
  { name: "外汇日线", expr: "0 6 * * *", nextRun: "明日 06:00", type: "cron" },
  { name: "邮件晨报", expr: "30 7 * * *", nextRun: "明日 07:30", type: "cron" },
  { name: "邮件午报", expr: "30 12 * * *", nextRun: "今日 12:30", type: "cron" },
  { name: "CFTC 持仓", expr: "0 8 * * 6", nextRun: "本周六 08:00", type: "cron" },
]

// 环境变量与通知配置
const envConfig = [
  { key: "TUSHARE_TOKEN", value: "ts_****************************8f9a", masked: true },
  { key: "FEISHU_WEBHOOK_ALERT", value: "https://open.feishu.cn/open-apis/bot/v2/hook/****", masked: true },
  { key: "FEISHU_WEBHOOK_NEWS", value: "https://open.feishu.cn/open-apis/bot/v2/hook/****", masked: true },
  { key: "FEISHU_WEBHOOK_TRADE", value: "https://open.feishu.cn/open-apis/bot/v2/hook/****", masked: true },
  { key: "SMTP_HOST", value: "smtp.qq.com", masked: false },
  { key: "SMTP_PORT", value: "465", masked: false },
  { key: "SMTP_USER", value: "jbot@qq.com", masked: false },
  { key: "SMTP_PASSWORD", value: "****************", masked: true },
  { key: "DATA_ROOT", value: "/Users/jbot/JBT-data/", masked: false },
  { key: "LOG_LEVEL", value: "INFO", masked: false },
]

// 数据源连接状态
const dataSources = [
  { name: "Tushare", status: "connected", latency: "128ms" },
  { name: "AkShare", status: "connected", latency: "85ms" },
  { name: "RSS Feeds", status: "connected", latency: "256ms" },
  { name: "yfinance", status: "connected", latency: "312ms" },
  { name: "SMTP (QQ Mail)", status: "connected", latency: "45ms" },
  { name: "飞书 Webhook", status: "connected", latency: "68ms" },
]

// 存储统计
const storageStats = [
  { path: "/data/futures_minute", size: "42.8 GB", files: 1256, lastUpdate: "10:42:00" },
  { path: "/data/stock_minute", size: "28.5 GB", files: 4520, lastUpdate: "10:42:00" },
  { path: "/data/overseas_kline", size: "12.3 GB", files: 385, lastUpdate: "10:40:00" },
  { path: "/data/parquet", size: "18.6 GB", files: 892, lastUpdate: "10:05:30" },
  { path: "/data/news_api", size: "8.2 GB", files: 3650, lastUpdate: "10:42:15" },
  { path: "/data/news_collected", size: "5.8 GB", files: 2840, lastUpdate: "10:42:00" },
  { path: "/data/sentiment", size: "2.4 GB", files: 365, lastUpdate: "10:42:30" },
  { path: "/data/macro_global", size: "1.2 GB", files: 128, lastUpdate: "08:00:12" },
  { path: "/data/tushare", size: "6.5 GB", files: 420, lastUpdate: "昨日 15:32" },
  { path: "/data/logs", size: "2.2 GB", files: 890, lastUpdate: "10:42:30" },
]

// 规则与阈值
const thresholds = [
  { name: "CPU 告警阈值", value: "80%", description: "超过此值触发告警" },
  { name: "内存告警阈值", value: "85%", description: "超过此值触发告警" },
  { name: "磁盘告警阈值", value: "90%", description: "超过此值触发告警" },
  { name: "采集延迟阈值", value: "60s", description: "超过此值标记为延迟" },
  { name: "采集超时阈值", value: "300s", description: "超过此值标记为失败" },
  { name: "心跳超时阈值", value: "10min", description: "超过此值触发告警" },
  { name: "通知失败重试", value: "3次", description: "失败后重试次数" },
]

// 变更记录
const changeLog = [
  { date: "2025-04-08", content: "修复邮件日报附件路径问题" },
  { date: "2025-04-05", content: "优化 Parquet 同步性能，减少 30% 耗时" },
  { date: "2025-04-01", content: "新增期权行情采集任务" },
  { date: "2025-03-28", content: "移除 launchctl 遗留服务配置" },
  { date: "2025-03-25", content: "修复飞书心跳时间戳格式问题" },
  { date: "2025-03-20", content: "升级 Python 至 3.11.8" },
  { date: "2025-03-15", content: "移除 Studio SSH 相关配置" },
  { date: "2025-03-10", content: "新增 CFTC 持仓采集任务" },
]

export default function SettingsPage() {
  const [showMasked, setShowMasked] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-12 w-64 bg-neutral-800" />
        <Skeleton className="h-40 bg-neutral-800" />
        <Skeleton className="h-96 bg-neutral-800" />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* 页面头部 */}
      <div>
        <h1 className="text-2xl font-bold text-white">配置与设置</h1>
        <p className="text-sm text-neutral-400 mt-1">
          只读展示当前运行配置和系统结构，帮助快速排查问题
        </p>
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
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
            <div>
              <p className="text-xs text-neutral-500 mb-1">服务名称</p>
              <p className="text-sm text-white font-medium">{serviceInfo.name}</p>
            </div>
            <div>
              <p className="text-xs text-neutral-500 mb-1">版本号</p>
              <p className="text-sm text-orange-400 font-mono">{serviceInfo.version}</p>
            </div>
            <div>
              <p className="text-xs text-neutral-500 mb-1">Python 版本</p>
              <p className="text-sm text-white font-mono">{serviceInfo.pythonVersion}</p>
            </div>
            <div>
              <p className="text-xs text-neutral-500 mb-1">运行主机</p>
              <p className="text-sm text-white">{serviceInfo.hostname}</p>
            </div>
            <div>
              <p className="text-xs text-neutral-500 mb-1">数据目录</p>
              <p className="text-sm text-white font-mono text-xs truncate">{serviceInfo.dataRoot}</p>
            </div>
            <div>
              <p className="text-xs text-neutral-500 mb-1">API 端口</p>
              <p className="text-sm text-white font-mono">{serviceInfo.apiPort}</p>
            </div>
            <div>
              <p className="text-xs text-neutral-500 mb-1">日志格式</p>
              <p className="text-sm text-white">{serviceInfo.logFormat}</p>
            </div>
            <div>
              <p className="text-xs text-neutral-500 mb-1">当前环境</p>
              <Badge variant="outline" className="border-green-500/30 text-green-400">
                {serviceInfo.environment}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 调度计划总表 */}
      <Card className="bg-neutral-900 border-neutral-800">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider flex items-center gap-2">
            <Calendar className="w-4 h-4 text-orange-500" />
            调度计划总表
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-neutral-800">
                  <th className="text-left py-2 px-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">
                    任务名称
                  </th>
                  <th className="text-left py-2 px-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">
                    调度表达式
                  </th>
                  <th className="text-left py-2 px-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">
                    下次运行
                  </th>
                </tr>
              </thead>
              <tbody>
                {scheduleTable.map((item, index) => (
                  <tr
                    key={item.name}
                    className={`border-b border-neutral-800/50 ${
                      index % 2 === 0 ? "bg-neutral-900" : "bg-neutral-900/50"
                    }`}
                  >
                    <td className="py-2 px-3 text-white">{item.name}</td>
                    <td className="py-2 px-3">
                      <code className="text-xs bg-neutral-800 px-2 py-1 rounded text-neutral-300 font-mono">
                        {item.expr}
                      </code>
                    </td>
                    <td className="py-2 px-3 text-neutral-300 font-mono">{item.nextRun}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* 环境变量和数据源连接 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 环境变量与通知配置 */}
        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider flex items-center gap-2">
                <Shield className="w-4 h-4 text-orange-500" />
                环境变量与通知配置
              </CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowMasked(!showMasked)}
                className="text-neutral-400 hover:text-white"
              >
                {showMasked ? (
                  <EyeOff className="w-4 h-4 mr-1" />
                ) : (
                  <Eye className="w-4 h-4 mr-1" />
                )}
                {showMasked ? "隐藏" : "显示"}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-72">
              <div className="space-y-2">
                {envConfig.map((item) => (
                  <div
                    key={item.key}
                    className="flex items-center justify-between p-3 bg-neutral-800/50 rounded-lg"
                  >
                    <span className="text-sm text-neutral-400 font-mono">{item.key}</span>
                    <span className="text-sm text-white font-mono truncate max-w-[200px]">
                      {item.masked && !showMasked ? "••••••••••••" : item.value}
                    </span>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* 数据源连接状态 */}
        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider flex items-center gap-2">
              <Link2 className="w-4 h-4 text-orange-500" />
              数据源连接状态
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {dataSources.map((source) => (
                <div
                  key={source.name}
                  className="flex items-center justify-between p-3 bg-neutral-800/50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span className="text-sm text-white">{source.name}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-neutral-400 font-mono">{source.latency}</span>
                    <Badge
                      variant="outline"
                      className="border-green-500/30 text-green-400 text-xs"
                    >
                      已连接
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 存储统计和规则阈值 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 存储统计 */}
        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider flex items-center gap-2">
              <HardDrive className="w-4 h-4 text-orange-500" />
              存储统计
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-72">
              <div className="space-y-2">
                {storageStats.map((item) => (
                  <div
                    key={item.path}
                    className="p-3 bg-neutral-800/50 rounded-lg"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-white font-mono">{item.path}</span>
                      <span className="text-sm text-orange-400 font-mono">{item.size}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs text-neutral-500">
                      <span>{item.files} 文件</span>
                      <span>更新于 {item.lastUpdate}</span>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* 规则与阈值 */}
        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider flex items-center gap-2">
              <Settings className="w-4 h-4 text-orange-500" />
              规则与阈值
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {thresholds.map((item) => (
                <div
                  key={item.name}
                  className="flex items-center justify-between p-3 bg-neutral-800/50 rounded-lg"
                >
                  <div>
                    <p className="text-sm text-white">{item.name}</p>
                    <p className="text-xs text-neutral-500">{item.description}</p>
                  </div>
                  <Badge
                    variant="outline"
                    className="border-neutral-600 text-white font-mono"
                  >
                    {item.value}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 变更记录 */}
      <Card className="bg-neutral-900 border-neutral-800">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider flex items-center gap-2">
            <History className="w-4 h-4 text-orange-500" />
            近期变更记录
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative">
            <div className="absolute left-4 top-0 bottom-0 w-px bg-neutral-800" />
            <div className="space-y-4">
              {changeLog.map((item, index) => (
                <div key={index} className="flex items-start gap-4 pl-4">
                  <div className="w-2 h-2 rounded-full bg-orange-500 mt-2 -ml-[5px] z-10" />
                  <div>
                    <p className="text-xs text-neutral-500 font-mono">{item.date}</p>
                    <p className="text-sm text-white">{item.content}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
