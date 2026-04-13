"use client"

import { useState } from "react"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from "recharts"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { TrendingUp } from "lucide-react"

interface TimeframeData {
  timeframe: string
  label: string
  equityCurve: any[]
}

interface EquityCurveChartProps {
  equityCurve: any[]
  title?: string
  multiTimeframeData?: TimeframeData[]
}

export function EquityCurveChart({ equityCurve, title = "权益曲线", multiTimeframeData }: EquityCurveChartProps) {
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>(
    multiTimeframeData?.[0]?.timeframe || "default"
  )
  const [comparisonMode, setComparisonMode] = useState(false)

  // 获取当前选中的数据
  const currentData = multiTimeframeData
    ? multiTimeframeData.find((d) => d.timeframe === selectedTimeframe)?.equityCurve || equityCurve
    : equityCurve
  // 计算回撤曲线
  const calculateDrawdown = (data: any[]) => {
    return data.map((point, index) => {
      const equity = point.equity || point.value || 0
      const peak = data.slice(0, index + 1).reduce((max, p) => Math.max(max, p.equity || p.value || 0), 0)
      const drawdown = peak > 0 ? ((peak - equity) / peak) * 100 : 0

      return {
        date: point.date || point.timestamp,
        equity,
        drawdown: -drawdown,
        underwater: -drawdown,
      }
    })
  }

  const dataWithDrawdown = calculateDrawdown(currentData)

  // 多时间框架对比数据
  const comparisonData = multiTimeframeData
    ? multiTimeframeData.map((tf) => {
        const data = calculateDrawdown(tf.equityCurve)
        return {
          timeframe: tf.timeframe,
          label: tf.label,
          data,
          finalEquity: data[data.length - 1]?.equity || 0,
          maxDrawdown: Math.min(...data.map((d) => d.drawdown)),
        }
      })
    : []

  return (
    <Card className="bg-neutral-800 border-neutral-700">
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle className="text-white flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-orange-500" />
            {title}
          </CardTitle>
          <div className="flex gap-2">
            {multiTimeframeData && multiTimeframeData.length > 1 && (
              <>
                <Select value={selectedTimeframe} onValueChange={setSelectedTimeframe}>
                  <SelectTrigger className="w-32 bg-neutral-700 border-neutral-600 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {multiTimeframeData.map((tf) => (
                      <SelectItem key={tf.timeframe} value={tf.timeframe}>
                        {tf.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  size="sm"
                  variant={comparisonMode ? "default" : "outline"}
                  onClick={() => setComparisonMode(!comparisonMode)}
                  className="text-white"
                >
                  对比模式
                </Button>
              </>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {comparisonMode && multiTimeframeData ? (
          // 对比模式
          <div className="space-y-6">
            {/* 多时间框架权益曲线对比 */}
            <div>
              <h3 className="text-sm text-neutral-400 mb-2">多时间框架权益曲线对比</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="date" stroke="#9CA3AF" tick={{ fill: "#9CA3AF" }} />
                  <YAxis stroke="#9CA3AF" tick={{ fill: "#9CA3AF" }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#1F2937", border: "1px solid #374151" }}
                    labelStyle={{ color: "#F3F4F6" }}
                  />
                  <Legend />
                  {comparisonData.map((tf, index) => {
                    const colors = ["#10B981", "#3B82F6", "#F59E0B", "#EF4444", "#8B5CF6"]
                    return (
                      <Line
                        key={tf.timeframe}
                        data={tf.data}
                        type="monotone"
                        dataKey="equity"
                        stroke={colors[index % colors.length]}
                        name={tf.label}
                        dot={false}
                      />
                    )
                  })}
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* 对比统计 */}
            <div>
              <h3 className="text-sm text-neutral-400 mb-2">时间框架对比统计</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {comparisonData.map((tf) => (
                  <div key={tf.timeframe} className="bg-neutral-700 rounded-lg p-3 space-y-1">
                    <div className="text-xs text-neutral-400">{tf.label}</div>
                    <div className="text-lg font-bold text-white">
                      ¥{tf.finalEquity.toLocaleString()}
                    </div>
                    <div className="text-xs text-red-400">
                      最大回撤: {tf.maxDrawdown.toFixed(2)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          // 单一时间框架模式
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
        )}
      </CardContent>
    </Card>
  )
}
