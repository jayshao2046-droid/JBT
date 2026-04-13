'use client'

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { StrategySignal } from '@/lib/mock-data'
import { useState } from 'react'

interface SignalConfirmDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  signal: StrategySignal | null
  onConfirm?: (data: SignalOrderData) => void
}

export interface SignalOrderData {
  signalId: string
  quantity: number
  stopLoss: number
  takeProfit: number
}

export function SignalConfirmDialog({
  open,
  onOpenChange,
  signal,
  onConfirm,
}: SignalConfirmDialogProps) {
  const [quantity, setQuantity] = useState('10')
  const [stopLoss, setStopLoss] = useState('')
  const [takeProfit, setTakeProfit] = useState('')

  const handleConfirm = () => {
    if (signal && quantity && stopLoss && takeProfit) {
      onConfirm?.({
        signalId: signal.id,
        quantity: parseInt(quantity),
        stopLoss: parseFloat(stopLoss),
        takeProfit: parseFloat(takeProfit),
      })
      onOpenChange(false)
    }
  }

  if (!signal) return null

  const signalLabel = {
    bullish: '看多',
    bearish: '看空',
    neutral: '观望',
  }[signal.signalType]

  const signalColor = {
    bullish: 'text-red-400',
    bearish: 'text-green-400',
    neutral: 'text-yellow-400',
  }[signal.signalType]

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-neutral-900 border-neutral-800">
        <DialogHeader>
          <DialogTitle>信号确认下单</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="bg-neutral-800/50 rounded-lg p-3 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-neutral-400">品种</span>
              <span className="font-mono font-semibold text-white">{signal.symbol}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-neutral-400">当前价格</span>
              <span className="font-mono font-semibold text-white">¥{signal.price.toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-neutral-400">策略名称</span>
              <span className="text-sm text-white">{signal.strategyName}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-neutral-400">信号方向</span>
              <span className={`text-sm font-semibold ${signalColor}`}>{signalLabel}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-neutral-400">置信度</span>
              <span className="text-sm font-semibold text-orange-400">{signal.confidence}%</span>
            </div>
          </div>

          <div className="space-y-3 border-t border-neutral-800 pt-4">
            <div>
              <Label className="text-neutral-400 text-sm">开仓数量（手）</Label>
              <Input
                type="number"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                className="bg-neutral-800 border-neutral-700 text-white"
                min="1"
                step="1"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-neutral-400 text-sm">止损价</Label>
                <Input
                  type="number"
                  value={stopLoss}
                  onChange={(e) => setStopLoss(e.target.value)}
                  placeholder="0.00"
                  className="bg-neutral-800 border-neutral-700 text-white"
                  step="0.01"
                />
              </div>
              <div>
                <Label className="text-neutral-400 text-sm">止盈价</Label>
                <Input
                  type="number"
                  value={takeProfit}
                  onChange={(e) => setTakeProfit(e.target.value)}
                  placeholder="0.00"
                  className="bg-neutral-800 border-neutral-700 text-white"
                  step="0.01"
                />
              </div>
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button
            onClick={handleConfirm}
            className="bg-orange-600 hover:bg-orange-700"
          >
            确认开仓
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
