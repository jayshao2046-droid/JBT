"use client"

import { useState, useMemo } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Download, Search, Filter } from "lucide-react"
import { toast } from "sonner"

interface Order {
  order_ref: string
  instrument_id: string
  direction: string
  offset: string
  price: number
  volume: number
  status: string
  timestamp: string
  filled_volume?: number
}

interface OrderFlowEnhancedProps {
  orders: Order[]
}

export function OrderFlowEnhanced({ orders }: OrderFlowEnhancedProps) {
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [directionFilter, setDirectionFilter] = useState<string>("all")

  // 筛选订单
  const filteredOrders = useMemo(() => {
    return orders.filter(order => {
      // 搜索过滤
      if (searchTerm) {
        const term = searchTerm.toLowerCase()
        if (
          !order.order_ref?.toLowerCase().includes(term) &&
          !order.instrument_id?.toLowerCase().includes(term)
        ) {
          return false
        }
      }

      // 状态过滤
      if (statusFilter !== "all" && order.status !== statusFilter) {
        return false
      }

      // 方向过滤
      if (directionFilter !== "all" && order.direction !== directionFilter) {
        return false
      }

      return true
    })
  }, [orders, searchTerm, statusFilter, directionFilter])

  // 订单统计
  const stats = useMemo(() => {
    const total = orders.length
    const filled = orders.filter(o => o.status === "filled").length
    const cancelled = orders.filter(o => o.status === "cancelled").length
    const rejected = orders.filter(o => o.status === "rejected" || o.status === "error").length

    return {
      total,
      filled,
      cancelled,
      rejected,
      fillRate: total > 0 ? ((filled / total) * 100).toFixed(1) : "0.0",
      cancelRate: total > 0 ? ((cancelled / total) * 100).toFixed(1) : "0.0",
      rejectRate: total > 0 ? ((rejected / total) * 100).toFixed(1) : "0.0",
    }
  }, [orders])

  // 导出为 CSV
  const exportToCSV = () => {
    if (filteredOrders.length === 0) {
      toast.error("没有可导出的订单")
      return
    }

    const headers = ["订单号", "合约", "方向", "开平", "价格", "手数", "状态", "时间"]
    const rows = filteredOrders.map(order => [
      order.order_ref || "",
      order.instrument_id || "",
      order.direction || "",
      order.offset || "",
      order.price?.toString() || "",
      order.volume?.toString() || "",
      order.status || "",
      order.timestamp || "",
    ])

    const csvContent = [
      headers.join(","),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(",")),
    ].join("\n")

    const blob = new Blob(["\ufeff" + csvContent], { type: "text/csv;charset=utf-8;" })
    const link = document.createElement("a")
    const url = URL.createObjectURL(blob)
    link.setAttribute("href", url)
    link.setAttribute("download", `orders_${new Date().toISOString().slice(0, 10)}.csv`)
    link.style.visibility = "hidden"
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    toast.success(`已导出 ${filteredOrders.length} 条订单`)
  }

  // 状态徽章颜色
  const getStatusBadge = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      filled: "default",
      pending: "secondary",
      cancelled: "outline",
      rejected: "destructive",
      error: "destructive",
    }
    return <Badge variant={variants[status] || "secondary"}>{status}</Badge>
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>订单流</CardTitle>
          <Button size="sm" variant="outline" onClick={exportToCSV}>
            <Download className="h-4 w-4 mr-2" />
            导出 CSV
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* 订单统计 */}
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold">{stats.total}</div>
            <div className="text-xs text-muted-foreground">总订单数</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{stats.fillRate}%</div>
            <div className="text-xs text-muted-foreground">成交率</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">{stats.cancelRate}%</div>
            <div className="text-xs text-muted-foreground">撤单率</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{stats.rejectRate}%</div>
            <div className="text-xs text-muted-foreground">拒绝率</div>
          </div>
        </div>

        {/* 筛选器 */}
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="搜索订单号或合约代码..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="pl-8"
            />
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="状态" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部状态</SelectItem>
              <SelectItem value="filled">已成交</SelectItem>
              <SelectItem value="pending">待成交</SelectItem>
              <SelectItem value="cancelled">已撤单</SelectItem>
              <SelectItem value="rejected">已拒绝</SelectItem>
            </SelectContent>
          </Select>
          <Select value={directionFilter} onValueChange={setDirectionFilter}>
            <SelectTrigger className="w-[120px]">
              <SelectValue placeholder="方向" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部方向</SelectItem>
              <SelectItem value="buy">买入</SelectItem>
              <SelectItem value="sell">卖出</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* 订单表格 */}
        <div className="border rounded-md">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>订单号</TableHead>
                <TableHead>合约</TableHead>
                <TableHead>方向</TableHead>
                <TableHead>开平</TableHead>
                <TableHead className="text-right">价格</TableHead>
                <TableHead className="text-right">手数</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>时间</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredOrders.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center text-muted-foreground">
                    {orders.length === 0 ? "暂无订单" : "没有符合条件的订单"}
                  </TableCell>
                </TableRow>
              ) : (
                filteredOrders.slice(0, 50).map((order, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-mono text-xs">{order.order_ref || "-"}</TableCell>
                    <TableCell className="font-medium">{order.instrument_id}</TableCell>
                    <TableCell>
                      <Badge variant={order.direction === "buy" ? "default" : "secondary"}>
                        {order.direction === "buy" ? "买" : "卖"}
                      </Badge>
                    </TableCell>
                    <TableCell>{order.offset === "open" ? "开" : "平"}</TableCell>
                    <TableCell className="text-right">{order.price?.toFixed(2) || "-"}</TableCell>
                    <TableCell className="text-right">{order.volume}</TableCell>
                    <TableCell>{getStatusBadge(order.status)}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {order.timestamp ? new Date(order.timestamp).toLocaleTimeString() : "-"}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {filteredOrders.length > 50 && (
          <div className="text-sm text-muted-foreground text-center">
            显示前 50 条，共 {filteredOrders.length} 条订单
          </div>
        )}
      </CardContent>
    </Card>
  )
}
