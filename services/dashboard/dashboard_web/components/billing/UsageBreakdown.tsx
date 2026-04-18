"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { billingApi, type BillingRecord } from "@/lib/api/billing"

export function UsageBreakdown() {
  const [data, setData] = useState<BillingRecord[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await billingApi.getRecords(100)
        setData(res.records || [])
      } catch (err) {
        console.error("Failed to fetch records:", err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>用量详情</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-muted-foreground">加载中...</div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>用量详情（最近 100 次调用）</CardTitle>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <div className="text-muted-foreground">暂无数据</div>
        ) : (
          <div className="max-h-[600px] overflow-y-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>时间</TableHead>
                  <TableHead>模型</TableHead>
                  <TableHead>组件</TableHead>
                  <TableHead>层级</TableHead>
                  <TableHead className="text-right">输入 Token</TableHead>
                  <TableHead className="text-right">输出 Token</TableHead>
                  <TableHead className="text-right">成本</TableHead>
                  <TableHead>本地</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((record, idx) => (
                  <TableRow key={idx}>
                    <TableCell className="font-mono text-xs">
                      {new Date(record.timestamp).toLocaleString("zh-CN")}
                    </TableCell>
                    <TableCell className="font-medium">{record.model}</TableCell>
                    <TableCell>{record.component}</TableCell>
                    <TableCell>
                      <Badge variant={record.tier === "主力" ? "default" : "secondary"}>
                        {record.tier}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">{record.input_tokens.toLocaleString()}</TableCell>
                    <TableCell className="text-right">{record.output_tokens.toLocaleString()}</TableCell>
                    <TableCell className="text-right">¥{record.total_cost.toFixed(4)}</TableCell>
                    <TableCell>
                      {record.is_local ? (
                        <Badge variant="outline">本地</Badge>
                      ) : (
                        <Badge>在线</Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
