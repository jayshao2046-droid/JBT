"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts"

interface ParamConfig {
  name: string
  min: number
  max: number
  step?: number
  values?: number[]
}

interface OptimizationResult {
  params: Record<string, number>
  score: number
  generation?: number
}

interface ParameterOptimizerProps {
  strategyName: string
  onOptimize: (algorithm: string, config: any) => Promise<OptimizationResult[]>
}

export function ParameterOptimizer({ strategyName, onOptimize }: ParameterOptimizerProps) {
  const [algorithm, setAlgorithm] = useState<string>("grid_search")
  const [params, setParams] = useState<ParamConfig[]>([
    { name: "param1", min: 0, max: 100, step: 10 },
  ])
  const [results, setResults] = useState<OptimizationResult[]>([])
  const [isOptimizing, setIsOptimizing] = useState(false)
  const [bestResult, setBestResult] = useState<OptimizationResult | null>(null)

  // 算法特定配置
  const [gridMaxIterations, setGridMaxIterations] = useState(100)
  const [gaPopulationSize, setGaPopulationSize] = useState(20)
  const [gaGenerations, setGaGenerations] = useState(10)
  const [bayesianIterations, setBayesianIterations] = useState(20)

  const addParameter = () => {
    setParams([...params, { name: `param${params.length + 1}`, min: 0, max: 100, step: 10 }])
  }

  const removeParameter = (index: number) => {
    setParams(params.filter((_, i) => i !== index))
  }

  const updateParameter = (index: number, field: keyof ParamConfig, value: any) => {
    const newParams = [...params]
    newParams[index] = { ...newParams[index], [field]: value }
    setParams(newParams)
  }

  const handleOptimize = async () => {
    setIsOptimizing(true)
    setResults([])
    setBestResult(null)

    try {
      const config: any = {
        params: params.reduce((acc, p) => {
          if (algorithm === "grid_search") {
            // 生成网格值
            const values = []
            for (let v = p.min; v <= p.max; v += p.step || 1) {
              values.push(v)
            }
            acc[p.name] = values
          } else {
            // 遗传算法和贝叶斯优化使用范围
            acc[p.name] = [p.min, p.max]
          }
          return acc
        }, {} as Record<string, any>),
      }

      if (algorithm === "grid_search") {
        config.max_iterations = gridMaxIterations
      } else if (algorithm === "genetic_algorithm") {
        config.population_size = gaPopulationSize
        config.generations = gaGenerations
      } else if (algorithm === "bayesian_optimization") {
        config.n_iterations = bayesianIterations
      }

      const optimizationResults = await onOptimize(algorithm, config)
      setResults(optimizationResults)

      // 找到最佳结果
      const best = optimizationResults.reduce((prev, current) =>
        current.score > prev.score ? current : prev
      )
      setBestResult(best)
    } catch (error) {
      console.error("Optimization failed:", error)
    } finally {
      setIsOptimizing(false)
    }
  }

  // 准备散点图数据（仅显示前两个参数）
  const scatterData = results.map(r => ({
    x: r.params[params[0]?.name] || 0,
    y: r.params[params[1]?.name] || 0,
    score: r.score,
  }))

  const maxScore = Math.max(...results.map(r => r.score), 0)
  const minScore = Math.min(...results.map(r => r.score), 0)

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>策略参数优化器 - {strategyName}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 算法选择 */}
          <div className="space-y-2">
            <Label>优化算法</Label>
            <Select value={algorithm} onValueChange={setAlgorithm}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="grid_search">网格搜索（Grid Search）</SelectItem>
                <SelectItem value="genetic_algorithm">遗传算法（Genetic Algorithm）</SelectItem>
                <SelectItem value="bayesian_optimization">贝叶斯优化（Bayesian Optimization）</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* 算法特定配置 */}
          {algorithm === "grid_search" && (
            <div className="space-y-2">
              <Label>最大迭代次数</Label>
              <Input
                type="number"
                value={gridMaxIterations}
                onChange={(e) => setGridMaxIterations(Number(e.target.value))}
              />
            </div>
          )}

          {algorithm === "genetic_algorithm" && (
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>种群大小</Label>
                <Input
                  type="number"
                  value={gaPopulationSize}
                  onChange={(e) => setGaPopulationSize(Number(e.target.value))}
                />
              </div>
              <div className="space-y-2">
                <Label>迭代代数</Label>
                <Input
                  type="number"
                  value={gaGenerations}
                  onChange={(e) => setGaGenerations(Number(e.target.value))}
                />
              </div>
            </div>
          )}

          {algorithm === "bayesian_optimization" && (
            <div className="space-y-2">
              <Label>迭代次数</Label>
              <Input
                type="number"
                value={bayesianIterations}
                onChange={(e) => setBayesianIterations(Number(e.target.value))}
              />
            </div>
          )}

          {/* 参数配置 */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <Label>参数配置</Label>
              <Button size="sm" variant="outline" onClick={addParameter}>
                + 添加参数
              </Button>
            </div>

            {params.map((param, index) => (
              <div key={index} className="grid grid-cols-5 gap-2 items-end">
                <div className="space-y-1">
                  <Label className="text-xs">参数名</Label>
                  <Input
                    value={param.name}
                    onChange={(e) => updateParameter(index, "name", e.target.value)}
                    placeholder="参数名"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">最小值</Label>
                  <Input
                    type="number"
                    value={param.min}
                    onChange={(e) => updateParameter(index, "min", Number(e.target.value))}
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">最大值</Label>
                  <Input
                    type="number"
                    value={param.max}
                    onChange={(e) => updateParameter(index, "max", Number(e.target.value))}
                  />
                </div>
                {algorithm === "grid_search" && (
                  <div className="space-y-1">
                    <Label className="text-xs">步长</Label>
                    <Input
                      type="number"
                      value={param.step || 1}
                      onChange={(e) => updateParameter(index, "step", Number(e.target.value))}
                    />
                  </div>
                )}
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() => removeParameter(index)}
                  disabled={params.length === 1}
                >
                  删除
                </Button>
              </div>
            ))}
          </div>

          <Button onClick={handleOptimize} disabled={isOptimizing || params.length === 0} className="w-full">
            {isOptimizing ? "优化中..." : "开始优化"}
          </Button>
        </CardContent>
      </Card>

      {/* 优化结果 */}
      {results.length > 0 && (
        <>
          {/* 最佳结果 */}
          {bestResult && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">最佳结果</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">评分</span>
                    <span className="font-medium text-green-600">{bestResult.score.toFixed(4)}</span>
                  </div>
                  {Object.entries(bestResult.params).map(([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span className="text-sm text-muted-foreground">{key}</span>
                      <span className="font-medium">{typeof value === 'number' ? value.toFixed(2) : value}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* 参数空间可视化 */}
          {params.length >= 2 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">参数空间探索</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <ScatterChart>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="x" name={params[0]?.name} />
                    <YAxis dataKey="y" name={params[1]?.name} />
                    <Tooltip
                      formatter={(value: any, name: string) => {
                        if (name === "score") return [value.toFixed(4), "评分"]
                        return [value.toFixed(2), name]
                      }}
                    />
                    <Scatter data={scatterData} fill="#8884d8">
                      {scatterData.map((entry, index) => {
                        const intensity = (entry.score - minScore) / (maxScore - minScore || 1)
                        const color = `hsl(${intensity * 120}, 70%, 50%)`
                        return <Cell key={`cell-${index}`} fill={color} />
                      })}
                    </Scatter>
                  </ScatterChart>
                </ResponsiveContainer>
                <p className="text-xs text-muted-foreground mt-2 text-center">
                  颜色表示评分：红色（低）→ 黄色（中）→ 绿色（高）
                </p>
              </CardContent>
            </Card>
          )}

          {/* 结果统计 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">优化统计</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">总迭代次数</span>
                  <span className="font-medium">{results.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">最高评分</span>
                  <span className="font-medium text-green-600">{maxScore.toFixed(4)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">最低评分</span>
                  <span className="font-medium text-red-600">{minScore.toFixed(4)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">平均评分</span>
                  <span className="font-medium">
                    {(results.reduce((sum, r) => sum + r.score, 0) / results.length).toFixed(4)}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
