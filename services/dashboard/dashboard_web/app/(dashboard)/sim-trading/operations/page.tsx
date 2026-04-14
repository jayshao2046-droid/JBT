"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useSimTrading } from "@/hooks/use-sim-trading"
import { simTradingApi } from "@/lib/api/sim-trading"
import { useToast } from "@/hooks/use-toast"
import { ALL_CONTRACTS } from "@/lib/contracts"
import { Skeleton } from "@/components/ui/skeleton"

export default function OperationsPage() {
  const { account, positions, orders, loading, refetch } = useSimTrading()
  const { toast } = useToast()
  const [orderForm, setOrderForm] = useState({
    instrument_id: "",
    direction: "long" as "long" | "short",
    volume: 1,
    price: 0,
    order_type: "limit" as "limit" | "market",
  })

  const handlePlaceOrder = async () => {
    try {
      await simTradingApi.placeOrder(orderForm)
      toast({ title: "下单成功", description: `${orderForm.instrument_id} ${orderForm.direction} ${orderForm.volume}手` })
      refetch()
      setOrderForm({ ...orderForm, instrument_id: "", volume: 1, price: 0 })
    } catch (err) {
      toast({ title: "下单失败", description: err instanceof Error ? err.message : "未知错误", variant: "destructive" })
    }
  }

  const handleCancelOrder = async (orderRef: string) => {
    try {
      await simTradingApi.cancelOrder(orderRef)
      toast({ title: "撤单成功" })
      refetch()
    } catch (err) {
      toast({ title: "撤单失败", description: err instanceof Error ? err.message : "未知错误", variant: "destructive" })
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-96" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 账户信息 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">账户权益</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">¥{account?.equity.toLocaleString() || 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">可用资金</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">¥{account?.available.toLocaleString() || 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">保证金</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">¥{account?.margin.toLocaleString() || 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">浮动盈亏</CardTitle>
          </CardHeader>
          <CardContent>
            <p className={`text-2xl font-bold ${(account?.float_pnl || 0) >= 0 ? "text-green-500" : "text-red-500"}`}>
              {(account?.float_pnl || 0) >= 0 ? "+" : ""}¥{account?.float_pnl.toLocaleString() || 0}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 下单面板 */}
        <Card>
          <CardHeader>
            <CardTitle>下单</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>合约</Label>
              <Select value={orderForm.instrument_id} onValueChange={(v) => setOrderForm({ ...orderForm, instrument_id: v })}>
                <SelectTrigger>
                  <SelectValue placeholder="选择合约" />
                </SelectTrigger>
                <SelectContent>
                  {ALL_CONTRACTS.slice(0, 20).map((c) => (
                    <SelectItem key={c.symbol} value={c.symbol}>
                      {c.name} ({c.symbol})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>方向</Label>
              <Select value={orderForm.direction} onValueChange={(v: "long" | "short") => setOrderForm({ ...orderForm, direction: v })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="long">做多</SelectItem>
                  <SelectItem value="short">做空</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>手数</Label>
              <Input
                type="number"
                value={orderForm.volume}
                onChange={(e) => setOrderForm({ ...orderForm, volume: parseInt(e.target.value) || 1 })}
              />
            </div>
            <div>
              <Label>价格</Label>
              <Input
                type="number"
                value={orderForm.price}
                onChange={(e) => setOrderForm({ ...orderForm, price: parseFloat(e.target.value) || 0 })}
              />
            </div>
            <div>
              <Label>类型</Label>
              <Select value={orderForm.order_type} onValueChange={(v: "limit" | "market") => setOrderForm({ ...orderForm, order_type: v })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="limit">限价单</SelectItem>
                  <SelectItem value="market">市价单</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={handlePlaceOrder} className="w-full">
              提交订单
            </Button>
          </CardContent>
        </Card>

        {/* 持仓列表 */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>持仓 ({positions.length})</CardTitle>
          </CardHeader>
          <CardContent>
            {positions.length === 0 ? (
              <p className="text-muted-foreground text-sm">暂无持仓</p>
            ) : (
              <div className="space-y-2">
                {positions.map((pos, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 border rounded">
                    <div>
                      <p className="font-medium">{pos.instrument_id}</p>
                      <p className="text-xs text-muted-foreground">
                        {pos.direction === "long" ? "多" : "空"} {pos.volume}手 @ ¥{pos.avg_price}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className={`font-medium ${pos.float_pnl >= 0 ? "text-green-500" : "text-red-500"}`}>
                        {pos.float_pnl >= 0 ? "+" : ""}¥{pos.float_pnl.toFixed(2)}
                      </p>
                      <p className="text-xs text-muted-foreground">当前价: ¥{pos.current_price}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 订单列表 */}
      <Card>
        <CardHeader>
          <CardTitle>今日订单 ({orders.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {orders.length === 0 ? (
            <p className="text-muted-foreground text-sm">暂无订单</p>
          ) : (
            <div className="space-y-2">
              {orders.map((order, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 border rounded">
                  <div>
                    <p className="font-medium">{order.instrument_id}</p>
                    <p className="text-xs text-muted-foreground">
                      {order.direction} {order.volume}手 @ ¥{order.price} - {order.insert_time}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs px-2 py-1 rounded ${
                        order.status === "filled"
                          ? "bg-green-500/10 text-green-500"
                          : order.status === "rejected"
                            ? "bg-red-500/10 text-red-500"
                            : "bg-yellow-500/10 text-yellow-500"
                      }`}
                    >
                      {order.status}
                    </span>
                    {order.status === "pending" && order.order_ref && (
                      <Button size="sm" variant="outline" onClick={() => handleCancelOrder(order.order_ref!)}>
                        撤单
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
