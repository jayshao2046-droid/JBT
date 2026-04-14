"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { useState } from "react"

// 后端路由: POST /api/v1/import/dashboard (接收 yaml_content)
// 代理: /api/decision/api/v1/import/dashboard → http://8104/api/v1/import/dashboard
const IMPORT_URL = "/api/decision/api/v1/import/dashboard"

interface ImportResultResponse {
  import_id: string
  channel: string
  status: string
  created_at: string
  strategy_ids: string[]
  errors: string[]
  raw_yaml_count: number
}

export function StrategyImport() {
  const [yamlContent, setYamlContent] = useState("")
  const [importing, setImporting] = useState(false)
  const [result, setResult] = useState<ImportResultResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleImport = async () => {
    if (!yamlContent.trim()) return
    try {
      setImporting(true)
      setResult(null)
      setError(null)

      const res = await fetch(IMPORT_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ yaml_content: yamlContent }),
      })

      if (!res.ok) {
        throw new Error(`导入失败: HTTP ${res.status}`)
      }

      const data: ImportResultResponse = await res.json()
      setResult(data)
      if (data.status === "success") {
        setYamlContent("")
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "未知错误")
    } finally {
      setImporting(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>YAML 策略导入</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="yaml-content">YAML 策略内容</Label>
          <Textarea
            id="yaml-content"
            value={yamlContent}
            onChange={(e) => setYamlContent(e.target.value)}
            placeholder={"strategy_id: strategy_001\nstrategy_name: 动量策略\ntemplate_id: momentum_v1\n..."}
            rows={10}
            className="font-mono text-xs"
          />
          <p className="text-xs text-muted-foreground">
            支持 JBT 标准格式 YAML，每次导入可包含多个策略块。
          </p>
        </div>

        <Button onClick={handleImport} disabled={importing || !yamlContent.trim()}>
          {importing ? "导入中..." : "导入策略"}
        </Button>

        {result && (
          <div className="text-sm space-y-1">
            <div className={`font-medium ${result.status === "success" ? "text-green-600" : "text-yellow-600"}`}>
              {result.status === "success" ? "✅ 导入成功" : `⚠️ 导入状态: ${result.status}`}
            </div>
            {result.strategy_ids.length > 0 && (
              <div className="text-muted-foreground">
                已导入策略: {result.strategy_ids.join(", ")}
              </div>
            )}
            {result.errors.length > 0 && (
              <div className="text-red-600">
                错误: {result.errors.join("; ")}
              </div>
            )}
            <div className="text-muted-foreground text-xs">
              共解析 {result.raw_yaml_count} 个 YAML 块，导入 ID: {result.import_id}
            </div>
          </div>
        )}

        {error && (
          <div className="text-sm text-red-600">❌ {error}</div>
        )}
      </CardContent>
    </Card>
  )
}
