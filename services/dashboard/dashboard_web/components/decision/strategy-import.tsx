"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { useState } from "react"

export function StrategyImport() {
  const [strategyId, setStrategyId] = useState("")
  const [strategyName, setStrategyName] = useState("")
  const [templateId, setTemplateId] = useState("")
  const [factorIds, setFactorIds] = useState("")
  const [importing, setImporting] = useState(false)
  const [result, setResult] = useState<string | null>(null)

  const handleImport = async () => {
    try {
      setImporting(true)
      setResult(null)

      const res = await fetch("/api/decision/api/v1/strategy/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          strategy_id: strategyId,
          strategy_name: strategyName,
          template_id: templateId,
          factor_ids: factorIds.split(",").map((s) => s.trim()).filter(Boolean),
        }),
      })

      if (!res.ok) {
        throw new Error(`Import failed: ${res.status}`)
      }

      const data = await res.json()
      setResult(`导入成功: ${data.strategy_id}`)
      setStrategyId("")
      setStrategyName("")
      setTemplateId("")
      setFactorIds("")
    } catch (err) {
      setResult(`导入失败: ${err instanceof Error ? err.message : "Unknown error"}`)
    } finally {
      setImporting(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>策略导入</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="strategy-id">策略ID</Label>
          <Input
            id="strategy-id"
            value={strategyId}
            onChange={(e) => setStrategyId(e.target.value)}
            placeholder="例如: strategy_001"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="strategy-name">策略名称</Label>
          <Input
            id="strategy-name"
            value={strategyName}
            onChange={(e) => setStrategyName(e.target.value)}
            placeholder="例如: 动量策略"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="template-id">模板ID</Label>
          <Input
            id="template-id"
            value={templateId}
            onChange={(e) => setTemplateId(e.target.value)}
            placeholder="例如: momentum_v1"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="factor-ids">因子列表（逗号分隔）</Label>
          <Textarea
            id="factor-ids"
            value={factorIds}
            onChange={(e) => setFactorIds(e.target.value)}
            placeholder="例如: factor_1, factor_2, factor_3"
            rows={3}
          />
        </div>

        <Button onClick={handleImport} disabled={importing || !strategyId || !strategyName}>
          {importing ? "导入中..." : "导入策略"}
        </Button>

        {result && (
          <div className={`text-sm ${result.includes("成功") ? "text-green-600" : "text-red-600"}`}>
            {result}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
