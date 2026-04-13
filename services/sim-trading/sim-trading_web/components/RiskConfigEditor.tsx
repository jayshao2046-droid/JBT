"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Save, RotateCcw } from "lucide-react"
import { toast } from "sonner"

interface RiskConfig {
  l1_rules: {
    trading_enabled_check: boolean
    ctp_connected_check: boolean
    reduce_only_check: boolean
    disaster_stop_check: boolean
    max_position_check: boolean
    daily_loss_check: boolean
    price_deviation_check: boolean
    order_frequency_check: boolean
    margin_rate_check: boolean
    connection_quality_check: boolean
  }
  l2_thresholds: {
    max_consecutive_losses: number
    max_margin_rate: number
    max_daily_trades: number
    max_daily_loss_pct: number
  }
}

const DEFAULT_CONFIG: RiskConfig = {
  l1_rules: {
    trading_enabled_check: true,
    ctp_connected_check: true,
    reduce_only_check: false,
    disaster_stop_check: true,
    max_position_check: true,
    daily_loss_check: true,
    price_deviation_check: true,
    order_frequency_check: true,
    margin_rate_check: true,
    connection_quality_check: true,
  },
  l2_thresholds: {
    max_consecutive_losses: 5,
    max_margin_rate: 70,
    max_daily_trades: 100,
    max_daily_loss_pct: 5.0,
  },
}

export function RiskConfigEditor() {
  const [config, setConfig] = useState<RiskConfig>(DEFAULT_CONFIG)
  const [hasChanges, setHasChanges] = useState(false)

  const handleL1RuleChange = (rule: keyof RiskConfig["l1_rules"], value: boolean) => {
    setConfig(prev => ({
      ...prev,
      l1_rules: {
        ...prev.l1_rules,
        [rule]: value,
      },
    }))
    setHasChanges(true)
  }

  const handleL2ThresholdChange = (
    threshold: keyof RiskConfig["l2_thresholds"],
    value: number
  ) => {
    setConfig(prev => ({
      ...prev,
      l2_thresholds: {
        ...prev.l2_thresholds,
        [threshold]: value,
      },
    }))
    setHasChanges(true)
  }

  const handleSave = async () => {
    try {
      // TODO: 调用后端 API 保存配置
      // await simApi.saveRiskConfig(config)
      toast.success("风控配置已保存")
      setHasChanges(false)
    } catch (error) {
      toast.error("保存失败：" + (error as Error).message)
    }
  }

  const handleReset = () => {
    setConfig(DEFAULT_CONFIG)
    setHasChanges(false)
    toast.info("已重置为默认配置")
  }

  const L1_RULE_LABELS: Record<keyof RiskConfig["l1_rules"], string> = {
    trading_enabled_check: "交易开关检查",
    ctp_connected_check: "CTP 连接检查",
    reduce_only_check: "只减仓模式检查",
    disaster_stop_check: "灾难止损检查",
    max_position_check: "最大持仓检查",
    daily_loss_check: "日内亏损检查",
    price_deviation_check: "价格偏离检查",
    order_frequency_check: "下单频率检查",
    margin_rate_check: "保证金率检查",
    connection_quality_check: "连接质量检查",
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>风控规则配置</CardTitle>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={handleReset}>
              <RotateCcw className="h-4 w-4 mr-2" />
              重置
            </Button>
            <Button size="sm" onClick={handleSave} disabled={!hasChanges}>
              <Save className="h-4 w-4 mr-2" />
              保存
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="l1">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="l1">L1 风控规则</TabsTrigger>
            <TabsTrigger value="l2">L2 风控阈值</TabsTrigger>
          </TabsList>

          <TabsContent value="l1" className="space-y-4 mt-4">
            <div className="text-sm text-muted-foreground mb-4">
              L1 风控规则是基础检查项，关闭后对应检查将被跳过
            </div>
            <div className="space-y-3">
              {Object.entries(config.l1_rules).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between">
                  <Label htmlFor={key} className="cursor-pointer">
                    {L1_RULE_LABELS[key as keyof RiskConfig["l1_rules"]]}
                  </Label>
                  <Switch
                    id={key}
                    checked={value}
                    onCheckedChange={checked =>
                      handleL1RuleChange(key as keyof RiskConfig["l1_rules"], checked)
                    }
                  />
                </div>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="l2" className="space-y-6 mt-4">
            <div className="text-sm text-muted-foreground mb-4">
              L2 风控阈值是数值限制，超过阈值将触发告警或限制交易
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <Label>最大连续亏损次数</Label>
                <span className="text-sm font-medium">
                  {config.l2_thresholds.max_consecutive_losses} 次
                </span>
              </div>
              <Slider
                value={[config.l2_thresholds.max_consecutive_losses]}
                onValueChange={([value]) =>
                  handleL2ThresholdChange("max_consecutive_losses", value)
                }
                min={1}
                max={20}
                step={1}
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <Label>最大保证金率</Label>
                <span className="text-sm font-medium">
                  {config.l2_thresholds.max_margin_rate}%
                </span>
              </div>
              <Slider
                value={[config.l2_thresholds.max_margin_rate]}
                onValueChange={([value]) => handleL2ThresholdChange("max_margin_rate", value)}
                min={30}
                max={95}
                step={5}
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <Label>日内最大交易次数</Label>
                <span className="text-sm font-medium">
                  {config.l2_thresholds.max_daily_trades} 次
                </span>
              </div>
              <Slider
                value={[config.l2_thresholds.max_daily_trades]}
                onValueChange={([value]) => handleL2ThresholdChange("max_daily_trades", value)}
                min={10}
                max={500}
                step={10}
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <Label>日内最大亏损比例</Label>
                <span className="text-sm font-medium">
                  {config.l2_thresholds.max_daily_loss_pct.toFixed(1)}%
                </span>
              </div>
              <Slider
                value={[config.l2_thresholds.max_daily_loss_pct]}
                onValueChange={([value]) => handleL2ThresholdChange("max_daily_loss_pct", value)}
                min={1}
                max={20}
                step={0.5}
              />
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
