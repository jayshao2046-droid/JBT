"use client"

import { useState } from "react"
import { Server, Wifi, WifiOff, Save, TestTube2 } from "lucide-react"
import { MainLayout } from "@/components/layout/main-layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { toast } from "sonner"

export default function SimCtpConfigPage() {
  const [isTesting, setIsTesting] = useState(false)
  const [connected, setConnected] = useState(true)
  const [config, setConfig] = useState({
    brokerID: "9999",
    userID: "demo_user",
    password: "••••••••",
    mdFront: "tcp://180.168.146.187:10131",
    tdFront: "tcp://180.168.146.187:10130",
    appID: "simnow_client_test",
    authCode: "0000000000000000",
    autoConnect: true,
    reconnectInterval: 30,
  })

  const handleTest = () => {
    setIsTesting(true)
    setTimeout(() => {
      setIsTesting(false)
      setConnected(true)
      toast.success("CTP 连接测试成功，行情和交易均已连接")
    }, 2000)
  }

  const handleSave = () => {
    toast.success("CTP 配置已保存")
  }

  return (
    <MainLayout title="模拟交易" subtitle="CTP 配置">
      <div className="p-4 md:p-6 space-y-6 max-w-3xl">
        {/* 连接状态 */}
        <div className="flex items-center gap-4 p-4 bg-card border border-border rounded-lg">
          <div className="flex items-center gap-2">
            {connected ? (
              <Wifi className="w-5 h-5 text-green-500" />
            ) : (
              <WifiOff className="w-5 h-5 text-red-500" />
            )}
            <span className={connected ? "text-green-400 font-medium" : "text-red-400 font-medium"}>
              {connected ? "已连接" : "未连接"}
            </span>
          </div>
          <div className="flex gap-2 ml-auto">
            <Badge variant="outline" className="border-green-500/30 text-green-400 text-xs">行情 已连接</Badge>
            <Badge variant="outline" className="border-green-500/30 text-green-400 text-xs">交易 已连接</Badge>
          </div>
        </div>

        {/* 账户信息 */}
        <Card className="bg-card border-border">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-foreground flex items-center gap-2">
              <Server className="w-4 h-4 text-orange-500" />
              账户信息
            </CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { id: "brokerID", label: "经纪商 ID", key: "brokerID" },
              { id: "userID", label: "用户 ID", key: "userID" },
              { id: "password", label: "密码", key: "password" },
              { id: "appID", label: "AppID", key: "appID" },
              { id: "authCode", label: "认证码", key: "authCode" },
            ].map((field) => (
              <div key={field.id} className="space-y-1.5">
                <Label htmlFor={field.id} className="text-xs text-muted-foreground">{field.label}</Label>
                <Input
                  id={field.id}
                  value={config[field.key as keyof typeof config] as string}
                  onChange={(e) => setConfig((prev) => ({ ...prev, [field.key]: e.target.value }))}
                  className="bg-accent border-border text-foreground text-sm h-9 focus:border-orange-500"
                  type={field.id === "password" ? "password" : "text"}
                />
              </div>
            ))}
          </CardContent>
        </Card>

        {/* 服务器地址 */}
        <Card className="bg-card border-border">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-foreground flex items-center gap-2">
              <Server className="w-4 h-4 text-blue-500" />
              服务器配置
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground">行情前置地址 (MdFront)</Label>
              <Input
                value={config.mdFront}
                onChange={(e) => setConfig((prev) => ({ ...prev, mdFront: e.target.value }))}
                className="bg-accent border-border text-foreground text-sm h-9 focus:border-orange-500 font-mono"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground">交易前置地址 (TdFront)</Label>
              <Input
                value={config.tdFront}
                onChange={(e) => setConfig((prev) => ({ ...prev, tdFront: e.target.value }))}
                className="bg-accent border-border text-foreground text-sm h-9 focus:border-orange-500 font-mono"
              />
            </div>
            <div className="flex items-center justify-between py-2">
              <div>
                <p className="text-sm text-foreground">自动重连</p>
                <p className="text-xs text-muted-foreground">断线后自动尝试重连</p>
              </div>
              <Switch
                checked={config.autoConnect}
                onCheckedChange={(v) => setConfig((prev) => ({ ...prev, autoConnect: v }))}
                className="data-[state=checked]:bg-orange-500"
              />
            </div>
          </CardContent>
        </Card>

        {/* 操作按钮 */}
        <div className="flex gap-3">
          <Button onClick={handleTest} disabled={isTesting} variant="outline" className="border-border text-muted-foreground hover:bg-accent hover:text-foreground">
            <TestTube2 className="w-4 h-4 mr-2" />
            {isTesting ? "测试中..." : "测试连接"}
          </Button>
          <Button onClick={handleSave} className="bg-orange-500 hover:bg-orange-600 text-white">
            <Save className="w-4 h-4 mr-2" />
            保存配置
          </Button>
        </div>
      </div>
    </MainLayout>
  )
}
