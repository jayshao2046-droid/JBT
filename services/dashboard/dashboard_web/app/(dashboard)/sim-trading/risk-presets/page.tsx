"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { simTradingApi, type RiskPreset } from "@/lib/api/sim-trading"
import { useToast } from "@/hooks/use-toast"
import { Skeleton } from "@/components/ui/skeleton"

export default function RiskPresetsPage() {
  const { toast } = useToast()
  const [presets, setPresets] = useState<Record<string, RiskPreset>>({})
  const [loading, setLoading] = useState(true)
  const [editingSymbol, setEditingSymbol] = useState<string | null>(null)
  const [editForm, setEditForm] = useState<RiskPreset | null>(null)

  const exchanges = ["SHFE", "DCE", "CZCE", "CFFEX", "INE", "GFEX"]

  useEffect(() => {
    fetchPresets()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const fetchPresets = async () => {
    try {
      setLoading(true)
      const res = await simTradingApi.getRiskPresets()
      setPresets(res.presets)
    } catch (err) {
      toast({ title: "加载失败", description: err instanceof Error ? err.message : "未知错误", variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = (symbol: string, preset: RiskPreset) => {
    setEditingSymbol(symbol)
    setEditForm(preset)
  }

  const handleSave = async () => {
    if (!editingSymbol || !editForm) return
    try {
      await simTradingApi.updateRiskPreset({ symbol: editingSymbol, ...editForm })
      toast({ title: "保存成功", description: `${editingSymbol} 风控预设已更新` })
      setEditingSymbol(null)
      setEditForm(null)
      fetchPresets()
    } catch (err) {
      toast({ title: "保存失败", description: err instanceof Error ? err.message : "未知错误", variant: "destructive" })
    }
  }

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-96" />
      </div>
    )
  }

  const getPresetsByExchange = (exchange: string) => {
    return Object.entries(presets).filter(([symbol]) => {
      // 简单判断：根据合约代码后缀判断交易所
      if (exchange === "SHFE") return symbol.endsWith("M") && !["iM", "jM", "jmM", "aM", "bM", "mM", "yM", "pM", "cM", "csM", "rrM", "lhM", "vM", "lM", "ppM", "egM", "ebM", "pgM"].includes(symbol)
      if (exchange === "DCE") return ["iM", "jM", "jmM", "aM", "bM", "mM", "yM", "pM", "cM", "csM", "rrM", "lhM", "vM", "lM", "ppM", "egM", "ebM", "pgM"].includes(symbol)
      if (exchange === "CZCE") return symbol.endsWith("M") && symbol.length === 3
      if (exchange === "CFFEX") return ["IF", "IC", "IH", "IM", "T", "TF", "TS", "TL"].includes(symbol)
      if (exchange === "INE") return ["scM", "luM"].includes(symbol)
      if (exchange === "GFEX") return ["siM", "lcM"].includes(symbol)
      return false
    })
  }

  return (
    <div className="p-6 space-y-6">
      <Tabs defaultValue="SHFE">
        <TabsList className="grid w-full grid-cols-6">
          {exchanges.map((ex) => (
            <TabsTrigger key={ex} value={ex}>
              {ex}
            </TabsTrigger>
          ))}
        </TabsList>

        {exchanges.map((exchange) => (
          <TabsContent key={exchange} value={exchange}>
            <Card>
              <CardHeader>
                <CardTitle>{exchange} 品种风控</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {getPresetsByExchange(exchange).length === 0 ? (
                    <p className="text-muted-foreground text-sm">暂无品种</p>
                  ) : (
                    getPresetsByExchange(exchange).map(([symbol, preset]) => (
                      <div key={symbol} className="p-3 border rounded">
                        {editingSymbol === symbol ? (
                          <div className="space-y-3">
                            <div className="grid grid-cols-2 gap-3">
                              <div>
                                <Label>最大手数</Label>
                                <Input
                                  type="number"
                                  value={editForm?.max_lots || 0}
                                  onChange={(e) => setEditForm({ ...editForm!, max_lots: parseInt(e.target.value) || 0 })}
                                />
                              </div>
                              <div>
                                <Label>最大持仓</Label>
                                <Input
                                  type="number"
                                  value={editForm?.max_position || 0}
                                  onChange={(e) => setEditForm({ ...editForm!, max_position: parseInt(e.target.value) || 0 })}
                                />
                              </div>
                              <div>
                                <Label>日内亏损比例 (%)</Label>
                                <Input
                                  type="number"
                                  value={(editForm?.daily_loss_pct || 0) * 100}
                                  onChange={(e) => setEditForm({ ...editForm!, daily_loss_pct: parseFloat(e.target.value) / 100 || 0 })}
                                />
                              </div>
                              <div>
                                <Label>价格偏离比例 (%)</Label>
                                <Input
                                  type="number"
                                  value={(editForm?.price_dev_pct || 0) * 100}
                                  onChange={(e) => setEditForm({ ...editForm!, price_dev_pct: parseFloat(e.target.value) / 100 || 0 })}
                                />
                              </div>
                            </div>
                            <div className="flex gap-2">
                              <Button onClick={handleSave}>保存</Button>
                              <Button variant="outline" onClick={() => { setEditingSymbol(null); setEditForm(null) }}>
                                取消
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="font-medium">{symbol}</p>
                              <p className="text-xs text-muted-foreground">
                                最大手数: {preset.max_lots} | 最大持仓: {preset.max_position} | 日亏损: {(preset.daily_loss_pct * 100).toFixed(1)}%
                              </p>
                            </div>
                            <Button size="sm" variant="outline" onClick={() => handleEdit(symbol, preset)}>
                              编辑
                            </Button>
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}
