"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { simTradingApi, type SystemState } from "@/lib/api/sim-trading"
import { useToast } from "@/hooks/use-toast"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"

export default function CtpConfigPage() {
  const { toast } = useToast()
  const [, setConfig] = useState<Partial<SystemState>>({})
  const [status, setStatus] = useState<{ md_connected: boolean; td_connected: boolean } | null>(null)
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState({
    broker_id: "",
    user_id: "",
    password: "",
    md_front: "",
    td_front: "",
  })

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchStatus, 2000)
    return () => clearInterval(interval)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const [configRes, statusRes] = await Promise.all([
        simTradingApi.getCtpConfig(),
        simTradingApi.getCtpStatus(),
      ])
      setConfig(configRes)
      setStatus(statusRes)
      setForm({
        broker_id: configRes.ctp_broker_id || "",
        user_id: configRes.ctp_user_id || "",
        password: "",
        md_front: configRes.ctp_md_front || "",
        td_front: configRes.ctp_td_front || "",
      })
    } catch (err) {
      toast({ title: "加载失败", description: err instanceof Error ? err.message : "未知错误", variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  const fetchStatus = async () => {
    try {
      const statusRes = await simTradingApi.getCtpStatus()
      setStatus(statusRes)
    } catch {
      // 静默失败
    }
  }

  const handleSave = async () => {
    try {
      await simTradingApi.saveCtpConfig(form)
      toast({ title: "保存成功", description: "CTP 配置已更新" })
      fetchData()
    } catch (err) {
      toast({ title: "保存失败", description: err instanceof Error ? err.message : "未知错误", variant: "destructive" })
    }
  }

  const handleConnect = async () => {
    try {
      await simTradingApi.ctpConnect()
      toast({ title: "连接成功", description: "CTP 连接已建立" })
      fetchStatus()
    } catch (err) {
      toast({ title: "连接失败", description: err instanceof Error ? err.message : "未知错误", variant: "destructive" })
    }
  }

  const handleDisconnect = async () => {
    try {
      await simTradingApi.ctpDisconnect()
      toast({ title: "断开成功", description: "CTP 连接已断开" })
      fetchStatus()
    } catch (err) {
      toast({ title: "断开失败", description: err instanceof Error ? err.message : "未知错误", variant: "destructive" })
    }
  }

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-96" />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* 连接状态 */}
      <Card>
        <CardHeader>
          <CardTitle>CTP 连接状态</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-center gap-2">
              <Badge variant={status?.md_connected ? "default" : "secondary"}>
                行情前置 {status?.md_connected ? "已连接" : "未连接"}
              </Badge>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={status?.td_connected ? "default" : "secondary"}>
                交易前置 {status?.td_connected ? "已连接" : "未连接"}
              </Badge>
            </div>
          </div>
          <div className="flex gap-2 mt-4">
            <Button onClick={handleConnect} disabled={status?.md_connected && status?.td_connected}>
              连接
            </Button>
            <Button variant="outline" onClick={handleDisconnect} disabled={!status?.md_connected && !status?.td_connected}>
              断开
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 配置表单 */}
      <Card>
        <CardHeader>
          <CardTitle>CTP 配置</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>期货公司代码</Label>
            <Input
              value={form.broker_id}
              onChange={(e) => setForm({ ...form, broker_id: e.target.value })}
              placeholder="例如: 9999"
            />
          </div>
          <div>
            <Label>用户名</Label>
            <Input
              value={form.user_id}
              onChange={(e) => setForm({ ...form, user_id: e.target.value })}
              placeholder="SimNow 用户名"
            />
          </div>
          <div>
            <Label>密码</Label>
            <Input
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              placeholder="留空则不修改"
            />
          </div>
          <div>
            <Label>行情前置地址</Label>
            <Input
              value={form.md_front}
              onChange={(e) => setForm({ ...form, md_front: e.target.value })}
              placeholder="tcp://180.168.146.187:10211"
            />
          </div>
          <div>
            <Label>交易前置地址</Label>
            <Input
              value={form.td_front}
              onChange={(e) => setForm({ ...form, td_front: e.target.value })}
              placeholder="tcp://180.168.146.187:10201"
            />
          </div>
          <Button onClick={handleSave}>保存配置</Button>
        </CardContent>
      </Card>

      {/* SimNow 预设 */}
      <Card>
        <CardHeader>
          <CardTitle>SimNow 预设</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="p-3 border rounded">
              <p className="font-medium">7x24 环境</p>
              <p className="text-xs text-muted-foreground mt-1">
                行情: tcp://180.168.146.187:10211 | 交易: tcp://180.168.146.187:10201
              </p>
              <Button
                size="sm"
                variant="outline"
                className="mt-2"
                onClick={() =>
                  setForm({
                    ...form,
                    md_front: "tcp://180.168.146.187:10211",
                    td_front: "tcp://180.168.146.187:10201",
                  })
                }
              >
                使用此预设
              </Button>
            </div>
            <div className="p-3 border rounded">
              <p className="font-medium">电信环境</p>
              <p className="text-xs text-muted-foreground mt-1">
                行情: tcp://218.202.237.33:10212 | 交易: tcp://218.202.237.33:10202
              </p>
              <Button
                size="sm"
                variant="outline"
                className="mt-2"
                onClick={() =>
                  setForm({
                    ...form,
                    md_front: "tcp://218.202.237.33:10212",
                    td_front: "tcp://218.202.237.33:10202",
                  })
                }
              >
                使用此预设
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
