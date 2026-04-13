"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { CalendarIcon } from "lucide-react"
import { format } from "date-fns"

interface BacktestConfig {
  start_date: string
  end_date: string
  initial_capital: number
  commission_rate: number
  slippage: number
  instruments?: string[]
}

interface BacktestConfigEditorProps {
  initialConfig?: BacktestConfig
  onSave: (config: BacktestConfig) => void
  onCancel?: () => void
}

export function BacktestConfigEditor({ initialConfig, onSave, onCancel }: BacktestConfigEditorProps) {
  const [config, setConfig] = useState<BacktestConfig>(
    initialConfig || {
      start_date: "2023-01-01",
      end_date: "2023-12-31",
      initial_capital: 1000000,
      commission_rate: 0.0003,
      slippage: 1,
      instruments: [],
    }
  )

  const [startDate, setStartDate] = useState<Date | undefined>(
    initialConfig?.start_date ? new Date(initialConfig.start_date) : new Date("2023-01-01")
  )
  const [endDate, setEndDate] = useState<Date | undefined>(
    initialConfig?.end_date ? new Date(initialConfig.end_date) : new Date("2023-12-31")
  )

  const [instrumentsText, setInstrumentsText] = useState(
    initialConfig?.instruments?.join(", ") || ""
  )

  const handleSave = () => {
    const finalConfig: BacktestConfig = {
      ...config,
      start_date: startDate ? format(startDate, "yyyy-MM-dd") : config.start_date,
      end_date: endDate ? format(endDate, "yyyy-MM-dd") : config.end_date,
      instruments: instrumentsText
        .split(",")
        .map(s => s.trim())
        .filter(s => s.length > 0),
    }
    onSave(finalConfig)
  }

  const updateConfig = (field: keyof BacktestConfig, value: any) => {
    setConfig({ ...config, [field]: value })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>回测配置编辑器</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* 时间范围 */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>开始日期</Label>
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" className="w-full justify-start text-left font-normal">
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {startDate ? format(startDate, "yyyy-MM-dd") : "选择日期"}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0">
                <Calendar
                  mode="single"
                  selected={startDate}
                  onSelect={setStartDate}
                  initialFocus
                />
              </PopoverContent>
            </Popover>
          </div>

          <div className="space-y-2">
            <Label>结束日期</Label>
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" className="w-full justify-start text-left font-normal">
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {endDate ? format(endDate, "yyyy-MM-dd") : "选择日期"}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0">
                <Calendar
                  mode="single"
                  selected={endDate}
                  onSelect={setEndDate}
                  initialFocus
                />
              </PopoverContent>
            </Popover>
          </div>
        </div>

        {/* 初始资金 */}
        <div className="space-y-2">
          <Label>初始资金（元）</Label>
          <Input
            type="number"
            value={config.initial_capital}
            onChange={(e) => updateConfig("initial_capital", Number(e.target.value))}
            placeholder="1000000"
          />
          <p className="text-xs text-muted-foreground">
            当前设置：¥{config.initial_capital.toLocaleString()}
          </p>
        </div>

        {/* 手续费率 */}
        <div className="space-y-2">
          <Label>手续费率</Label>
          <Input
            type="number"
            step="0.0001"
            value={config.commission_rate}
            onChange={(e) => updateConfig("commission_rate", Number(e.target.value))}
            placeholder="0.0003"
          />
          <p className="text-xs text-muted-foreground">
            当前设置：{(config.commission_rate * 100).toFixed(4)}%（双边）
          </p>
        </div>

        {/* 滑点 */}
        <div className="space-y-2">
          <Label>滑点（跳）</Label>
          <Input
            type="number"
            value={config.slippage}
            onChange={(e) => updateConfig("slippage", Number(e.target.value))}
            placeholder="1"
          />
          <p className="text-xs text-muted-foreground">
            每次交易的价格滑点，单位为最小变动价位
          </p>
        </div>

        {/* 交易品种 */}
        <div className="space-y-2">
          <Label>交易品种（可选）</Label>
          <Input
            value={instrumentsText}
            onChange={(e) => setInstrumentsText(e.target.value)}
            placeholder="例如：rb2310, hc2310, i2309"
          />
          <p className="text-xs text-muted-foreground">
            多个品种用逗号分隔，留空表示策略自动选择
          </p>
        </div>

        {/* 预设配置 */}
        <div className="space-y-2">
          <Label>快速预设</Label>
          <div className="grid grid-cols-3 gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setConfig({
                  ...config,
                  initial_capital: 1000000,
                  commission_rate: 0.0003,
                  slippage: 1,
                })
              }}
            >
              标准配置
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setConfig({
                  ...config,
                  initial_capital: 100000,
                  commission_rate: 0.0005,
                  slippage: 2,
                })
              }}
            >
              小资金
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setConfig({
                  ...config,
                  initial_capital: 10000000,
                  commission_rate: 0.0002,
                  slippage: 1,
                })
              }}
            >
              大资金
            </Button>
          </div>
        </div>

        {/* 配置摘要 */}
        <div className="rounded-lg bg-muted p-4 space-y-2">
          <div className="text-sm font-medium">配置摘要</div>
          <div className="text-xs space-y-1 text-muted-foreground">
            <div>回测周期：{startDate ? format(startDate, "yyyy-MM-dd") : config.start_date} 至 {endDate ? format(endDate, "yyyy-MM-dd") : config.end_date}</div>
            <div>初始资金：¥{config.initial_capital.toLocaleString()}</div>
            <div>手续费率：{(config.commission_rate * 100).toFixed(4)}%</div>
            <div>滑点：{config.slippage} 跳</div>
            {instrumentsText && <div>交易品种：{instrumentsText}</div>}
          </div>
        </div>

        {/* 操作按钮 */}
        <div className="flex gap-2">
          <Button onClick={handleSave} className="flex-1">
            保存配置
          </Button>
          {onCancel && (
            <Button variant="outline" onClick={onCancel} className="flex-1">
              取消
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
