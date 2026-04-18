"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { simTradingApi } from "@/lib/api/sim-trading"
import type { Position } from "@/lib/api/types"

interface BatchCloseDialogProps {
  positions: Position[]
  onSuccess?: () => void
}

export function BatchCloseDialog({ positions, onSuccess }: BatchCloseDialogProps) {
  const [open, setOpen] = useState(false)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)

  const handleToggle = (positionId: string) => {
    const newSelected = new Set(selected)
    if (newSelected.has(positionId)) {
      newSelected.delete(positionId)
    } else {
      newSelected.add(positionId)
    }
    setSelected(newSelected)
  }

  const handleConfirm = async () => {
    if (selected.size === 0) {
      alert("请至少选择一个持仓")
      return
    }
    if (password !== "confirm") {
      alert("确认密码错误")
      return
    }

    setLoading(true)
    try {
      const result = await simTradingApi.batchClosePositions(Array.from(selected))
      alert(`批量平仓完成：成功 ${result.success}，失败 ${result.failed}`)
      setOpen(false)
      setSelected(new Set())
      setPassword("")
      onSuccess?.()
    } catch (err) {
      console.error("Batch close failed:", err)
      alert(`批量平仓失败: ${err}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="destructive">批量平仓</Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>批量平仓</DialogTitle>
          <DialogDescription>
            选择要平仓的持仓，输入确认密码 &quot;confirm&quot; 后执行
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="border rounded-lg p-4 space-y-2 max-h-[300px] overflow-y-auto">
            {positions.length === 0 ? (
              <div className="text-center text-muted-foreground py-4">暂无持仓</div>
            ) : (
              positions.map((pos) => (
                <div key={pos.instrument_id} className="flex items-center space-x-2 p-2 hover:bg-accent rounded">
                  <Checkbox
                    checked={selected.has(pos.instrument_id)}
                    onCheckedChange={() => handleToggle(pos.instrument_id)}
                  />
                  <div className="flex-1">
                    <div className="font-medium">{pos.instrument_id}</div>
                    <div className="text-sm text-muted-foreground">
                      {pos.direction === "long" ? "多" : "空"} | 数量: {pos.volume} | 盈亏: {pos.float_pnl?.toFixed(2) || "N/A"}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">确认密码</Label>
            <Input
              id="password"
              type="password"
              placeholder="输入 'confirm' 确认"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <div className="text-sm text-muted-foreground">
            已选择 {selected.size} 个持仓
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            取消
          </Button>
          <Button variant="destructive" onClick={handleConfirm} disabled={loading || selected.size === 0}>
            {loading ? "执行中..." : "确认平仓"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
