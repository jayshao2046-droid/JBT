"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ParamGrid } from "./param-grid"
import { Play, Settings2 } from "lucide-react"
import { toast } from "sonner"
import type { Strategy } from "@/lib/api/backtest"

interface ParameterOptimizerProps {
  strategies: Strategy[]
}

interface ParamRange {
  name: string
  min: number
  max: number
  step: number
}

export function ParameterOptimizer({ strategies }: ParameterOptimizerProps) {
  const [selectedStrategy, setSelectedStrategy] = useState<string>("")
  const [paramRanges, setParamRanges] = useState<ParamRange[]>([])
  const [optimizing, setOptimizing] = useState(false)
  const [results, setResults] = useState<Array<{ params: Record<string, number>; score: number }>>([])

  const handleStrategyChange = (strategyName: string) => {
    setSelectedStrategy(strategyName)
    const strategy = strategies.find(s => s.name === strategyName)
    if (strategy) {
      const ranges: ParamRange[] = Object.entries(strategy.params)
        .filter(([, value]) => typeof value === "number")
        .map(([key, value]) => ({
          name: key,
          min: (value as number) * 0.5,
          max: (value as number) * 1.5,
          step: (value as number) * 0.1,
        }))
      setParamRanges(ranges)
    }
  }

  const handleOptimize = async () => {
    if (!selectedStrategy) {
      toast.error("请选择策略")
      return
    }
    if (paramRanges.length === 0) {
      toast.error("请配置参数范围")
      return
    }

    setOptimizing(true)
    toast.info("开始参数优化...")

    // 模拟优化过程
    setTimeout(() => {
      const mockResults = Array.from({ length: 20 }, () => ({
        params: paramRanges.reduce((acc, range) => {
          acc[range.name] = range.min + Math.random() * (range.max - range.min)
          return acc
        }, {} as Record<string, number>),
        score: Math.random() * 100,
      })).sort((a, b) => b.score - a.score)

      setResults(mockResults)
      setOptimizing(false)
      toast.success("优化完成")
    }, 2000)
  }

  const updateParamRange = (index: number, field: keyof ParamRange, value: number) => {
    const newRanges = [...paramRanges]
    newRanges[index] = { ...newRanges[index], [field]: value }
    setParamRanges(newRanges)
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings2 className="w-5 h-5" />
            参数优化器
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>选择策略</Label>
            <Select value={selectedStrategy} onValueChange={handleStrategyChange}>
              <SelectTrigger>
                <SelectValue placeholder="选择要优化的策略" />
              </SelectTrigger>
              <SelectContent>
                {strategies.map((strategy) => (
                  <SelectItem key={strategy.id || strategy.name} value={strategy.name}>
                    {strategy.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {paramRanges.length > 0 && (
            <div className="space-y-3">
              <Label>参数范围配置</Label>
              {paramRanges.map((range, index) => (
                <div key={range.name} className="grid grid-cols-4 gap-3 p-3 border rounded">
                  <div>
                    <Label className="text-xs">{range.name}</Label>
                  </div>
                  <div>
                    <Input
                      type="number"
                      placeholder="最小值"
                      value={range.min}
                      onChange={(e) => updateParamRange(index, "min", parseFloat(e.target.value))}
                    />
                  </div>
                  <div>
                    <Input
                      type="number"
                      placeholder="最大值"
                      value={range.max}
                      onChange={(e) => updateParamRange(index, "max", parseFloat(e.target.value))}
                    />
                  </div>
                  <div>
                    <Input
                      type="number"
                      placeholder="步长"
                      value={range.step}
                      onChange={(e) => updateParamRange(index, "step", parseFloat(e.target.value))}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}

          <Button
            onClick={handleOptimize}
            disabled={optimizing || !selectedStrategy}
            className="w-full"
          >
            <Play className="w-4 h-4 mr-2" />
            {optimizing ? "优化中..." : "开始优化"}
          </Button>
        </CardContent>
      </Card>

      {results.length > 0 && <ParamGrid results={results} />}
    </div>
  )
}
