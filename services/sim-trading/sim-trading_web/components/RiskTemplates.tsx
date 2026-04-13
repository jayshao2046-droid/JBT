"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Download, Upload, Save, Trash2, FileJson } from "lucide-react"
import { toast } from "sonner"

interface RiskTemplate {
  id: string
  name: string
  description: string
  config: {
    l2_thresholds: {
      max_consecutive_losses: number
      max_margin_rate: number
      max_daily_trades: number
      max_daily_loss_pct: number
    }
  }
}

const PRESET_TEMPLATES: RiskTemplate[] = [
  {
    id: "conservative",
    name: "保守模式",
    description: "适合新手或小资金账户，风控严格",
    config: {
      l2_thresholds: {
        max_consecutive_losses: 3,
        max_margin_rate: 50,
        max_daily_trades: 50,
        max_daily_loss_pct: 2.0,
      },
    },
  },
  {
    id: "balanced",
    name: "稳健模式",
    description: "平衡风险与收益，适合大多数交易者",
    config: {
      l2_thresholds: {
        max_consecutive_losses: 5,
        max_margin_rate: 70,
        max_daily_trades: 100,
        max_daily_loss_pct: 5.0,
      },
    },
  },
  {
    id: "aggressive",
    name: "激进模式",
    description: "追求高收益，风险较高",
    config: {
      l2_thresholds: {
        max_consecutive_losses: 10,
        max_margin_rate: 85,
        max_daily_trades: 200,
        max_daily_loss_pct: 10.0,
      },
    },
  },
]

export function RiskTemplates() {
  const [selectedTemplate, setSelectedTemplate] = useState<string>("balanced")
  const [customTemplates, setCustomTemplates] = useState<RiskTemplate[]>([])
  const [newTemplateName, setNewTemplateName] = useState("")
  const [showSaveDialog, setShowSaveDialog] = useState(false)

  const allTemplates = [...PRESET_TEMPLATES, ...customTemplates]

  const handleApplyTemplate = (templateId: string) => {
    const template = allTemplates.find(t => t.id === templateId)
    if (!template) return

    // TODO: 调用后端 API 应用模板
    // await simApi.applyRiskTemplate(template.config)
    toast.success(`已应用模板：${template.name}`)
    setSelectedTemplate(templateId)
  }

  const handleSaveCustomTemplate = () => {
    if (!newTemplateName.trim()) {
      toast.error("请输入模板名称")
      return
    }

    // TODO: 获取当前配置并保存为模板
    const newTemplate: RiskTemplate = {
      id: `custom_${Date.now()}`,
      name: newTemplateName,
      description: "自定义模板",
      config: {
        l2_thresholds: {
          max_consecutive_losses: 5,
          max_margin_rate: 70,
          max_daily_trades: 100,
          max_daily_loss_pct: 5.0,
        },
      },
    }

    setCustomTemplates(prev => [...prev, newTemplate])
    localStorage.setItem("risk_templates", JSON.stringify([...customTemplates, newTemplate]))
    toast.success(`已保存模板：${newTemplateName}`)
    setNewTemplateName("")
    setShowSaveDialog(false)
  }

  const handleDeleteTemplate = (templateId: string) => {
    const updatedTemplates = customTemplates.filter(t => t.id !== templateId)
    setCustomTemplates(updatedTemplates)
    localStorage.setItem("risk_templates", JSON.stringify(updatedTemplates))
    toast.success("已删除模板")
  }

  const handleExportTemplate = (template: RiskTemplate) => {
    const json = JSON.stringify(template, null, 2)
    const blob = new Blob([json], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = url
    link.download = `risk_template_${template.id}.json`
    link.click()
    URL.revokeObjectURL(url)
    toast.success("已导出模板")
  }

  const handleImportTemplate = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = e => {
      try {
        const template = JSON.parse(e.target?.result as string) as RiskTemplate
        template.id = `custom_${Date.now()}`
        setCustomTemplates(prev => [...prev, template])
        localStorage.setItem("risk_templates", JSON.stringify([...customTemplates, template]))
        toast.success(`已导入模板：${template.name}`)
      } catch (error) {
        toast.error("导入失败：文件格式错误")
      }
    }
    reader.readAsText(file)
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>风控模板</CardTitle>
          <div className="flex gap-2">
            <label htmlFor="import-template">
              <Button size="sm" variant="outline" asChild>
                <span>
                  <Upload className="h-4 w-4 mr-2" />
                  导入
                </span>
              </Button>
            </label>
            <input
              id="import-template"
              type="file"
              accept=".json"
              className="hidden"
              onChange={handleImportTemplate}
            />
            <Dialog open={showSaveDialog} onOpenChange={setShowSaveDialog}>
              <DialogTrigger asChild>
                <Button size="sm" variant="outline">
                  <Save className="h-4 w-4 mr-2" />
                  保存当前配置
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>保存为模板</DialogTitle>
                  <DialogDescription>将当前风控配置保存为自定义模板</DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label htmlFor="template-name">模板名称</Label>
                    <Input
                      id="template-name"
                      placeholder="例如：我的交易策略"
                      value={newTemplateName}
                      onChange={e => setNewTemplateName(e.target.value)}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowSaveDialog(false)}>
                    取消
                  </Button>
                  <Button onClick={handleSaveCustomTemplate}>保存</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* 预设模板 */}
        <div>
          <Label className="text-sm font-medium mb-2 block">预设模板</Label>
          <div className="grid gap-3">
            {PRESET_TEMPLATES.map(template => (
              <div
                key={template.id}
                className={`border rounded-lg p-3 cursor-pointer transition-colors ${
                  selectedTemplate === template.id
                    ? "border-primary bg-primary/5"
                    : "hover:border-primary/50"
                }`}
                onClick={() => handleApplyTemplate(template.id)}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="font-medium">{template.name}</div>
                    <div className="text-sm text-muted-foreground">{template.description}</div>
                    <div className="text-xs text-muted-foreground mt-2">
                      连续亏损: {template.config.l2_thresholds.max_consecutive_losses} 次 |
                      保证金率: {template.config.l2_thresholds.max_margin_rate}% | 日内交易:{" "}
                      {template.config.l2_thresholds.max_daily_trades} 次
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={e => {
                      e.stopPropagation()
                      handleExportTemplate(template)
                    }}
                  >
                    <Download className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 自定义模板 */}
        {customTemplates.length > 0 && (
          <div>
            <Label className="text-sm font-medium mb-2 block">自定义模板</Label>
            <div className="grid gap-3">
              {customTemplates.map(template => (
                <div
                  key={template.id}
                  className={`border rounded-lg p-3 cursor-pointer transition-colors ${
                    selectedTemplate === template.id
                      ? "border-primary bg-primary/5"
                      : "hover:border-primary/50"
                  }`}
                  onClick={() => handleApplyTemplate(template.id)}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="font-medium">{template.name}</div>
                      <div className="text-sm text-muted-foreground">{template.description}</div>
                      <div className="text-xs text-muted-foreground mt-2">
                        连续亏损: {template.config.l2_thresholds.max_consecutive_losses} 次 |
                        保证金率: {template.config.l2_thresholds.max_margin_rate}% | 日内交易:{" "}
                        {template.config.l2_thresholds.max_daily_trades} 次
                      </div>
                    </div>
                    <div className="flex gap-1">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={e => {
                          e.stopPropagation()
                          handleExportTemplate(template)
                        }}
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={e => {
                          e.stopPropagation()
                          handleDeleteTemplate(template.id)
                        }}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
