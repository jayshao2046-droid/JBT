'use client'

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { PositionData } from '@/lib/mock-data'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useState } from 'react'
import { cn } from '@/lib/utils'

interface ClosePositionDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  position: PositionData | null
  onConfirm?: (data: ClosePositionData) => void
}

export interface ClosePositionData {
  positionId: string
  quantity: number
  closeType: 'full' | 'partial'
}

export function ClosePositionDialog({
  open,
  onOpenChange,
  position,
  onConfirm,
}: ClosePositionDialogProps) {
  const [closeType, setCloseType] = useState<'full' | 'partial'>('full')
  const [quantity, setQuantity] = useState('')

  const handleConfirm = () => {
    const closeQty = closeType === 'full' ? position?.quantity : parseInt(quantity)
    if (position && closeQty) {
      onConfirm?.({
        positionId: position.id,
        quantity: closeQty,
        closeType,
      })
      onOpenChange(false)
    }
  }

  if (!position) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-neutral-900 border-neutral-800">
        <DialogHeader>
          <DialogTitle>平仓确认</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="bg-neutral-800/50 rounded-lg p-3 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-neutral-400">品种</span>
              <span className="font-mono font-semibold text-white">{position.symbol}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">方向</span>
              <span
                className={`text-sm font-semibold ${
                  position.direction === 'long' ? 'text-red-400' : 'text-green-400'
                }`}
              >
                {position.direction === 'long' ? '多头' : '空头'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-neutral-400">持仓数量</span>
              <span className="font-mono font-semibold text-white">{position.quantity}手</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-neutral-400">成本价</span>
              <span className="font-mono text-neutral-300">¥{position.costPrice.toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-neutral-400">当前价</span>
              <span className="font-mono text-neutral-300">¥{position.currentPrice.toFixed(2)}</span>
            </div>
            <div className="border-t border-border pt-2 mt-2 flex items-center justify-between">
              <span className="text-sm text-muted-foreground">预期盈亏</span>
              <span
                className={`font-mono font-semibold ${
                  position.profitLoss >= 0 ? 'text-red-400' : 'text-green-400'
                }`}
              >
                {position.profitLoss >= 0 ? '+' : ''}¥{position.profitLoss.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </span>
            </div>
          </div>

          <div className="border-t border-neutral-800 pt-4">
            <Tabs value={closeType} onValueChange={(v) => setCloseType(v as 'full' | 'partial')}>
              <TabsList className="w-full bg-neutral-800">
                <TabsTrigger value="full" className="flex-1">全部平仓</TabsTrigger>
                <TabsTrigger value="partial" className="flex-1">部分平仓</TabsTrigger>
              </TabsList>
              <TabsContent value="partial" className="mt-3">
                <div>
                  <Label className="text-neutral-400 text-sm mb-2">平仓数量（手）</Label>
                  <Input
                    type="number"
                    value={quantity}
                    onChange={(e) => setQuantity(e.target.value)}
                    placeholder={`1-${position.quantity}`}
                    className="bg-neutral-800 border-neutral-700 text-white"
                    min="1"
                    max={position.quantity}
                    step="1"
                  />
                  <p className="text-xs text-neutral-500 mt-1">
                    最多可平 {position.quantity} 手
                  </p>
                </div>
              </TabsContent>
            </Tabs>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button
            onClick={handleConfirm}
            className={cn(
              position.direction === 'long'
                ? 'bg-green-600 hover:bg-green-700'
                : 'bg-red-600 hover:bg-red-700'
            )}
          >
            {closeType === 'full' ? '全部平仓' : '部分平仓'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
