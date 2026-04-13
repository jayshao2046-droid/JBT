"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Download, Upload, Save, Trash2, Copy } from "lucide-react"

interface BacktestTemplate {
  id: string
  name: string
  description: string
  config: {
    start_date: string
    end_date: string
    initial_capital: number
    commission_rate: number
    slippage: number
    instruments?: string[]
    [key: string]: any
  }
  created_at: string
  is_preset?: boolean
}

interface BacktestTemplatesProps {
  templates: BacktestTemplate[]
  onSave: (template: Omit<BacktestTemplate, "id" | "created_at">) => Promise<void>
  onLoad: (template: BacktestTemplate) => void
  onDelete: (templateId: string) => Promise<void>
  onExport: (template: BacktestTemplate) => void
  onImport: (file: File) => Promise<void>
}

export function BacktestTemplates({
  templates,
  onSave,
  onLoad,
  onDelete,
  onExport,
  onImport,
}: BacktestTemplatesProps) {
  const [isCreating, setIsCreating] = useState(false)
  const [newTemplate, setNewTemplate] = useState({
    name: "",
    description: "",
    config: {
      start_date: "2023-01-01",
      end_date: "2023-12-31",
      initial_capital: 1000000,
      commission_rate: 0.0003,
      slippage: 1,
    },
  })

  const handleSave = async () => {
    if (!newTemplate.name.trim()) {
      alert("请输入模板名称")
      return
    }

    try {
      await onSave(newTemplate)
      setIsCreating(false)
      setNewTemplate({
        name: "",
        description: "",
        config: {
          start_date: "2023-01-01",
          end_date: "2023-12-31",
          initial_capital: 1000000,
          commission_rate: 0.0003,
          slippage: 1,
        },
      })
    } catch (error) {
      console.error("Failed to save template:", error)
    }
  }

  const handleImport = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      onImport(file)
    }
  }

  const handleDuplicate = (template: BacktestTemplate) => {
    setNewTemplate({
      name: `${template.name} (副本)`,
      description: template.description,
      config: { ...template.config },
    })
    setIsCreating(true)
  }

  const presetTemplates = templates.filter((t) => t.is_preset)
  const customTemplates = templates.filter((t) => !t.is_preset)

  return (
    <div className="space-y-4">
      {/* 操作栏 */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle className="text-base">回测模板管理</CardTitle>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={() => setIsCreating(true)}>
                <Save className="h-4 w-4 mr-1" />
                新建模板
              </Button>
              <Button size="sm" variant="outline" asChild>
                <label>
                  <Upload className="h-4 w-4 mr-1" />
                  导入模板
                  <input
                    type="file"
                    accept=".json"
                    className="hidden"
                    onChange={handleImport}
                  />
                </label>
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* 创建模板表单 */}
      {isCreating && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">创建新模板</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>模板名称</Label>
              <Input
                value={newTemplate.name}
                onChange={(e) => setNewTemplate({ ...newTemplate, name: e.target.value })}
                placeholder="例如：标准回测配置"
              />
            </div>

            <div className="space-y-2">
              <Label>模板描述</Label>
              <Input
                value={newTemplate.description}
                onChange={(e) => setNewTemplate({ ...newTemplate, description: e.target.value })}
                placeholder="简要描述此模板的用途"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>开始日期</Label>
                <Input
                  type="date"
                  value={newTemplate.config.start_date}
                  onChange={(e) =>
                    setNewTemplate({
                      ...newTemplate,
                      config: { ...newTemplate.config, start_date: e.target.value },
                    })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label>结束日期</Label>
                <Input
                  type="date"
                  value={newTemplate.config.end_date}
                  onChange={(e) =>
                    setNewTemplate({
                      ...newTemplate,
                      config: { ...newTemplate.config, end_date: e.target.value },
                    })
                  }
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>初始资金</Label>
                <Input
                  type="number"
                  value={newTemplate.config.initial_capital}
                  onChange={(e) =>
                    setNewTemplate({
                      ...newTemplate,
                      config: { ...newTemplate.config, initial_capital: Number(e.target.value) },
                    })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label>手续费率</Label>
                <Input
                  type="number"
                  step="0.0001"
                  value={newTemplate.config.commission_rate}
                  onChange={(e) =>
                    setNewTemplate({
                      ...newTemplate,
                      config: { ...newTemplate.config, commission_rate: Number(e.target.value) },
                    })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label>滑点（跳）</Label>
                <Input
                  type="number"
                  value={newTemplate.config.slippage}
                  onChange={(e) =>
                    setNewTemplate({
                      ...newTemplate,
                      config: { ...newTemplate.config, slippage: Number(e.target.value) },
                    })
                  }
                />
              </div>
            </div>

            <div className="flex gap-2">
              <Button onClick={handleSave} className="flex-1">
                保存模板
              </Button>
              <Button variant="outline" onClick={() => setIsCreating(false)} className="flex-1">
                取消
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 预设模板 */}
      {presetTemplates.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">预设模板</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-2">
              {presetTemplates.map((template) => (
                <div key={template.id} className="border rounded-lg p-4 space-y-2">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="font-medium">{template.name}</div>
                      <div className="text-xs text-muted-foreground">{template.description}</div>
                    </div>
                    <Badge variant="secondary">预设</Badge>
                  </div>
                  <div className="text-xs space-y-1 text-muted-foreground">
                    <div>初始资金: ¥{template.config.initial_capital.toLocaleString()}</div>
                    <div>手续费率: {(template.config.commission_rate * 100).toFixed(4)}%</div>
                    <div>滑点: {template.config.slippage} 跳</div>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => onLoad(template)} className="flex-1">
                      加载
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => handleDuplicate(template)}>
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 自定义模板 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">自定义模板</CardTitle>
        </CardHeader>
        <CardContent>
          {customTemplates.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              暂无自定义模板，点击"新建模板"创建
            </p>
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              {customTemplates.map((template) => (
                <div key={template.id} className="border rounded-lg p-4 space-y-2">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="font-medium">{template.name}</div>
                      <div className="text-xs text-muted-foreground">{template.description}</div>
                    </div>
                  </div>
                  <div className="text-xs space-y-1 text-muted-foreground">
                    <div>
                      时间范围: {template.config.start_date} ~ {template.config.end_date}
                    </div>
                    <div>初始资金: ¥{template.config.initial_capital.toLocaleString()}</div>
                    <div>手续费率: {(template.config.commission_rate * 100).toFixed(4)}%</div>
                    <div>滑点: {template.config.slippage} 跳</div>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => onLoad(template)} className="flex-1">
                      加载
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => onExport(template)}>
                      <Download className="h-4 w-4" />
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => handleDuplicate(template)}>
                      <Copy className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => onDelete(template.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
