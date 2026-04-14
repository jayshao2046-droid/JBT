"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useBacktest } from "@/hooks/use-backtest"
import { backtestApi } from "@/lib/api/backtest"
import { useToast } from "@/hooks/use-toast"
import { Skeleton } from "@/components/ui/skeleton"
import MainLayout from "@/components/layout/main-layout"

export default function OperationsPage() {
  const { strategies, loading, refetch } = useBacktest()
  const { toast } = useToast()
  const [form, setForm] = useState({
    strategy_name: "",
    start_date: "",
    end_date: "",
    params: {} as Record<string, unknown>,
  })
  const [running, setRunning] = useState(false)

  const safeStrategies = Array.isArray(strategies) ? strategies : []

  const handleRun = async () => {
    try {
      setRunning(true)
      const res = await backtestApi.runBacktest(form)
      toast({ title: "回测已启动", description: `任务ID: ${res.task_id}` })
      refetch()
      setForm({ strategy_name: "", start_date: "", end_date: "", params: {} })
    } catch (err) {
      toast({ title: "启动失败", description: err instanceof Error ? err.message : "未知错误", variant: "destructive" })
    } finally {
      setRunning(false)
    }
  }

  if (loading) {
    return (
      <MainLayout title="回测操作" onRefresh={refetch}>
        <div className="p-6 space-y-6">
          <Skeleton className="h-96" />
        </div>
      </MainLayout>
    )
  }

  return (
    <MainLayout title="回测操作" onRefresh={refetch}>
      <div className="p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>发起回测</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>策略</Label>
            <Select value={form.strategy_name} onValueChange={(v) => setForm({ ...form, strategy_name: v })}>
              <SelectTrigger>
                <SelectValue placeholder="选择策略" />
              </SelectTrigger>
              <SelectContent>
                {safeStrategies.map((s) => (
                  <SelectItem key={s.name} value={s.name}>
                    {s.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>开始日期</Label>
              <Input
                type="date"
                value={form.start_date}
                onChange={(e) => setForm({ ...form, start_date: e.target.value })}
              />
            </div>
            <div>
              <Label>结束日期</Label>
              <Input
                type="date"
                value={form.end_date}
                onChange={(e) => setForm({ ...form, end_date: e.target.value })}
              />
            </div>
          </div>
          <Button onClick={handleRun} disabled={running || !form.strategy_name} className="w-full">
            {running ? "运行中..." : "开始回测"}
          </Button>
        </CardContent>
      </Card>
    </div>
    </MainLayout>
  )
}
