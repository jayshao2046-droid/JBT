"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface OrderFlowProps {
  orders: Array<{
    instrument_id: string
    direction: string
    volume: number
    price: number
    status: string
    insert_time?: string
  }>
}

export function OrderFlow({ orders }: OrderFlowProps) {
  const statusMap: Record<string, { label: string; variant: "default" | "secondary" | "destructive" }> = {
    filled: { label: "已成交", variant: "default" },
    pending: { label: "待成交", variant: "secondary" },
    rejected: { label: "已拒绝", variant: "destructive" },
    cancelled: { label: "已撤单", variant: "secondary" },
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>订单流 ({orders.length})</CardTitle>
      </CardHeader>
      <CardContent>
        {orders.length === 0 ? (
          <p className="text-muted-foreground text-sm">暂无订单</p>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {orders.map((order, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 border rounded text-sm">
                <div>
                  <p className="font-medium">{order.instrument_id}</p>
                  <p className="text-xs text-muted-foreground">
                    {order.direction} {order.volume}手 @ ¥{order.price}
                  </p>
                </div>
                <div className="text-right">
                  <Badge variant={statusMap[order.status]?.variant || "secondary"}>
                    {statusMap[order.status]?.label || order.status}
                  </Badge>
                  {order.insert_time && (
                    <p className="text-xs text-muted-foreground mt-1">{order.insert_time}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
