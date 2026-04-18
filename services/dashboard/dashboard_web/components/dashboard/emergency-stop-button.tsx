"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { simTradingApi } from "@/lib/api/sim-trading"
import { useRiskControl } from "@/hooks/use-risk-control"
import { AlertTriangle, Play } from "lucide-react"

export function EmergencyStopButton() {
  const { l1Status, refetch } = useRiskControl()
  const [showDialog, setShowDialog] = useState(false)
  const [loading, setLoading] = useState(false)

  const tradingEnabled = l1Status?.trading_enabled ?? true

  const handleConfirm = async () => {
    setLoading(true)
    try {
      if (tradingEnabled) {
        await simTradingApi.pauseTrading("用户手动暂停")
      } else {
        await simTradingApi.resumeTrading()
      }
      refetch()
    } catch (err) {
      console.error("Failed to toggle trading:", err)
      alert(`操作失败: ${err}`)
    } finally {
      setLoading(false)
      setShowDialog(false)
    }
  }

  return (
    <>
      <Button
        variant={tradingEnabled ? "destructive" : "default"}
        size="sm"
        onClick={() => setShowDialog(true)}
        disabled={loading}
      >
        {tradingEnabled ? (
          <>
            <AlertTriangle className="mr-2 h-4 w-4" />
            紧急暂停
          </>
        ) : (
          <>
            <Play className="mr-2 h-4 w-4" />
            恢复交易
          </>
        )}
      </Button>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {tradingEnabled ? "确认暂停交易？" : "确认恢复交易？"}
            </DialogTitle>
            <DialogDescription>
              {tradingEnabled
                ? "暂停后系统将停止所有新订单提交，现有持仓不受影响。"
                : "恢复后系统将重新开始接受交易信号。"}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>
              取消
            </Button>
            <Button onClick={handleConfirm} disabled={loading}>
              {loading ? "处理中..." : "确认"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
