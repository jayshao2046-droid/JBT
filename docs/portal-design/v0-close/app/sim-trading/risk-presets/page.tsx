"use client"

import { useState } from "react"
import { Shield, Edit, Save, X, Plus } from "lucide-react"
import { MainLayout } from "@/components/layout/main-layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { toast } from "sonner"

const riskPresets = [
  { symbol: "IF", name: "沪深300股指期货", enabled: true, maxPos: 5, maxLoss: 50000, stopLossPct: 1.5, stopProfitPct: 3.0 },
  { symbol: "IC", name: "中证500股指期货", enabled: true, maxPos: 3, maxLoss: 30000, stopLossPct: 2.0, stopProfitPct: 4.0 },
  { symbol: "RB", name: "螺纹钢", enabled: true, maxPos: 20, maxLoss: 15000, stopLossPct: 1.0, stopProfitPct: 2.0 },
  { symbol: "CU", name: "铜", enabled: false, maxPos: 5, maxLoss: 20000, stopLossPct: 0.8, stopProfitPct: 1.5 },
  { symbol: "AU", name: "黄金", enabled: true, maxPos: 10, maxLoss: 10000, stopLossPct: 0.5, stopProfitPct: 1.0 },
]

export default function SimRiskPresetsPage() {
  const [presets, setPresets] = useState(riskPresets)
  const [editingId, setEditingId] = useState<string | null>(null)

  const handleToggle = (symbol: string) => {
    setPresets((prev) => prev.map((p) => p.symbol === symbol ? { ...p, enabled: !p.enabled } : p))
    toast.success("风控状态已更新")
  }

  const handleSave = () => {
    setEditingId(null)
    toast.success("风控参数已保存")
  }

  return (
    <MainLayout title="模拟交易" subtitle="品种风控">
      <div className="p-4 md:p-6 space-y-6">
        {/* 全局风控设置 */}
        <Card className="border-orange-500/30">
          <CardHeader className="pb-3">
            <CardTitle className="text-base text-foreground flex items-center gap-2">
              <Shield className="w-4 h-4 text-orange-500" />
              全局风控参数
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: "账户最大风险度", value: "60%", desc: "超过此值触发平仓警告" },
                { label: "单日最大亏损", value: "¥50,000", desc: "超过此值强制停止交易" },
                { label: "单品种最大持仓", value: "30%", desc: "单品种保证金占比上限" },
                { label: "全局止损开关", value: "已开启", desc: "自动止损保护" },
              ].map((item) => (
                <div key={item.label} className="p-3 glass-card rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">{item.label}</p>
                  <p className="text-base font-semibold text-orange-400">{item.value}</p>
                  <p className="text-xs text-muted-foreground/60 mt-1">{item.desc}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* 品种风控列表 */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-base text-foreground flex items-center gap-2">
              <Shield className="w-4 h-4 text-blue-500" />
              品种风控配置
            </CardTitle>
            <Button size="sm" className="bg-orange-500 hover:bg-orange-600 text-white text-xs">
              <Plus className="w-3 h-3 mr-1" />
              新增品种
            </Button>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    {["品种", "启用", "最大持仓(手)", "最大亏损(元)", "止损(%)", "止盈(%)", "操作"].map((h) => (
                      <th key={h} className="text-left py-3 px-4 text-xs text-muted-foreground font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {presets.map((preset) => (
                    <tr key={preset.symbol} className="border-b border-border/50 hover:bg-muted/20">
                      <td className="py-3 px-4">
                        <div>
                          <p className="text-foreground font-mono font-medium">{preset.symbol}</p>
                          <p className="text-xs text-muted-foreground">{preset.name}</p>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <Switch
                          checked={preset.enabled}
                          onCheckedChange={() => handleToggle(preset.symbol)}
                          className="data-[state=checked]:bg-orange-500"
                        />
                      </td>
                      {editingId === preset.symbol ? (
                        <>
                          <td className="py-3 px-4"><Input defaultValue={preset.maxPos} className="w-20 h-7 text-xs" /></td>
                          <td className="py-3 px-4"><Input defaultValue={preset.maxLoss} className="w-24 h-7 text-xs" /></td>
                          <td className="py-3 px-4"><Input defaultValue={preset.stopLossPct} className="w-20 h-7 text-xs" /></td>
                          <td className="py-3 px-4"><Input defaultValue={preset.stopProfitPct} className="w-20 h-7 text-xs" /></td>
                          <td className="py-3 px-4">
                            <div className="flex gap-1">
                              <Button size="icon" variant="ghost" onClick={handleSave} className="h-7 w-7 text-green-500 hover:text-green-400 hover:bg-muted">
                                <Save className="w-3.5 h-3.5" />
                              </Button>
                              <Button size="icon" variant="ghost" onClick={() => setEditingId(null)} className="h-7 w-7 text-muted-foreground hover:text-foreground hover:bg-muted">
                                <X className="w-3.5 h-3.5" />
                              </Button>
                            </div>
                          </td>
                        </>
                      ) : (
                        <>
                          <td className="py-3 px-4 text-foreground font-mono">{preset.maxPos}</td>
                          <td className="py-3 px-4 text-foreground font-mono">{preset.maxLoss.toLocaleString()}</td>
                          <td className="py-3 px-4 text-red-400 font-mono">{preset.stopLossPct}%</td>
                          <td className="py-3 px-4 text-green-400 font-mono">{preset.stopProfitPct}%</td>
                          <td className="py-3 px-4">
                            <Button size="icon" variant="ghost" onClick={() => setEditingId(preset.symbol)} className="h-7 w-7 text-muted-foreground hover:text-foreground hover:bg-muted">
                              <Edit className="w-3.5 h-3.5" />
                            </Button>
                          </td>
                        </>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  )
}
