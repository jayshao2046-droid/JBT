"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { RefreshCw, Save, ShieldCheck, AlertTriangle } from "lucide-react"
import { toast } from "sonner"
import { simApi, type RiskPreset } from "@/lib/sim-api"

type PresetRow = RiskPreset & { symbol: string; editing: boolean; dirty: boolean }

const EXCHANGES: Record<string, string> = {
  // SHFE 上期所
  RB: "上期所", HC: "上期所", SS: "上期所", SP: "上期所", CU: "上期所", AL: "上期所",
  ZN: "上期所", PB: "上期所", NI: "上期所", SN: "上期所", BC: "上期所", AU: "上期所",
  AG: "上期所", FU: "上期所", BU: "上期所", RU: "上期所", NR: "上期所",
  // DCE 大商所
  I: "大商所", J: "大商所", JM: "大商所", A: "大商所", B: "大商所", M: "大商所",
  Y: "大商所", P: "大商所", C: "大商所", CS: "大商所", RR: "大商所", LH: "大商所",
  V: "大商所", L: "大商所", PP: "大商所", EG: "大商所", EB: "大商所", PG: "大商所",
  // CZCE 郑商所
  CF: "郑商所", CY: "郑商所", SR: "郑商所", AP: "郑商所", CJ: "郑商所", OI: "郑商所",
  RM: "郑商所", RS: "郑商所", PK: "郑商所", SM: "郑商所", SF: "郑商所", TA: "郑商所",
  MA: "郑商所", FG: "郑商所", SA: "郑商所", UR: "郑商所", PF: "郑商所", PX: "郑商所",
  // CFFEX 中金所
  IF: "中金所", IC: "中金所", IH: "中金所", IM: "中金所", T: "中金所",
  TF: "中金所", TS: "中金所", TL: "中金所",
  // INE 上海能源 / GFEX 广期所
  SC: "上海能源", LU: "上海能源", SI: "广期所", LC: "广期所",
}

export default function RiskPresetsPage() {
  const [rows, setRows] = useState<PresetRow[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [saving, setSaving] = useState<string | null>(null)

  const loadPresets = async () => {
    setIsLoading(true)
    try {
      const { presets } = await simApi.riskPresets()
      setRows(
        Object.entries(presets).map(([symbol, p]) => ({
          symbol,
          ...p,
          editing: false,
          dirty: false,
        }))
      )
    } catch {
      toast.error("加载风控预设失败，请检查后端连接")
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => { loadPresets() }, [])

  const update = (symbol: string, field: keyof RiskPreset, value: unknown) => {
    setRows(rows.map(r => r.symbol === symbol ? { ...r, [field]: value, dirty: true } : r))
  }

  const save = async (row: PresetRow) => {
    setSaving(row.symbol)
    try {
      await simApi.updateRiskPreset({
        symbol: row.symbol,
        name: row.name,
        max_lots: Number(row.max_lots),
        max_position: Number(row.max_position),
        daily_loss_pct: Number(row.daily_loss_pct),
        price_dev_pct: Number(row.price_dev_pct),
        enabled: row.enabled,
        commission: Number(row.commission),
        slippage_ticks: Number(row.slippage_ticks),
      })
      setRows(rows.map(r => r.symbol === row.symbol ? { ...r, dirty: false } : r))
      toast.success(`${row.name}（${row.symbol}）风控预设已保存`)
    } catch {
      toast.error(`保存 ${row.symbol} 失败`)
    } finally {
      setSaving(null)
    }
  }

  const toggleEnabled = (symbol: string) => {
    const row = rows.find(r => r.symbol === symbol)
    if (!row) return
    update(symbol, "enabled", !row.enabled)
  }

  const enabledCount = rows.filter(r => r.enabled).length

  return (
    <div className="p-6 space-y-6 bg-neutral-950 min-h-screen">
      {/* 头部 */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wider">品种预设风控</h1>
          <p className="text-sm text-neutral-400">
            每个品种独立配置风控参数，策略 YAML 不含风控时由此处 100% 强制执行
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="outline" className="border-orange-600 text-orange-400">
            已启用 {enabledCount} / {rows.length} 个品种
          </Badge>
          <Button
            onClick={loadPresets}
            variant="ghost"
            size="icon"
            className="text-neutral-400 hover:text-orange-500"
            disabled={isLoading}
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {/* 说明卡 */}
      <Card className="bg-amber-900/20 border-amber-700/50">
        <CardContent className="p-4 flex gap-3 items-start">
          <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
          <div className="text-xs text-amber-300 space-y-1">
            <p>• <strong>单笔最大手数</strong>：单笔报单超限直接废单，不拆单</p>
            <p>• <strong>单品种最大持仓</strong>：净持仓超限后新开仓被拒绝</p>
            <p>• <strong>日亏限额</strong>：该品种当日浮亏+实亏超过账户权益的该百分比后暂停该品种</p>
            <p>• <strong>价格偏离限制</strong>：报单价偏离最新价超过该百分比时视为异常价格，废单保护</p>
          </div>
        </CardContent>
      </Card>

      {/* 风控预设表格 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-300 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-orange-500" />
            品种风控参数表
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-neutral-700 bg-neutral-800/50">
                  <th className="text-left py-3 px-4 text-xs text-neutral-400 w-12">启用</th>
                  <th className="text-left py-3 px-4 text-xs text-neutral-400">品种</th>
                  <th className="text-left py-3 px-4 text-xs text-neutral-400">交易所</th>
                  <th className="text-left py-3 px-4 text-xs text-neutral-400">单笔最大手数</th>
                  <th className="text-left py-3 px-4 text-xs text-neutral-400">最大持仓(手)</th>
                  <th className="text-left py-3 px-4 text-xs text-neutral-400">日亏限额(%)</th>
                  <th className="text-left py-3 px-4 text-xs text-neutral-400">价格偏离(%)</th>
                  <th className="text-left py-3 px-4 text-xs text-neutral-400">手续费(元/手)</th>
                  <th className="text-left py-3 px-4 text-xs text-neutral-400">滑点(Tick)</th>
                  <th className="text-left py-3 px-4 text-xs text-neutral-400">操作</th>
                </tr>
              </thead>
              <tbody>
                {rows.map(row => (
                  <tr
                    key={row.symbol}
                    className={`border-b border-neutral-800 transition-colors ${
                      row.enabled ? "hover:bg-neutral-800/50" : "opacity-50 hover:bg-neutral-900/30"
                    } ${row.dirty ? "bg-orange-900/10" : ""}`}
                  >
                    {/* 启用开关 */}
                    <td className="py-3 px-4">
                      <button
                        onClick={() => toggleEnabled(row.symbol)}
                        className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                          row.enabled ? "bg-orange-500" : "bg-neutral-600"
                        }`}
                      >
                        <span
                          className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                            row.enabled ? "translate-x-5" : "translate-x-0.5"
                          }`}
                        />
                      </button>
                    </td>
                    {/* 品种名 */}
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-orange-400 font-bold">{row.symbol}</span>
                        <span className="text-neutral-300">{row.name}</span>
                        {row.dirty && <Badge className="bg-orange-900/30 text-orange-400 text-xs border-none">未保存</Badge>}
                      </div>
                    </td>
                    {/* 交易所 */}
                    <td className="py-3 px-4 text-xs text-neutral-500">{EXCHANGES[row.symbol] ?? "--"}</td>
                    {/* 单笔手数 */}
                    <td className="py-3 px-4">
                      <Input
                        type="number"
                        value={row.max_lots}
                        min={1}
                        max={100}
                        onChange={e => update(row.symbol, "max_lots", e.target.value)}
                        className="w-20 h-7 bg-neutral-800 border-neutral-600 text-white text-xs text-center"
                      />
                    </td>
                    {/* 最大持仓 */}
                    <td className="py-3 px-4">
                      <Input
                        type="number"
                        value={row.max_position}
                        min={1}
                        max={500}
                        onChange={e => update(row.symbol, "max_position", e.target.value)}
                        className="w-20 h-7 bg-neutral-800 border-neutral-600 text-white text-xs text-center"
                      />
                    </td>
                    {/* 日亏限额 */}
                    <td className="py-3 px-4">
                      <Input
                        type="number"
                        value={row.daily_loss_pct}
                        min={0.1}
                        max={10}
                        step={0.1}
                        onChange={e => update(row.symbol, "daily_loss_pct", e.target.value)}
                        className="w-20 h-7 bg-neutral-800 border-neutral-600 text-white text-xs text-center"
                      />
                    </td>
                    {/* 价格偏离 */}
                    <td className="py-3 px-4">
                      <Input
                        type="number"
                        value={row.price_dev_pct}
                        min={0.1}
                        max={5}
                        step={0.1}
                        onChange={e => update(row.symbol, "price_dev_pct", e.target.value)}
                        className="w-20 h-7 bg-neutral-800 border-neutral-600 text-white text-xs text-center"
                      />
                    </td>
                    {/* 手续费 */}
                    <td className="py-3 px-4">
                      <Input
                        type="number"
                        value={row.commission}
                        min={0}
                        step={0.5}
                        onChange={e => update(row.symbol, "commission", e.target.value)}
                        className="w-20 h-7 bg-neutral-800 border-neutral-600 text-white text-xs text-center"
                      />
                    </td>
                    {/* 滑点 */}
                    <td className="py-3 px-4">
                      <Input
                        type="number"
                        value={row.slippage_ticks}
                        min={0}
                        max={5}
                        onChange={e => update(row.symbol, "slippage_ticks", e.target.value)}
                        className="w-16 h-7 bg-neutral-800 border-neutral-600 text-white text-xs text-center"
                      />
                    </td>
                    {/* 保存 */}
                    <td className="py-3 px-4">
                      <Button
                        size="sm"
                        onClick={() => save(row)}
                        disabled={!row.dirty || saving === row.symbol}
                        className={`h-7 px-3 text-xs ${
                          row.dirty
                            ? "bg-orange-600 hover:bg-orange-700 text-white"
                            : "bg-neutral-800 text-neutral-600"
                        }`}
                      >
                        <Save className="w-3 h-3 mr-1" />
                        {saving === row.symbol ? "保存中..." : "保存"}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
