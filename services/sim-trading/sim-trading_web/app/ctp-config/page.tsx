"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Eye, EyeOff, Plug, PlugZap, RefreshCw, Server } from "lucide-react"
import { toast } from "sonner"
import { simApi, type SystemState } from "@/lib/sim-api"

const CTP_PRESETS = [
  {
    label: "SimNow 7×24",
    broker_id: "9999",
    md_front: "tcp://180.168.146.187:10131",
    td_front: "tcp://180.168.146.187:10130",
  },
  {
    label: "SimNow 交易时段",
    broker_id: "9999",
    md_front: "tcp://210.14.72.21:10131",
    td_front: "tcp://210.14.72.21:10130",
  },
  {
    label: "SimNow 备用",
    broker_id: "9999",
    md_front: "tcp://180.168.146.187:10211",
    td_front: "tcp://180.168.146.187:10210",
  },
]

export default function CtpConfigPage() {
  const [state, setState] = useState<Partial<SystemState>>({})
  const [form, setForm] = useState({
    broker_id: "9999",
    user_id: "",
    password: "",
    md_front: "tcp://180.168.146.187:10131",
    td_front: "tcp://180.168.146.187:10130",
  })
  const [showPwd, setShowPwd] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [connecting, setConnecting] = useState(false)
  const [activePreset, setActivePreset] = useState(0)

  const loadState = async () => {
    setIsLoading(true)
    try {
      const s = await simApi.systemState()
      setState(s)
      setForm(f => ({
        ...f,
        broker_id: s.ctp_broker_id || f.broker_id,
        user_id: s.ctp_user_id || f.user_id,
        md_front: s.ctp_md_front || f.md_front,
        td_front: s.ctp_td_front || f.td_front,
      }))
    } catch {
      toast.error("无法加载 CTP 状态")
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => { loadState() }, [])

  const applyPreset = (idx: number) => {
    const p = CTP_PRESETS[idx]
    setActivePreset(idx)
    setForm(f => ({ ...f, broker_id: p.broker_id, md_front: p.md_front, td_front: p.td_front }))
    toast.info(`已切换至 ${p.label} 前置地址`)
  }

  const handleSave = async () => {
    if (!form.user_id.trim()) { toast.warning("请填写 SimNow 账号"); return }
    if (!form.password.trim()) { toast.warning("请填写密码"); return }
    setIsLoading(true)
    try {
      await simApi.saveCtp(form)
      toast.success("CTP 配置已保存")
      await loadState()
    } catch {
      toast.error("保存失败")
    } finally {
      setIsLoading(false)
    }
  }

  const handleConnect = async () => {
    setConnecting(true)
    try {
      const r = await simApi.ctpConnect()
      toast.success(`CTP 连接成功（${r.result}）`)
      await loadState()
    } catch {
      toast.error("CTP 连接失败")
    } finally {
      setConnecting(false)
    }
  }

  const handleDisconnect = async () => {
    setConnecting(true)
    try {
      await simApi.ctpDisconnect()
      toast.info("CTP 已断开")
      await loadState()
    } catch {
      toast.error("断开失败")
    } finally {
      setConnecting(false)
    }
  }

  const mdOnline = state.ctp_md_connected
  const tdOnline = state.ctp_td_connected

  return (
    <div className="p-6 space-y-6 bg-neutral-950 min-h-screen">
      {/* 头部 */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wider">CTP 接口配置</h1>
          <p className="text-sm text-neutral-400">SimNow 模拟账户登录 / 实盘接口切换</p>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={loadState}
          disabled={isLoading}
          className="text-neutral-400 hover:text-orange-500"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
        </Button>
      </div>

      {/* 双通道连接状态 */}
      <div className="grid grid-cols-2 gap-4">
        <Card className={`bg-neutral-900 border ${mdOnline ? "border-green-600" : "border-neutral-700"}`}>
          <CardContent className="p-4 flex items-center gap-3">
            <Server className={`w-5 h-5 ${mdOnline ? "text-green-400" : "text-neutral-500"}`} />
            <div>
              <p className="text-xs text-neutral-400">行情通道（mdapi）</p>
              <p className={`text-sm font-bold ${mdOnline ? "text-green-400" : "text-neutral-500"}`}>
                {mdOnline ? "● 已连接" : "○ 未连接"}
              </p>
            </div>
          </CardContent>
        </Card>
        <Card className={`bg-neutral-900 border ${tdOnline ? "border-green-600" : "border-neutral-700"}`}>
          <CardContent className="p-4 flex items-center gap-3">
            <PlugZap className={`w-5 h-5 ${tdOnline ? "text-green-400" : "text-neutral-500"}`} />
            <div>
              <p className="text-xs text-neutral-400">交易通道（traderapi）</p>
              <p className={`text-sm font-bold ${tdOnline ? "text-green-400" : "text-neutral-500"}`}>
                {tdOnline ? "● 已连接" : "○ 未连接"}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 前置地址预设 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-300">前置地址快速切换</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {CTP_PRESETS.map((p, i) => (
            <Button
              key={i}
              size="sm"
              onClick={() => applyPreset(i)}
              className={`text-xs ${
                activePreset === i
                  ? "bg-orange-600 text-white hover:bg-orange-700"
                  : "bg-neutral-800 text-neutral-400 hover:bg-neutral-700 hover:text-white"
              }`}
            >
              {p.label}
            </Button>
          ))}
        </CardContent>
      </Card>

      {/* 配置表单 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-300">账户配置</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 max-w-xl">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs text-neutral-400">Broker ID（经纪公司代码）</label>
              <Input
                value={form.broker_id}
                onChange={e => setForm(f => ({ ...f, broker_id: e.target.value }))}
                className="bg-neutral-800 border-neutral-600 text-white font-mono"
                placeholder="9999"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-neutral-400">User ID（SimNow 账号）</label>
              <Input
                value={form.user_id}
                onChange={e => setForm(f => ({ ...f, user_id: e.target.value }))}
                className="bg-neutral-800 border-neutral-600 text-white font-mono"
                placeholder="SimNow 账号"
              />
            </div>
          </div>
          <div className="space-y-1">
            <label className="text-xs text-neutral-400">密码</label>
            <div className="relative">
              <Input
                type={showPwd ? "text" : "password"}
                value={form.password}
                onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                className="bg-neutral-800 border-neutral-600 text-white font-mono pr-10"
                placeholder="SimNow 密码"
              />
              <button
                type="button"
                onClick={() => setShowPwd(!showPwd)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500 hover:text-neutral-300"
              >
                {showPwd ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>
          <div className="space-y-1">
            <label className="text-xs text-neutral-400">行情前置地址（MD Front）</label>
            <Input
              value={form.md_front}
              onChange={e => setForm(f => ({ ...f, md_front: e.target.value }))}
              className="bg-neutral-800 border-neutral-600 text-white font-mono text-xs"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-neutral-400">交易前置地址（TD Front）</label>
            <Input
              value={form.td_front}
              onChange={e => setForm(f => ({ ...f, td_front: e.target.value }))}
              className="bg-neutral-800 border-neutral-600 text-white font-mono text-xs"
            />
          </div>
          <div className="flex gap-3 pt-2">
            <Button
              onClick={handleSave}
              disabled={isLoading}
              className="bg-orange-600 hover:bg-orange-700 text-white"
            >
              保存配置
            </Button>
            {mdOnline || tdOnline ? (
              <Button
                onClick={handleDisconnect}
                disabled={connecting}
                variant="outline"
                className="border-red-700 text-red-400 hover:bg-red-900/30"
              >
                <Plug className="w-4 h-4 mr-2" />
                {connecting ? "断开中..." : "断开连接"}
              </Button>
            ) : (
              <Button
                onClick={handleConnect}
                disabled={connecting}
                className="bg-green-700 hover:bg-green-800 text-white"
              >
                <PlugZap className="w-4 h-4 mr-2" />
                {connecting ? "连接中..." : "连接 CTP"}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 注意事项 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardContent className="p-4 text-xs text-neutral-500 space-y-1">
          <p className="text-neutral-400 font-medium mb-2">SimNow 注意事项</p>
          <p>• SimNow 7×24 通道全天可用，但非交易时段无行情推送</p>
          <p>• SimNow 账号在 <span className="text-orange-400">www.simnow.com.cn</span> 注册，经纪代码固定 9999</p>
          <p>• 实盘切换需要更换 Broker ID、前置地址和密码，谨慎操作</p>
          <p>• 骨架阶段：connect 返回模拟成功，真实 CTP 握手将在 TASK-0016 实现</p>
        </CardContent>
      </Card>
    </div>
  )
}
