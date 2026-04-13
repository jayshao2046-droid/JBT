"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { FileText, Save, Upload, Download } from "lucide-react"

interface Template {
  name: string
  strategy_id: string
  params: Record<string, any>
  description: string
}

const PRESET_TEMPLATES: Template[] = [
  {
    name: "趋势跟踪",
    strategy_id: "trend_following",
    params: { stop_loss: 0.03, take_profit: 0.08, timeframe: 60 },
    description: "适用于趋势明显的市场环境",
  },
  {
    name: "均值回归",
    strategy_id: "mean_reversion",
    params: { stop_loss: 0.02, take_profit: 0.05, timeframe: 30 },
    description: "适用于震荡市场",
  },
  {
    name: "套利策略",
    strategy_id: "arbitrage",
    params: { stop_loss: 0.01, take_profit: 0.03, timeframe: 15 },
    description: "低风险套利机会",
  },
]

export function DecisionTemplates() {
  const [customTemplates, setCustomTemplates] = useState<Template[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null)

  const handleSaveCustom = () => {
    if (!selectedTemplate) return

    const newTemplate: Template = {
      name: `自定义模板 ${customTemplates.length + 1}`,
      strategy_id: selectedTemplate.strategy_id,
      params: { ...selectedTemplate.params },
      description: "用户自定义模板",
    }

    setCustomTemplates([...customTemplates, newTemplate])
  }

  const handleExport = () => {
    const data = JSON.stringify(customTemplates, null, 2)
    const blob = new Blob([data], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "decision_templates.json"
    a.click()
  }

  const handleImport = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const templates = JSON.parse(e.target?.result as string)
        setCustomTemplates(templates)
      } catch (error) {
        console.error("Failed to import templates:", error)
      }
    }
    reader.readAsText(file)
  }

  return (
    <Card className="bg-neutral-800 border-neutral-700">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <FileText className="w-5 h-5 text-yellow-500" />
          决策模板
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* 预设模板 */}
          <div>
            <h3 className="text-sm font-medium text-white mb-2">预设模板</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
              {PRESET_TEMPLATES.map((template, index) => (
                <button
                  key={index}
                  onClick={() => setSelectedTemplate(template)}
                  className={`p-3 rounded-lg border text-left transition-colors ${
                    selectedTemplate?.name === template.name
                      ? "border-orange-500 bg-orange-500/10"
                      : "border-neutral-700 bg-neutral-900 hover:border-neutral-600"
                  }`}
                >
                  <div className="text-sm font-medium text-white mb-1">{template.name}</div>
                  <div className="text-xs text-neutral-400">{template.description}</div>
                </button>
              ))}
            </div>
          </div>

          {/* 自定义模板 */}
          {customTemplates.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-white mb-2">自定义模板</h3>
              <div className="space-y-2">
                {customTemplates.map((template, index) => (
                  <div key={index} className="p-3 bg-neutral-900 rounded-lg border border-neutral-700">
                    <div className="text-sm font-medium text-white">{template.name}</div>
                    <div className="text-xs text-neutral-400 mt-1">{template.strategy_id}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 操作按钮 */}
          <div className="flex gap-2">
            <Button size="sm" onClick={handleSaveCustom} disabled={!selectedTemplate}>
              <Save className="w-4 h-4 mr-2" />
              保存为自定义
            </Button>
            <Button size="sm" variant="outline" onClick={handleExport} disabled={customTemplates.length === 0}>
              <Download className="w-4 h-4 mr-2" />
              导出
            </Button>
            <Button size="sm" variant="outline" onClick={() => document.getElementById("import-input")?.click()}>
              <Upload className="w-4 h-4 mr-2" />
              导入
            </Button>
            <input id="import-input" type="file" accept=".json" onChange={handleImport} className="hidden" />
          </div>

          {/* 选中模板详情 */}
          {selectedTemplate && (
            <div className="p-4 bg-neutral-900 rounded-lg border border-neutral-700">
              <h4 className="text-sm font-medium text-white mb-2">当前选中：{selectedTemplate.name}</h4>
              <pre className="text-xs text-neutral-300 font-mono overflow-x-auto">
                {JSON.stringify(selectedTemplate.params, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
