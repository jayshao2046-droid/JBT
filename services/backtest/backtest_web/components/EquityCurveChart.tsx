"use client"

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from "recharts"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { TrendingUp } from "lucide-react"

interface EquityCurveChartProps {
  equityCurve: any[]
  title?: string
}

export function EquityCurveChart({ equityCurve, title = "权益曲线" }: EquityCurveChartProps) {
  // 计算回撤曲线
  const dataWithDrawdown = equityCurve.map((point, index) => {
    const equity = point.equity || point.value || 0
    const peak = equityCurve.slice(0, index + 1).reduce((max, p) => Math.max(max, p.equity || p.value || 0), 0)
    const drawdown = peak > 0 ? ((peak - equity) / peak) * 100 : 0

    return {
      date: point.date || point.timestamp,
      equity,
      drawdown: -drawdown,
      underwater: -drawdown,
    }
  })

  return (
    <Card className="bg-neutral-800 border-neutral-700">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-orange-500" />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* 权益曲线 */}
          <div>
            <h3 className="text-sm text-neutral-400 mb-2">权益曲线</h3>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={dataWithDrawdown}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="date" stroke="#9CA3AF" tick={{ fill: "#9CA3AF" }} />
                <YAxis stroke="#9CA3AF" tick={{ fill: "#9CA3AF" }} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#1F2937", border: "1px solid #374151" }}
                  labelStyle={{ color: "#F3F4F6" }}
                />
                <Area type="monotone" dataKey="equity" stroke="#10B981" fill="#10B981" fillOpacity={0.3} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* 回撤曲线 */}
          <div>
            <h3 className="text-sm text-neutral-400 mb-2">回撤曲线</h3>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={dataWithDrawdown}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="date" stroke="#9CA3AF" tick={{ fill: "#9CA3AF" }} />
                <YAxis stroke="#9CA3AF" tick={{ fill: "#9CA3AF" }} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#1F2937", border: "1px solid #374151" }}
                  labelStyle={{ color: "#F3F4F6" }}
                />
                <Area type="monotone" dataKey="drawdown" stroke="#EF4444" fill="#EF4444" fillOpacity={0.3} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* 水下曲线 */}
          <div>
            <h3 className="text-sm text-neutral-400 mb-2">水下曲线（Underwater Curve）</h3>
            <ResponsiveContainer width="100%" height={150}>
              <AreaChart data={dataWithDrawdown}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="date" stroke="#9CA3AF" tick={{ fill: "#9CA3AF" }} />
                <YAxis stroke="#9CA3AF" tick={{ fill: "#9CA3AF" }} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#1F2937", border: "1px solid #374151" }}
                  labelStyle={{ color: "#F3F4F6" }}
                />
                <Area type="monotone" dataKey="underwater" stroke="#F59E0B" fill="#F59E0B" fillOpacity={0.3} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
