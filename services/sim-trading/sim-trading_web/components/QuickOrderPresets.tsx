"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Plus, Trash2, Zap } from "lucide-react"
import { simApi } from "@/lib/sim-api"
import { toast } from "sonner"

interface QuickOrderPreset {
  id: string
  name: string
  contract: string
  direction: "buy" | "sell"
  offset: "open" | "close" | "close_today"
  quantity: number
  hotkey?: string
}

export function QuickOrderPresets() {
  const [presets, setPresets] = useState<QuickOrderPreset[]>([])
  const [showAdd, setShowAdd] = useState(false)
  const [newPreset, setNewPreset] = useState<Partial<QuickOrderPreset>>({
    name: "",
    contract: "",
    direction: "buy",
    offset: "open",
    quantity: 1,
  })

  useEffect(() => {
    // 从 localStorage 加载预设
    const saved = localStorage.getItem("quickOrderPresets")
    if (saved) {
      try {
        setPresets(JSON.parse(saved))
      } catch (err) {
        console.error("加载预设失败:", err)
      }
    }
  }, [])

  useEffect(() => {
    // 保存预设到 localStorage
    localStorage.setItem("quickOrderPresets", JSON.stringify(presets))
  }, [presets])

  useEffect(() => {
    // 监听快捷键
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.key >= "F1" && e.key <= "F12") {
        e.preventDefault()
        const preset = presets.find((p) => p.hotkey === e.key)
        if (preset) {
          executeQuickOrder(preset)
        }
      }
    }

    window.addEventListener("keydown", handleKeyPress)
    return () => window.removeEventListener("keydown", handleKeyPress)
  }, [presets])

  const executeQuickOrder = async (preset: QuickOrderPreset) => {
    try {
      const result = await simApi.createOrder({
        instrument_id: preset.contract,
        direction: preset.direction,
        offset: preset.offset,
        price: 0, // 市价单
        volume: preset.quantity,
      })

      if (result.rejected) {
        toast.error(`下单失败: ${result.error}`)
      } else {
        toast.success(`快速下单成功: ${preset.name}`)
      }
    } catch (err) {
      toast.error(`下单失败: ${err}`)
    }
  }

  const addPreset = () => {
    if (!newPreset.name || !newPreset.contract) {
      toast.error("请填写预设名称和合约代码")
      return
    }

    const preset: QuickOrderPreset = {
      id: Date.now().toString(),
      name: newPreset.name,
      contract: newPreset.contract,
      direction: newPreset.direction || "buy",
      offset: newPreset.offset || "open",
      quantity: newPreset.quantity || 1,
      hotkey: newPreset.hotkey,
    }

    setPresets([...presets, preset])
    setNewPreset({ name: "", contract: "", direction: "buy", offset: "open", quantity: 1 })
    setShowAdd(false)
    toast.success("预设已添加")
  }

  const deletePreset = (id: string) => {
    setPresets(presets.filter((p) => p.id !== id))
    toast.success("预设已删除")
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">快速下单预设</CardTitle>
          <Button size="sm" variant="outline" onClick={() => setShowAdd(!showAdd)}>
            <Plus className="h-4 w-4 mr-1" />
            添加预设
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {showAdd && (
          <div className="border rounded-lg p-4 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>预设名称</Label>
                <Input
                  value={newPreset.name}
                  onChange={(e) => setNewPreset({ ...newPreset, name: e.target.value })}
                  placeholder="例如：RB多开1手"
                />
              </div>
              <div>
                <Label>合约代码</Label>
                <Input
                  value={newPreset.contract}
                  onChange={(e) => setNewPreset({ ...newPreset, contract: e.target.value })}
                  placeholder="例如：RB2505"
                />
              </div>
              <div>
                <Label>方向</Label>
                <Select
                  value={newPreset.direction}
                  onValueChange={(v) => setNewPreset({ ...newPreset, direction: v as "buy" | "sell" })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="buy">买入</SelectItem>
                    <SelectItem value="sell">卖出</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>开平</Label>
                <Select
                  value={newPreset.offset}
                  onValueChange={(v) => setNewPreset({ ...newPreset, offset: v as "open" | "close" })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="open">开仓</SelectItem>
                    <SelectItem value="close">平仓</SelectItem>
                    <SelectItem value="close_today">平今</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>手数</Label>
                <Input
                  type="number"
                  value={newPreset.quantity}
                  onChange={(e) => setNewPreset({ ...newPreset, quantity: parseInt(e.target.value) || 1 })}
                />
              </div>
              <div>
                <Label>快捷键（可选）</Label>
                <Input
                  value={newPreset.hotkey || ""}
                  onChange={(e) => setNewPreset({ ...newPreset, hotkey: e.target.value })}
                  placeholder="例如：F1"
                />
              </div>
            </div>
            <div className="flex justify-end space-x-2">
              <Button size="sm" variant="outline" onClick={() => setShowAdd(false)}>
                取消
              </Button>
              <Button size="sm" onClick={addPreset}>
                保存
              </Button>
            </div>
          </div>
        )}

        <div className="grid grid-cols-4 gap-2">
          {presets.map((preset) => (
            <Button
              key={preset.id}
              variant="outline"
              className="h-auto flex flex-col items-start p-3 relative group"
              onClick={() => executeQuickOrder(preset)}
            >
              <div className="flex items-center justify-between w-full">
                <Zap className="h-4 w-4 text-orange-500" />
                {preset.hotkey && (
                  <span className="text-xs text-muted-foreground">{preset.hotkey}</span>
                )}
              </div>
              <div className="text-sm font-medium mt-1">{preset.name}</div>
              <div className="text-xs text-muted-foreground">
                {preset.contract} {preset.direction === "buy" ? "买" : "卖"}
                {preset.offset === "open" ? "开" : "平"} {preset.quantity}手
              </div>
              <Button
                size="sm"
                variant="ghost"
                className="absolute top-1 right-1 h-6 w-6 p-0 opacity-0 group-hover:opacity-100"
                onClick={(e) => {
                  e.stopPropagation()
                  deletePreset(preset.id)
                }}
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            </Button>
          ))}
        </div>

        {presets.length === 0 && !showAdd && (
          <div className="text-center text-sm text-muted-foreground py-8">
            暂无预设，点击"添加预设"创建快速下单按钮
          </div>
        )}
      </CardContent>
    </Card>
  )
}
