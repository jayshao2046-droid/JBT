"use client"

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { useState } from "react"
import type { StrategySignal } from "@/lib/api/types"

interface DisableSignalDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  signal: StrategySignal | null
  onConfirm?: (data: DisableSignalData) => void
}

export interface DisableSignalData {
  signalId: string
  reason: string
  remarks: string
}

export function DisableSignalDialog({
  open,
  onOpenChange,
  signal,
  onConfirm,
}: DisableSignalDialogProps) {
  const [reason, setReason] = useState("")
  const [remarks, setRemarks] = useState("")

  const reasonOptions = [
    { value: "invalid", label: "策略失效" },
    { value: "market-change", label: "市场环境变化" },
    { value: "manual", label: "手动干预" },
    { value: "other", label: "其他" },
  ]

  const handleConfirm = () => {
    if (signal && reason) {
      onConfirm?.({
        signalId: signal.id,
        reason,
        remarks,
      })
      onOpenChange(false)
      setReason("")
      setRemarks("")
    }
  }

  if (!signal) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-neutral-900 border-neutral-800">
        <DialogHeader>
          <DialogTitle>禁止信号</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="bg-neutral-800/50 rounded-lg p-3 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-neutral-400">品种</span>
              <span className="font-mono font-semibold text-white">{signal.instrument_id}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-neutral-400">策略</span>
              <span className="text-sm text-white">{signal.strategy_name}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-neutral-400">置信度</span>
              <span className="text-sm font-semibold text-orange-400">{signal.confidence}%</span>
            </div>
          </div>

          <div className="border-t border-neutral-800 pt-4 space-y-3">
            <div>
              <Label className="text-neutral-400 text-sm mb-2">禁止原因</Label>
              <div className="space-y-2">
                {reasonOptions.map((option) => (
                  <div key={option.value} className="flex items-center gap-2">
                    <Checkbox
                      id={option.value}
                      checked={reason === option.value}
                      onCheckedChange={() => setReason(option.value)}
                    />
                    <label htmlFor={option.value} className="text-sm text-neutral-300 cursor-pointer">
                      {option.label}
                    </label>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <Label className="text-neutral-400 text-sm mb-2">备注</Label>
              <Textarea
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
                placeholder="请输入禁止原因的详细说明..."
                className="bg-neutral-800 border-neutral-700 text-white text-sm"
                rows={3}
              />
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleConfirm} disabled={!reason} className="bg-yellow-600 hover:bg-yellow-700">
            确认禁止
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
