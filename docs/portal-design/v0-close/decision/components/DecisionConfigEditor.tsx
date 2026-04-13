"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Settings } from "lucide-react"

export function DecisionConfigEditor() {
  const [config, setConfig] = useState({
    strategy_params: {
      initial_capital: 100000,
      max_position_size: 0.3,
      stop_loss_pct: 0.03,
      take_profit_pct: 0.08,
    },
    factor_weights: {
      momentum: 0.3,
      value: 0.25,
      quality: 0.25,
      sentiment: 0.2,
    },
    risk_params: {
      max_drawdown: 0.2,
      max_leverage: 2.0,
      position_limit: 10,
    },
  })

  const handleSave = () => {
    console.log("Saving config:", config)
    // TODO: 调用 API 保存配置
  }

  return (
    <Card className="bg-neutral-800 border-neutral-700">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <Settings className="w-5 h-5 text-purple-500" />
          决策配置编辑器
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* 策略参数 */}
          <div>
            <h3 className="text-sm font-medium text-white mb-3">策略参数</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-neutral-300">初始资金</Label>
                <Input
                  type="number"
                  value={config.strategy_params.initial_capital}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      strategy_params: { ...config.strategy_params, initial_capital: parseFloat(e.target.value) },
                    })
                  }
                  className="bg-neutral-900 border-neutral-700 text-white"
                />
              </div>
              <div>
                <Label className="text-neutral-300">最大仓位</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={config.strategy_params.max_position_size}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      strategy_params: { ...config.strategy_params, max_position_size: parseFloat(e.target.value) },
                    })
                  }
                  className="bg-neutral-900 border-neutral-700 text-white"
                />
              </div>
              <div>
                <Label className="text-neutral-300">止损比例</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={config.strategy_params.stop_loss_pct}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      strategy_params: { ...config.strategy_params, stop_loss_pct: parseFloat(e.target.value) },
                    })
                  }
                  className="bg-neutral-900 border-neutral-700 text-white"
                />
              </div>
              <div>
                <Label className="text-neutral-300">止盈比例</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={config.strategy_params.take_profit_pct}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      strategy_params: { ...config.strategy_params, take_profit_pct: parseFloat(e.target.value) },
                    })
                  }
                  className="bg-neutral-900 border-neutral-700 text-white"
                />
              </div>
            </div>
          </div>

          {/* 因子权重 */}
          <div>
            <h3 className="text-sm font-medium text-white mb-3">因子权重配置</h3>
            <div className="grid grid-cols-2 gap-4">
              {Object.entries(config.factor_weights).map(([key, value]) => (
                <div key={key}>
                  <Label className="text-neutral-300 capitalize">{key}</Label>
                  <Input
                    type="number"
                    step="0.05"
                    value={value}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        factor_weights: { ...config.factor_weights, [key]: parseFloat(e.target.value) },
                      })
                    }
                    className="bg-neutral-900 border-neutral-700 text-white"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* 风控参数 */}
          <div>
            <h3 className="text-sm font-medium text-white mb-3">风控参数</h3>
            <div className="grid grid-cols-2 gap-4">
              {Object.entries(config.risk_params).map(([key, value]) => (
                <div key={key}>
                  <Label className="text-neutral-300 capitalize">{key.replace(/_/g, " ")}</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={value}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        risk_params: { ...config.risk_params, [key]: parseFloat(e.target.value) },
                      })
                    }
                    className="bg-neutral-900 border-neutral-700 text-white"
                  />
                </div>
              ))}
            </div>
          </div>

          <Button onClick={handleSave} className="w-full">
            保存配置
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
