"use client"

import { useState } from "react"
import {
  Users,
  Clock,
  Bell,
  Calendar,
  Database,
  Shield,
  Key,
  Monitor,
  Save,
  Plus,
  Trash2,
  Edit,
  Check,
  X,
} from "lucide-react"
import { MainLayout } from "@/components/layout/main-layout"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { toast } from "sonner"
import { cn } from "@/lib/utils"

// 用户类型
interface User {
  id: string
  username: string
  role: "admin" | "operator" | "viewer"
  status: "active" | "inactive"
  lastLogin: string
}

// 交易时段
interface TradingSession {
  id: string
  name: string
  startTime: string
  endTime: string
  enabled: boolean
}

export default function SettingsPage() {
  const [lastUpdate, setLastUpdate] = useState<Date | null>(new Date())
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [activeTab, setActiveTab] = useState("users")

  // 用户管理
  const [users, setUsers] = useState<User[]>([
    { id: "1", username: "admin", role: "admin", status: "active", lastLogin: "2024-01-15 10:30" },
    { id: "2", username: "operator1", role: "operator", status: "active", lastLogin: "2024-01-14 16:45" },
    { id: "3", username: "viewer1", role: "viewer", status: "inactive", lastLogin: "2024-01-10 09:00" },
  ])

  // 交易时段配置
  const [tradingSessions, setTradingSessions] = useState<TradingSession[]>([
    { id: "1", name: "日盘上午", startTime: "09:00", endTime: "11:30", enabled: true },
    { id: "2", name: "日盘下午", startTime: "13:30", endTime: "15:00", enabled: true },
    { id: "3", name: "夜盘", startTime: "21:00", endTime: "02:30", enabled: true },
  ])

  // 通知配置
  const [notifications, setNotifications] = useState({
    email: true,
    webhook: false,
    dingding: true,
    wecom: false,
    emailAddress: "admin@example.com",
    webhookUrl: "",
    dingdingToken: "***",
    wecomKey: "",
  })

  // 日志设置
  const [logSettings, setLogSettings] = useState({
    level: "info",
    retention: "30",
    maxSize: "100",
    compress: true,
  })

  // 安全设置
  const [securitySettings, setSecuritySettings] = useState({
    sessionTimeout: "30",
    maxLoginAttempts: "5",
    twoFactor: false,
    ipWhitelist: true,
  })

  const handleRefresh = () => {
    setIsRefreshing(true)
    setTimeout(() => {
      setLastUpdate(new Date())
      setIsRefreshing(false)
      toast.success("配置已刷新")
    }, 500)
  }

  const handleSave = () => {
    toast.success("设置已保存")
  }

  const getRoleBadge = (role: string) => {
    switch (role) {
      case "admin":
        return <Badge className="bg-red-500/20 text-red-400 border-red-500/30">管理员</Badge>
      case "operator":
        return <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">操作员</Badge>
      case "viewer":
        return <Badge className="bg-neutral-500/20 text-neutral-400 border-neutral-500/30">观察者</Badge>
      default:
        return null
    }
  }

  const settingsTabs = [
    { id: "users", label: "用户管理", icon: Users },
    { id: "trading", label: "交易时段", icon: Clock },
    { id: "notifications", label: "通知配置", icon: Bell },
    { id: "holidays", label: "节假日", icon: Calendar },
    { id: "database", label: "数据管理", icon: Database },
    { id: "security", label: "安全设置", icon: Shield },
    { id: "api", label: "API 密钥", icon: Key },
    { id: "system", label: "系统监控", icon: Monitor },
  ]

  return (
    <MainLayout
      title="系统设置"
      onRefresh={handleRefresh}
      isRefreshing={isRefreshing}
      lastUpdate={lastUpdate}
    >
      <div className="p-4 md:p-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          {/* Tab 导航 */}
          <TabsList className="flex flex-wrap h-auto gap-2 bg-transparent p-0">
            {settingsTabs.map((tab) => {
              const Icon = tab.icon
              return (
                <TabsTrigger
                  key={tab.id}
                  value={tab.id}
                  className={cn(
                    "flex items-center gap-2 px-4 py-2 rounded-lg border transition-all",
                    "data-[state=active]:bg-orange-500/10 data-[state=active]:border-orange-500/30 data-[state=active]:text-orange-500",
                    "data-[state=inactive]:bg-muted/50 data-[state=inactive]:border-border data-[state=inactive]:text-muted-foreground",
                    "hover:bg-muted hover:text-foreground"
                  )}
                >
                  <Icon className="w-4 h-4" />
                  <span className="text-sm">{tab.label}</span>
                </TabsTrigger>
              )
            })}
          </TabsList>

          {/* 用户管理 */}
          <TabsContent value="users" className="space-y-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-foreground">用户管理</CardTitle>
                  <CardDescription className="text-muted-foreground">
                    管理系统用户账号和权限
                  </CardDescription>
                </div>
                <Dialog>
                  <DialogTrigger asChild>
                    <Button className="bg-orange-500 hover:bg-orange-600">
                      <Plus className="w-4 h-4 mr-2" />
                      添加用户
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle className="text-foreground">添加新用户</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 pt-4">
                      <div className="space-y-2">
                        <Label className="text-muted-foreground">用户名</Label>
                        <Input
                          placeholder="请输入用户名"
                          className="bg-background border-input text-foreground"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label className="text-muted-foreground">密码</Label>
                        <Input
                          type="password"
                          placeholder="请输入密码"
                          className="bg-background border-input text-foreground"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label className="text-muted-foreground">角色</Label>
                        <Select defaultValue="viewer">
                          <SelectTrigger className="bg-background border-input text-foreground">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="admin">管理员</SelectItem>
                            <SelectItem value="operator">操作员</SelectItem>
                            <SelectItem value="viewer">观察者</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <Button className="w-full bg-orange-500 hover:bg-orange-600">
                        创建用户
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow className="border-border hover:bg-transparent">
                      <TableHead className="text-muted-foreground">用户名</TableHead>
                      <TableHead className="text-muted-foreground">角色</TableHead>
                      <TableHead className="text-muted-foreground">状态</TableHead>
                      <TableHead className="text-muted-foreground">最后登录</TableHead>
                      <TableHead className="text-muted-foreground text-right">操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map((user) => (
                      <TableRow key={user.id} className="border-border">
                        <TableCell className="text-foreground font-medium">
                          {user.username}
                        </TableCell>
                        <TableCell>{getRoleBadge(user.role)}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div
                              className={cn(
                                "w-2 h-2 rounded-full",
                                user.status === "active" ? "bg-green-500" : "bg-neutral-500"
                              )}
                            />
                            <span className={user.status === "active" ? "text-green-500" : "text-neutral-500"}>
                              {user.status === "active" ? "启用" : "禁用"}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell className="text-muted-foreground">{user.lastLogin}</TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-2">
                            <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground">
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-red-500">
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* 交易时段 */}
          <TabsContent value="trading" className="space-y-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-foreground">交易时段配置</CardTitle>
                  <CardDescription className="text-muted-foreground">
                    设置允许交易的时间段
                  </CardDescription>
                </div>
                <Button className="bg-orange-500 hover:bg-orange-600">
                  <Plus className="w-4 h-4 mr-2" />
                  添加时段
                </Button>
              </CardHeader>
              <CardContent className="space-y-4">
                {tradingSessions.map((session) => (
                  <div
                    key={session.id}
                    className="flex items-center justify-between p-4 glass-card rounded-lg"
                  >
                    <div className="flex items-center gap-4">
                      <Switch
                        checked={session.enabled}
                        onCheckedChange={(checked) => {
                          setTradingSessions((prev) =>
                            prev.map((s) => (s.id === session.id ? { ...s, enabled: checked } : s))
                          )
                        }}
                        className="data-[state=checked]:bg-orange-500"
                      />
                      <div>
                        <p className="text-foreground font-medium">{session.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {session.startTime} - {session.endTime}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground">
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-red-500">
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}

                <div className="pt-4 border-t border-border">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-foreground font-medium">全局交易开关</p>
                      <p className="text-sm text-muted-foreground">关闭后将禁止所有交易操作</p>
                    </div>
                    <Switch defaultChecked className="data-[state=checked]:bg-green-500" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* 通知配置 */}
          <TabsContent value="notifications" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* 邮件通知 */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-foreground text-base">邮件通知</CardTitle>
                    <Switch
                      checked={notifications.email}
                      onCheckedChange={(checked) =>
                        setNotifications((prev) => ({ ...prev, email: checked }))
                      }
                      className="data-[state=checked]:bg-orange-500"
                    />
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label className="text-muted-foreground">接收邮箱</Label>
                    <Input
                      value={notifications.emailAddress}
                      onChange={(e) =>
                        setNotifications((prev) => ({ ...prev, emailAddress: e.target.value }))
                      }
                      disabled={!notifications.email}
                      className="bg-background border-input text-foreground disabled:opacity-50"
                    />
                  </div>
                </CardContent>
              </Card>

              {/* 钉钉通知 */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-foreground text-base">钉钉机器人</CardTitle>
                    <Switch
                      checked={notifications.dingding}
                      onCheckedChange={(checked) =>
                        setNotifications((prev) => ({ ...prev, dingding: checked }))
                      }
                      className="data-[state=checked]:bg-orange-500"
                    />
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label className="text-muted-foreground">Access Token</Label>
                    <Input
                      type="password"
                      value={notifications.dingdingToken}
                      onChange={(e) =>
                        setNotifications((prev) => ({ ...prev, dingdingToken: e.target.value }))
                      }
                      disabled={!notifications.dingding}
                      className="bg-background border-input text-foreground disabled:opacity-50"
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Webhook */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-foreground text-base">Webhook</CardTitle>
                    <Switch
                      checked={notifications.webhook}
                      onCheckedChange={(checked) =>
                        setNotifications((prev) => ({ ...prev, webhook: checked }))
                      }
                      className="data-[state=checked]:bg-orange-500"
                    />
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label className="text-muted-foreground">Webhook URL</Label>
                    <Input
                      value={notifications.webhookUrl}
                      onChange={(e) =>
                        setNotifications((prev) => ({ ...prev, webhookUrl: e.target.value }))
                      }
                      placeholder="https://..."
                      disabled={!notifications.webhook}
                      className="bg-background border-input text-foreground disabled:opacity-50"
                    />
                  </div>
                </CardContent>
              </Card>

              {/* 企业微信 */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-foreground text-base">企业微信</CardTitle>
                    <Switch
                      checked={notifications.wecom}
                      onCheckedChange={(checked) =>
                        setNotifications((prev) => ({ ...prev, wecom: checked }))
                      }
                      className="data-[state=checked]:bg-orange-500"
                    />
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label className="text-muted-foreground">Corp Key</Label>
                    <Input
                      type="password"
                      value={notifications.wecomKey}
                      onChange={(e) =>
                        setNotifications((prev) => ({ ...prev, wecomKey: e.target.value }))
                      }
                      disabled={!notifications.wecom}
                      className="bg-background border-input text-foreground disabled:opacity-50"
                    />
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* 安全设置 */}
          <TabsContent value="security" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-foreground">安全设置</CardTitle>
                <CardDescription className="text-muted-foreground">
                  配置系统安全相关选项
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label className="text-muted-foreground">会话超时时间（分钟）</Label>
                    <Input
                      type="number"
                      value={securitySettings.sessionTimeout}
                      onChange={(e) =>
                        setSecuritySettings((prev) => ({ ...prev, sessionTimeout: e.target.value }))
                      }
                      className="bg-background border-input text-foreground"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-muted-foreground">最大登录尝试次数</Label>
                    <Input
                      type="number"
                      value={securitySettings.maxLoginAttempts}
                      onChange={(e) =>
                        setSecuritySettings((prev) => ({ ...prev, maxLoginAttempts: e.target.value }))
                      }
                      className="bg-background border-input text-foreground"
                    />
                  </div>
                </div>

                <div className="space-y-4 pt-4 border-t border-border">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-foreground font-medium">双因素认证</p>
                      <p className="text-sm text-muted-foreground">启用后登录需要额外验证</p>
                    </div>
                    <Switch
                      checked={securitySettings.twoFactor}
                      onCheckedChange={(checked) =>
                        setSecuritySettings((prev) => ({ ...prev, twoFactor: checked }))
                      }
                      className="data-[state=checked]:bg-orange-500"
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-foreground font-medium">IP 白名单</p>
                      <p className="text-sm text-muted-foreground">仅允许特定 IP 访问系统</p>
                    </div>
                    <Switch
                      checked={securitySettings.ipWhitelist}
                      onCheckedChange={(checked) =>
                        setSecuritySettings((prev) => ({ ...prev, ipWhitelist: checked }))
                      }
                      className="data-[state=checked]:bg-orange-500"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* 其他 Tabs 占位 */}
          {["holidays", "database", "api", "system"].map((tabId) => (
            <TabsContent key={tabId} value={tabId}>
              <Card>
                <CardContent className="py-16 text-center">
                  <p className="text-muted-foreground">
                    {tabId === "holidays" && "节假日配置功能开发中..."}
                    {tabId === "database" && "数据管理功能开发中..."}
                    {tabId === "api" && "API 密钥管理功能开发中..."}
                    {tabId === "system" && "系统监控功能开发中..."}
                  </p>
                </CardContent>
              </Card>
            </TabsContent>
          ))}
        </Tabs>

        {/* 保存按钮 */}
        <div className="fixed bottom-6 right-6">
          <Button onClick={handleSave} className="bg-orange-500 hover:bg-orange-600 shadow-lg">
            <Save className="w-4 h-4 mr-2" />
            保存设置
          </Button>
        </div>
      </div>
    </MainLayout>
  )
}
