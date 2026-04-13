"use client"

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useState } from "react"
import { cn } from "@/lib/utils"

interface ManualOpenDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onConfirm?: (data: ManualOrderData) => void
}

export interface ManualOrderData {
  symbol: string
  direction: "long" | "short"
  quantity: number
  price: number
  stopLoss: number
  takeProfit: number
}

export function ManualOpenDialog({ open, onOpenChange, onConfirm }: ManualOpenDialogProps) {
  const [symbol, setSymbol] = useState("")
  const [direction, setDirection] = useState<"long" | "short">("long")
  const [quantity, setQuantity] = useState("")
  const [price, setPrice] = useState("")
  const [stopLoss, setStopLoss] = useState("")
  const [takeProfit, setTakeProfit] = useState("")

  const handleConfirm = () => {
    if (symbol && quantity && price && stopLoss && takeProfit) {
      onConfirm?.({
        symbol,
        direction,
        quantity: parseInt(quantity),
        price: parseFloat(price),
        stopLoss: parseFloat(stopLoss),
        takeProfit: parseFloat(takeProfit),
      })
      onOpenChange(false)
      setSymbol("")
      setDirection("long")
      setQuantity("")
      setPrice("")
      setStopLoss("")
      setTakeProfit("")
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-neutral-900 border-neutral-800 max-w-lg">
        <DialogHeader>
          <DialogTitle>手动开仓</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label className="text-neutral-400 text-sm">品种代码</Label>
            <Input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              placeholder="如：IF2504"
              className="bg-neutral-800 border-neutral-700 text-white mt-1"
            />
          </div>

          <div>
            <Label className="text-muted-foreground text-sm mb-2">交易方向</Label>
            <Tabs value={direction} onValueChange={(v) => setDirection(v as "long" | "short")}>
              <TabsList className="w-full">
                <TabsTrigger
                  value="long"
                  className="flex-1 data-[state=active]:bg-red-600 data-[state=active]:text-white"
                >
                  做多
                </TabsTrigger>
                <TabsTrigger
                  value="short"
                  className="flex-1 data-[state=active]:bg-green-600 data-[state=active]:text-white"
                >
                  做空
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-neutral-400 text-sm">开仓数量（手）</Label>
              <Input
                type="number"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                placeholder="0"
                className="bg-neutral-800 border-neutral-700 text-white mt-1"
                min="1"
                step="1"
              />
            </div>
            <div>
              <Label className="text-neutral-400 text-sm">开仓价格</Label>
              <Input
                type="number"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="0.00"
                className="bg-neutral-800 border-neutral-700 text-white mt-1"
                step="0.01"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-neutral-400 text-sm">止损价</Label>
              <Input
                type="number"
                value={stopLoss}
                onChange={(e) => setStopLoss(e.target.value)}
                placeholder="0.00"
                className="bg-neutral-800 border-neutral-700 text-white mt-1"
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
                className="bg-neutral-800 border-neutral-700 text-white mt-1"
                step="0.01"
              />
            </div>
          </div>

          {symbol && quantity && price && (
            <div className="bg-neutral-800/50 rounded-lg p-3 space-y-1 text-sm">
              <div className="flex justify-between text-neutral-400">
                <span>预期保证金：</span>
                <span className="text-white">
                  ¥
                  {(parseFloat(price || "0") * parseInt(quantity || "0") * 100).toLocaleString(undefined, {
                    maximumFractionDigits: 0,
                  })}
                </span>
              </div>
              <div className="flex justify-between text-neutral-400">
                <span>最大风险：</span>
                <span className="text-red-400">
                  ¥
                  {Math.abs(
                    (parseFloat(stopLoss || "0") - parseFloat(price || "0")) * parseInt(quantity || "0") * 100
                  ).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </span>
              </div>
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={!symbol || !quantity || !price || !stopLoss || !takeProfit}
            className={cn(
              direction === "long"
                ? "bg-red-600 hover:bg-red-700 disabled:opacity-50"
                : "bg-green-600 hover:bg-green-700 disabled:opacity-50"
            )}
          >
            {direction === "long" ? "做多开仓" : "做空开仓"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
