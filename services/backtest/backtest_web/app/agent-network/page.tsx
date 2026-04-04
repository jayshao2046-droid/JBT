"use client"

import { useEffect, useRef, useState } from "react"
import api, { deleteStrategy, exportStrategyContent, saveStrategyParams, approveStrategyLocal, getApprovedStrategies, isStrategyApproved, revokeApprovedStrategy, markStrategyDelivered } from "@/src/utils/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import EmptyState from "@/components/ui/empty-state"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Search,
  Upload,
  Edit2,
  Play,
  CheckCircle,
  XCircle,
  FileText,
  Activity,
  Clock,
  Download,
  Trash2,
  Settings,
  Save,
  Shield,
  AlertTriangle,
  Zap,
  X,
} from "lucide-react"

type ParamValues = Record<string, string>

// ─── 双语参数标签体系 ──────────────────────────────────────────────
// 所有从策略 YAML 读取的参数均在此映射中标注中英文注释
const PARAM_BILINGUAL: Record<string, { zh: string; en: string; unit?: string; desc: string }> = {
  // 执行通用
  slippage:         { zh: "滑点",         en: "Slippage",          unit: "点",  desc: "每笔成交价格偏差 / Price deviation per trade" },
  commission:       { zh: "手续费",       en: "Commission",        unit: "%",   desc: "每笔交易手续费率 / Transaction fee rate" },
  initialCapital:   { zh: "初始资金",     en: "Initial Capital",   unit: "元",  desc: "回测启动资金 / Backtest starting capital" },
  positionSize:     { zh: "持仓占比",     en: "Position Size",     unit: "%",   desc: "单次开仓资金占比 / Capital ratio per trade" },
  minLotSize:       { zh: "最小手数",     en: "Min Lot Size",      unit: "手",  desc: "最小下单单位 / Minimum order unit" },
  leverage:         { zh: "杠杆倍数",     en: "Leverage",                       desc: "杠杆比例 / Leverage ratio" },
  multiplier:       { zh: "合约乘数",     en: "Contract Mult.",                 desc: "期货合约乘数 / Futures multiplier" },
  // K线/时序
  lookback:         { zh: "回望周期",     en: "Lookback",          unit: "根",  desc: "K线回望数量 / Lookback bar count" },
  period:           { zh: "计算周期",     en: "Period",            unit: "根",  desc: "通用指标计算窗口 / Indicator window" },
  window:           { zh: "窗口大小",     en: "Window",            unit: "根",  desc: "计算窗口大小 / Calculation window" },
  fast_period:      { zh: "快线周期",     en: "Fast Period",       unit: "根",  desc: "快速均线/指标周期 / Fast period" },
  slow_period:      { zh: "慢线周期",     en: "Slow Period",       unit: "根",  desc: "慢速均线/指标周期 / Slow period" },
  signal_period:    { zh: "信号线周期",   en: "Signal Period",     unit: "根",  desc: "MACD信号线周期 / Signal line period" },
  atr_period:       { zh: "ATR 周期",    en: "ATR Period",        unit: "根",  desc: "平均真实波幅计算周期 / ATR window" },
  rsi_period:       { zh: "RSI 周期",    en: "RSI Period",        unit: "根",  desc: "RSI指标周期 / RSI window" },
  ma_period:        { zh: "均线周期",     en: "MA Period",         unit: "根",  desc: "简单移动均线周期 / SMA window" },
  ma_short:         { zh: "短期均线",     en: "Short MA",          unit: "根",  desc: "短期均线周期 / Short-term MA" },
  ma_long:          { zh: "长期均线",     en: "Long MA",           unit: "根",  desc: "长期均线周期 / Long-term MA" },
  ema_period:       { zh: "EMA 周期",    en: "EMA Period",        unit: "根",  desc: "指数移动均线周期 / EMA window" },
  cooldown:         { zh: "冷却期",       en: "Cooldown",          unit: "根",  desc: "信号触发后冷却K线数 / Cooldown bars" },
  // 信号阈值
  threshold:        { zh: "信号阈值",     en: "Threshold",                      desc: "入场信号触发阈值 / Signal trigger threshold" },
  entry_threshold:  { zh: "入场阈值",     en: "Entry Threshold",                desc: "触发开仓信号 / Entry signal threshold" },
  exit_threshold:   { zh: "出场阈值",     en: "Exit Threshold",                 desc: "触发平仓信号 / Exit signal threshold" },
  upper_threshold:  { zh: "上轨阈值",     en: "Upper Threshold",                desc: "上轨/超买 / Upper band threshold" },
  lower_threshold:  { zh: "下轨阈值",     en: "Lower Threshold",                desc: "下轨/超卖 / Lower band threshold" },
  overbought:       { zh: "超买线",       en: "Overbought",                     desc: "RSI/随机超买阈值 / Overbought level" },
  oversold:         { zh: "超卖线",       en: "Oversold",                       desc: "RSI/随机超卖阈值 / Oversold level" },
  // 风控参数
  stop_loss:        { zh: "止损比例",     en: "Stop Loss",         unit: "%",   desc: "最大亏损限制 / Max loss limit" },
  take_profit:      { zh: "止盈比例",     en: "Take Profit",       unit: "%",   desc: "目标盈利 / Target profit" },
  trailing_stop:    { zh: "追踪止损",     en: "Trailing Stop",     unit: "%",   desc: "移动止损比例 / Trailing stop %" },
  max_drawdown:     { zh: "最大允许回撤", en: "Max Drawdown",      unit: "%",   desc: "策略风控回撤上限 / Risk control max DD" },
  max_position:     { zh: "最大仓位",     en: "Max Position",      unit: "手",  desc: "持仓上限手数 / Max lots" },
  no_overnight:     { zh: "不隔夜",       en: "No Overnight",                   desc: "强制日内平仓 / Force intraday close" },
  // 因子/模型
  alpha:            { zh: "Alpha 系数",  en: "Alpha",                           desc: "计算权重系数 / Weight coefficient" },
  beta:             { zh: "Beta 系数",   en: "Beta",                            desc: "市场敏感度 / Market sensitivity" },
  atr_mult:         { zh: "ATR 倍数",    en: "ATR Multiplier",                  desc: "ATR止损倍数 / ATR stop multiplier" },
  volatility_mult:  { zh: "波动率倍数",   en: "Vol Multiplier",                  desc: "波动率倍数参数 / Volatility multiplier" },
  momentum:         { zh: "动量参数",     en: "Momentum",                        desc: "动量计算系数 / Momentum coefficient" },
  // K线时序（YAML 顶层）
  timeframe_minutes:{ zh: "K线周期",     en: "Timeframe",         unit: "分钟",  desc: "策略运行的K线时间周期 / Strategy timeframe" },
  initial_capital:  { zh: "初始资金",     en: "Initial Capital",   unit: "元",   desc: "回测启动资金 / Backtest starting capital" },
  position_fraction:{ zh: "持仓占比",     en: "Position Fraction", unit: "小数", desc: "单次开仓资金占比（小数格式，如0.08=8%） / Capital ratio decimal" },
  min_position_size:{ zh: "最小仓位",     en: "Min Position Size", unit: "手",   desc: "最小下单手数 / Minimum position size in lots" },
  // 风控参数（YAML risk: 节）
  daily_loss_limit_yuan:    { zh: "日亏损限额",     en: "Daily Loss Limit",    unit: "元",   desc: "当日最大允许亏损金额，触发熔断 / Max daily loss in yuan" },
  per_symbol_fuse_yuan:     { zh: "单品种熔断",     en: "Per Symbol Fuse",    unit: "元",   desc: "单品种亏损熔断阈值 / Per symbol loss fuse" },
  max_drawdown_pct:         { zh: "最大回撤限制",   en: "Max Drawdown %",     unit: "小数", desc: "策略级最大回撤触发熔断（如0.03=3%） / Drawdown fuse ratio" },
  force_close_day:          { zh: "日盘强平时间",   en: "Force Close Day",               desc: "日盘最晚强制平仓时间 / Day session force close time" },
  force_close_night:        { zh: "夜盘强平时间",   en: "Force Close Night",             desc: "夜盘最晚强制平仓时间 / Night session force close time" },
  slippage_points:          { zh: "滑点（点数）",   en: "Slippage Points",   unit: "点",   desc: "成交价格偏差点数 / Price slippage in ticks" },
  commission_rate:          { zh: "手续费率",       en: "Commission Rate",   unit: "小数", desc: "每笔交易手续费率（如0.0001） / Fee rate per trade" },
  per_trade_stop_loss_pct:  { zh: "单笔止损",       en: "Stop Loss %",       unit: "小数", desc: "单笔最大止损比例（如0.012=1.2%） / Per trade stop loss ratio" },
  per_trade_take_profit_pct:{ zh: "单笔止盈",       en: "Take Profit %",     unit: "小数", desc: "单笔目标止盈比例（如0.02=2%） / Per trade take profit ratio" },
  atr_filter_multiple:      { zh: "ATR过滤倍数",    en: "ATR Filter Mult.",             desc: "ATR过滤入场条件倍数 / ATR filter entry condition" },
  atr_stop_loss_multiple:   { zh: "ATR止损倍数",    en: "ATR Stop Mult.",               desc: "基于ATR的动态止损倍数 / ATR-based stop loss multiplier" },
  atr_take_profit_multiple: { zh: "ATR止盈倍数",    en: "ATR TP Mult.",                 desc: "基于ATR的动态止盈倍数 / ATR-based take profit multiplier" },
  // 合约规格（YAML contract_specs: 节）
  contract_size:   { zh: "合约乘数",    en: "Contract Size",   unit: "吨/手", desc: "每手合约代表的实物数量 / Contract unit size" },
  min_price_move:  { zh: "最小价格变动", en: "Min Price Move",  unit: "元",   desc: "最小价格波动单位 / Minimum price tick size" },
  price_per_tick:  { zh: "每跳盈亏",    en: "Price Per Tick",  unit: "元",   desc: "每个最小价格变动的盈亏 / P&L per tick" },
  margin_ratio:    { zh: "保证金比例",   en: "Margin Ratio",   unit: "小数", desc: "合约保证金占名义价值比例 / Contract margin ratio" },
  // 信号参数（YAML signal: 节）
  long_threshold:  { zh: "多头阈值",    en: "Long Threshold",              desc: "因子合成多头信号触发阈值 / Long signal threshold" },
  short_threshold: { zh: "空头阈值",    en: "Short Threshold",             desc: "因子合成空头信号触发阈值 / Short signal threshold" },
  ema_periods:     { zh: "EMA平滑期",   en: "EMA Periods",   unit: "根",   desc: "信号EMA平滑周期数 / Signal smoothing EMA period" },
  confirm_bars:    { zh: "确认K线数",   en: "Confirm Bars",  unit: "根",   desc: "信号确认所需K线数量 / Bars required to confirm signal" },
}

// ─── 辅助：从 YAML 文本提取所有顶层标量 key-value ────────────────
const YAML_SKIP_KEYS = new Set([
  'name','version','symbols','symbol','category','type','description','strategy_type',
  'market_type','entry_signal','exit_signal','entry_conditions','exit_conditions',
  'filters','indicators','metadata','class','module','mode','contract','contracts',
  'tags','factors','market_filter','conditions',
])

// 需要解析嵌套值的 section header
const YAML_PARSE_SECTIONS = new Set(['risk','contract_specs','signal'])

// 动态参数分组 key 集合（用于 UI 分节显示）
const RISK_GROUP_KEYS = new Set(['daily_loss_limit_yuan','per_symbol_fuse_yuan','max_drawdown_pct','force_close_day','force_close_night','no_overnight','slippage_points','commission_rate','per_trade_stop_loss_pct','per_trade_take_profit_pct','atr_period','atr_filter_multiple','atr_stop_loss_multiple','atr_take_profit_multiple'])
const CONTRACT_GROUP_KEYS = new Set(['contract_size','min_price_move','price_per_tick','margin_ratio'])
const SIGNAL_GROUP_KEYS = new Set(['long_threshold','short_threshold','ema_periods','confirm_bars'])

function parseYamlScalars(yaml: string): Record<string, number | boolean | string> {
  const result: Record<string, number | boolean | string> = {}
  let currentSection = ''

  const storeValue = (key: string, rawVal: string) => {
    const v = rawVal.trim()
    if (v === '' || v === '|' || v === '>') return
    if (v === 'true') result[key] = true
    else if (v === 'false') result[key] = false
    else if (/^-?\d+(\.\d+)?$/.test(v)) result[key] = parseFloat(v)
    else if (/^['"](.*)['"]$/.test(v)) result[key] = v.slice(1, -1)
    else if (!v.startsWith('-') && !v.startsWith('[') && !v.startsWith('{')) result[key] = v
  }

  for (const line of yaml.split('\n')) {
    // 顶层节头（无缩进，冒号后无值）
    const secM = line.match(/^([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*$/)
    if (secM) {
      currentSection = YAML_PARSE_SECTIONS.has(secM[1]) ? secM[1] : '__skip__'
      continue
    }
    // 顶层 key-value（无缩进，冒号后有值）
    if (!/^\s/.test(line)) {
      currentSection = ''
      const m = line.match(/^([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.+)$/)
      if (!m) continue
      const key = m[1].trim()
      if (YAML_SKIP_KEYS.has(key)) continue
      storeValue(key, m[2])
      continue
    }
    // 一级嵌套 key-value（2个空格缩进，在允许解析的节下）
    if (currentSection && currentSection !== '__skip__') {
      const m = line.match(/^ {2}([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.+)$/)
      if (m) storeValue(m[1].trim(), m[2])
    }
  }
  return result
}

// ── 预设类型 ────────────────────────────────────────────────
type ParamPreset = {
  label: string
  desc: string
  color: string
  params: ParamValues
}
type ProductPresetItem = { name: string; params: ParamValues }

const MARKET_PRESETS: Record<string, ParamPreset> = {
  balanced: {
    label: "均衡标准",
    desc: "常规回测使用",
    color: "border-neutral-500 text-neutral-300",
    params: { positionSize: "35" },
  },
  trending: {
    label: "趋势行情",
    desc: "提高仓位参与单边行情",
    color: "border-blue-500 text-blue-300",
    params: { positionSize: "40" },
  },
  ranging: {
    label: "震荡行情",
    desc: "降低仓位控制频繁开平仓",
    color: "border-yellow-500 text-yellow-300",
    params: { positionSize: "25" },
  },
  high_vol: {
    label: "高波动",
    desc: "适当提高滑点假设并降低仓位",
    color: "border-red-500 text-red-300",
    params: { slippage: "2", positionSize: "20" },
  },
  low_vol: {
    label: "低波动",
    desc: "保持较低滑点与常规仓位",
    color: "border-green-500 text-green-300",
    params: { slippage: "0.5", positionSize: "30" },
  },
}

const PRODUCT_PRESETS: Record<string, ProductPresetItem[]> = {
  "常用品种": [
    { name: "棕榈油 P", params: { slippage: "2", commission: "0.03", positionSize: "35", minLotSize: "1" } },
    { name: "豆粕 M", params: { slippage: "1", commission: "0.03", positionSize: "30", minLotSize: "1" } },
    { name: "螺纹钢 RB", params: { slippage: "1", commission: "0.02", positionSize: "20", minLotSize: "1" } },
    { name: "铜 CU", params: { slippage: "10", commission: "0.03", positionSize: "20", minLotSize: "1" } },
    { name: "甲醇 MA", params: { slippage: "1", commission: "0.03", positionSize: "25", minLotSize: "1" } },
  ],
}

const SYMBOL_CODE_MAP: Record<string, string> = {
  p: "棕榈油 P",
  m: "豆粕 M",
  rb: "螺纹钢 RB",
  cu: "铜 CU",
  ma: "甲醇 MA",
}

function categoryToMarketKey(cat: string): string {
  const c = cat.toLowerCase()
  if (c.includes("reversal") || c.includes("oscillat") || c.includes("rang")) return "ranging"
  if (c.includes("trend") || c.includes("momentum")) return "trending"
  if (c.includes("high_vol") || c.includes("hf") || c.includes("high vol")) return "high_vol"
  if (c.includes("low_vol") || c.includes("lf")) return "low_vol"
  return "balanced"
}

function mapStatus(status: string): string {
  const m: Record<string, string> = {
    local: "待测试",
    running: "运行中",
    submitted: "运行中",
    completed: "已完成",
    done: "已完成",
    archived: "已归档",
    error: "错误",
  }
  return m[status] ?? status ?? "未知"
}

function fmtDate(ts: number): string {
  if (!ts) return "--"
  return new Date(ts * 1000).toLocaleDateString("zh-CN")
}

export default function StrategyManagementPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedStrategy, setSelectedStrategy] = useState<any>(null)
  const [importErrors, setImportErrors] = useState<string[]>([])
  const [importSuccess, setImportSuccess] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [apiError, setApiError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState(new Date())
  const [strategies, setStrategies] = useState<any[]>([])
  const [results, setResults] = useState<any[]>([])
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [editedParams, setEditedParams] = useState<Record<string, string>>({})
  const [isSavingParams, setIsSavingParams] = useState(false)
  const [paramSaveMsg, setParamSaveMsg] = useState<string | null>(null)
  const [backtestStart, setBacktestStart] = useState("2025-04-01")
  const [backtestEnd, setBacktestEnd] = useState("2026-04-01")
  const [backtestResults, setBacktestResults] = useState<any[]>([])
  const [mainContracts, setMainContracts] = useState<string[]>([])
  const [mainContractsNote, setMainContractsNote] = useState<string>("")
  const [selectedContract, setSelectedContract] = useState("")
  const [showRunPanel, setShowRunPanel] = useState(true)
  const [adjustedParams, setAdjustedParams] = useState<ParamValues>({})
  const [runParamMsg, setRunParamMsg] = useState<string | null>(null)
  const [activePreset, setActivePreset] = useState<string | null>(null)
  const [presetCategory, setPresetCategory] = useState(Object.keys(PRODUCT_PRESETS)[0])
  const [selectedStrategyForRun, setSelectedStrategyForRun] = useState<string>("")
  const [cancellingId, setCancellingId] = useState<string | null>(null)
  const [strategyMeta, setStrategyMeta] = useState<{ category: string; productName: string; yamlContract: string } | null>(null)
  const [progressMap, setProgressMap] = useState<Record<string, { progress: number; current_date: string | null }>>({})
  const [yamlEditorStrategy, setYamlEditorStrategy] = useState<string | null>(null)
  const [yamlContent, setYamlContent] = useState<string>("")
  const [yamlSaveMsg, setYamlSaveMsg] = useState<string | null>(null)
  const [isSavingYaml, setIsSavingYaml] = useState(false)
  const [selectedContracts, setSelectedContracts] = useState<string[]>([])
  const [contractInput, setContractInput] = useState("")
  const [contractSuggestions, setContractSuggestions] = useState<string[]>([])
  // ─── 新增状态 ──────────────────────────────────────────────────────
  // 从当前策略 YAML 解析出的全量参数（用于 KPI 框动态显示）
  const [strategyYamlParams, setStrategyYamlParams] = useState<Record<string, number | boolean | string>>({})
  // 批量并发上限（前端层）：限制每次同时提交给后端队列的任务数
  const [batchConcurrentLimit, setBatchConcurrentLimit] = useState<number>(8)
  // 已审批（保存到生产）策略列表
  const [approvedStrategies, setApprovedStrategies] = useState<Array<{ name: string; date: string; path: string }>>([])
  const [approveMsg, setApproveMsg] = useState<string | null>(null)
  const [isApprovingStrategy, setIsApprovingStrategy] = useState<string | null>(null)
  const [approveConfirmTarget, setApproveConfirmTarget] = useState<string | null>(null)
  // 回测回调异常提示
  const [anomalyBanner, setAnomalyBanner] = useState<string | null>(null)

  const fileInputRef = useRef<HTMLInputElement>(null)
  const multipleFileInputRef = useRef<HTMLInputElement>(null)
  const runPanelRef = useRef<HTMLDivElement>(null)

  // 初始化已审批策略列表
  useEffect(() => {
    setApprovedStrategies(getApprovedStrategies())
  }, [])

  const loadAll = async () => {
    setIsLoading(true)
    setApiError(null)
    try {
      const [strategiesData, resultsData, contractsData] = await Promise.allSettled([
        api.getStrategies(),
        api.getResults(),
        api.getMainContracts(),
      ])
      if (strategiesData.status === "fulfilled") {
        setStrategies(Array.isArray(strategiesData.value) ? strategiesData.value : [])
      } else {
        setApiError(api.friendlyError(strategiesData.reason))
      }
      if (resultsData.status === "fulfilled") {
        const arr = Array.isArray(resultsData.value) ? resultsData.value : []
        setResults(arr)
        setBacktestResults(arr)
      }
      if (contractsData.status === "fulfilled") {
        const arr = Array.isArray(contractsData.value?.contracts) ? contractsData.value.contracts : []
        setMainContracts(arr)
        const source = contractsData.value?.source ? `来源: ${contractsData.value.source}` : ""
        const note = contractsData.value?.note ? String(contractsData.value.note) : ""
        setMainContractsNote([source, note].filter(Boolean).join(" | "))
      }
      const now = new Date()
      setLastUpdate(now)
      try {
        window.dispatchEvent(new CustomEvent("backtest:lastUpdate", { detail: now.toISOString() }))
      } catch {}
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadAll()
    const onRefresh = () => loadAll()
    window.addEventListener("backtest:refresh", onRefresh)
    return () => window.removeEventListener("backtest:refresh", onRefresh)
  }, [])

  // 进度轮询：每 2 秒拉取 running 任务进度
  useEffect(() => {
    const runningTasks = results.filter((r) => r.status === "running" || r.status === "submitted" || r.status === "pending")
    if (runningTasks.length === 0) return
    const pollProgress = async () => {
      const updates: Record<string, { progress: number; current_date: string | null }> = {}
      let anyCompleted = false
      await Promise.allSettled(
        runningTasks.map(async (r: any) => {
          try {
            const p = await api.getProgress(r.id)
            updates[r.id] = { progress: p.progress ?? 0, current_date: p.current_date ?? null }
            if (p.status === "completed") anyCompleted = true
          } catch (_) {}
        })
      )
      setProgressMap((prev) => ({ ...prev, ...updates }))
      if (anyCompleted) {
        loadAll()
        // 完成/失败后检查是否存在异常
        await checkCompletedAnomalies()
      }
    }
    const timer = setInterval(pollProgress, 2000)
    return () => clearInterval(timer)
  }, [results])

  const stats = {
    total: strategies.length,
    running: results.filter((r) => r.status === "running" || r.status === "submitted").length,
    completed: results.filter((r) => r.status === "completed" || r.status === "done").length,
    pending: strategies.filter((s) => s.status === "local" || s.status === "pending").length,
  }

  const filteredStrategies = strategies.filter((s) =>
    (s.name || "").toLowerCase().includes(searchTerm.toLowerCase()),
  )

  const handleImportYAML = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    setIsLoading(true)
    const reader = new FileReader()
    reader.onload = async (e) => {
      try {
        const content = e.target?.result as string
        await api.importStrategy(file.name, content)
        setImportSuccess([`成功提交导入申请: ${file.name}`])
        setImportErrors([])
        setTimeout(() => loadAll(), 500)
      } catch (err) {
        setImportErrors([`导入失败: ${api.friendlyError(err)}`])
        setImportSuccess([])
      } finally {
        setIsLoading(false)
        if (fileInputRef.current) fileInputRef.current.value = ""
      }
    }
    reader.readAsText(file)
  }

  const handleBatchImport = (event: { target: { files: FileList } }) => {
    const files = event.target.files
    if (!files || files.length === 0) return
    setIsLoading(true)
    const uploads = Array.from(files)
      .filter((f) => f.name.endsWith(".yaml") || f.name.endsWith(".yml"))
      .map(
        (file) =>
          new Promise<{ ok: boolean; msg?: string }>((resolve) => {
            const reader = new FileReader()
            reader.onload = async (e) => {
              const content = e.target?.result as string
              try {
                await api.importStrategy(file.name, content)
                resolve({ ok: true })
              } catch (err) {
                resolve({ ok: false, msg: `${file.name}: ${api.friendlyError(err)}` })
              }
            }
            reader.readAsText(file)
          }),
      )

    Promise.all(uploads)
      .then((res) => {
        const ok = res.filter((r) => r.ok).length
        const errs = res.filter((r) => !r.ok).map((r) => r.msg as string)
        if (ok > 0) setImportSuccess([`成功提交 ${ok} 个导入请求`])
        if (errs.length > 0) setImportErrors(errs)
      })
      .finally(() => {
        if (multipleFileInputRef.current) multipleFileInputRef.current.value = ""
        setTimeout(() => loadAll(), 500)
      })
  }

  const handleRunBacktest = async (strategyName: string) => {
    try {
      setIsLoading(true)
      const resp = await api.runBacktest({ strategy_id: strategyName, start: backtestStart, end: backtestEnd })
      setImportSuccess([`回测已提交: ${resp.task_id ?? "任务已提交"}`])
      setTimeout(() => loadAll(), 800)
    } catch (err) {
      setApiError(api.friendlyError(err))
    } finally {
      setIsLoading(false)
    }
  }

  const handleSaveParamsAndRun = async (strategyNameOverride?: string) => {
    const name = strategyNameOverride ?? selectedStrategyForRun
    if (!name) {
      setRunParamMsg("请先在下方选择一个策略（点击策略名）")
      return
    }
    if (selectedContracts.length === 0 && !selectedContract) {
      const yamlSym = strategyMeta?.yamlContract
      if (yamlSym) {
        setRunParamMsg(`ℹ️ 未手动选择合约，将自动使用策略内置合约：${yamlSym}`)
      } else {
        setRunParamMsg("⚠️ 未选择合约，且策略 YAML 中未找到合约信息，可能导致0开仓")
      }
    }
    setIsLoading(true)
    try {
      // 全量传递 strategyYamlParams（含所有风控参数），后端按 YAML 执行
      const symbolsToUse = selectedContracts.length > 0 ? selectedContracts : (selectedContract ? [selectedContract] : undefined)
      const resp = await api.runBacktest({
        strategy_id: name,
        params: Object.fromEntries(
          Object.entries(strategyYamlParams).map(([k, v]) => [k, typeof v === 'string' ? (isNaN(Number(v)) ? v : Number(v)) : v])
        ),
        start: backtestStart,
        end: backtestEnd,
        symbols: symbolsToUse,
      })
      const msg = `✓ 已提交回测：${resp.task_id || "已提交"}（策略：${name}）`
      setRunParamMsg(msg)
      setImportSuccess([msg])
      setTimeout(() => loadAll(), 800)
    } catch (err) {
      setRunParamMsg(`提交失败：${api.friendlyError(err)}`)
      setApiError(api.friendlyError(err))
    } finally {
      setIsLoading(false)
    }
  }

  const handleBatchRunBacktest = async () => {
    if (selectedIds.size === 0) { setRunParamMsg("请先在策略列表中勾选要回测的策略"); return }
    setIsLoading(true)
    setRunParamMsg(null)
    try {
      // 批量回测：每个策略独立读取自己的 YAML 参数传入
      const names = Array.from(selectedIds)
      const symbolsToUse = selectedContracts.length > 0 ? selectedContracts : (selectedContract ? [selectedContract] : undefined)
      const limit = Math.max(1, Math.min(batchConcurrentLimit, names.length))
      let submitted = 0
      for (let i = 0; i < names.length; i += limit) {
        const chunk = names.slice(i, i + limit)
        await Promise.allSettled(chunk.map(async (stratName) => {
          try {
            // 每个策略单独拉取 YAML 解析参数，确保使用各自的风控设置
            const content = await exportStrategyContent(stratName)
            const yamlP = parseYamlScalars(content)
            const params = Object.fromEntries(
              Object.entries(yamlP).map(([k, v]) => [k, typeof v === 'string' ? (isNaN(Number(v)) ? v : Number(v)) : v])
            )
            await api.runBacktest({ strategy_id: stratName, params, start: backtestStart, end: backtestEnd, symbols: symbolsToUse })
          } catch (e) {
            console.warn(`[batch] ${stratName} 提交失败:`, e)
          }
        }))
        submitted += chunk.length
        setRunParamMsg(`⏳ 已提交 ${submitted}/${names.length}（批次上限 ${limit}）`)
      }
      setRunParamMsg(`✓ 已批量提交 ${names.length} 个回测任务（并发上限 ${limit}）`)
      setImportSuccess([`✓ 已批量提交 ${names.length} 个回测`])
      setTimeout(() => loadAll(), 800)
    } catch (err) {
      setRunParamMsg(`提交失败：${api.friendlyError(err)}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleContractInputChange = (val: string) => {
    setContractInput(val)
    if (!val.trim()) { setContractSuggestions([]); return }
    const lower = val.toLowerCase()
    const matched = mainContracts.filter((c) => c.toLowerCase().includes(lower)).slice(0, 8)
    setContractSuggestions(matched)
  }

  const addContract = (c: string) => {
    const sym = c.trim()
    if (sym && !selectedContracts.includes(sym)) {
      setSelectedContracts((prev) => [...prev, sym])
    }
    setContractInput("")
    setContractSuggestions([])
  }

  const removeContract = (c: string) => setSelectedContracts((prev) => prev.filter((x) => x !== c))

  // 品种分组预设
  const PRODUCT_GROUPS: Record<string, string[]> = {
    "油脂类": ["DCE.P", "DCE.Y", "DCE.OI", "CZCE.OI"],
    "农产品": ["DCE.C", "DCE.CS", "DCE.A", "DCE.B", "DCE.M", "CZCE.SR", "CZCE.CF", "CZCE.CJ"],
    "有色金属": ["SHFE.CU", "SHFE.AL", "SHFE.ZN", "SHFE.NI", "SHFE.SN", "SHFE.PB"],
    "黑色系": ["DCE.I", "SHFE.RB", "SHFE.HC", "DCE.J", "DCE.JM"],
    "能源化工": ["SHFE.FU", "SHFE.SC", "DCE.L", "DCE.PP", "DCE.V", "CZCE.MA", "CZCE.TA"],
  }

  const addProductGroup = (groupKey: string) => {
    const prefixes = PRODUCT_GROUPS[groupKey] || []
    const matched = mainContracts.filter((c) => prefixes.some((p) => c.toUpperCase().startsWith(p.toUpperCase())))
    const toAdd = matched.filter((c) => !selectedContracts.includes(c))
    if (toAdd.length > 0) setSelectedContracts((prev) => [...prev, ...toAdd])
  }

  const applyPreset = (params: ParamValues, key: string) => {
    // 预设仅更新展示用的 adjustedParams，不影响strategyYamlParams（回测时从 YAML 取全量）
    setAdjustedParams((p) => ({ ...p, ...params }))
    setActivePreset(key)
  }

  // 智能预设：根据策略 YAML 自动识别品种 + 行情类型，一键应用最匹配的预设
  // 同时解析 YAML 全量参数，填充 KPI 参数展示框
  const autoApplyPresetForStrategy = async (stratName: string) => {
    try {
      const content = await exportStrategyContent(stratName)

      // ─── 解析 YAML 全量参数（供 KPI 框展示 + 自动回填）────────────
      const allScalars = parseYamlScalars(content)
      setStrategyYamlParams(allScalars)

      // 不再单独维护 adjustedParams —— YAML 全量参数直接存在 strategyYamlParams 中回测时整体传入

      // 解析 category
      const catMatch = content.match(/^category:\s*(.+)/m)
      const cat = (catMatch?.[1] ?? "").trim()

      // 解析第一个合约（支持列表/单行/KQ格式）
      const symMatch =
        content.match(/^symbols:\s*\n\s*-\s*(\S+)/m) ||
        content.match(/^symbols:\s*\[([^\],]+)/m) ||
        content.match(/^symbol:\s*(\S+)/m)
      const rawSym = (symMatch?.[1] ?? "").trim()

      // 提取品种代码（小写）
      let productCode = ""
      const kqMatch = rawSym.match(/KQ\.m@\w+\.([A-Za-z]+)/i)
      const dotMatch = rawSym.match(/[A-Z]+\.([A-Za-z]+)\d*/i)
      const bareMatch = rawSym.match(/^([A-Za-z]+)\d*$/)
      if (kqMatch) productCode = kqMatch[1].toLowerCase()
      else if (dotMatch) productCode = dotMatch[1].toLowerCase()
      else if (bareMatch) productCode = bareMatch[1].toLowerCase()

      // 匹配品种预设
      const productName = SYMBOL_CODE_MAP[productCode] ?? null
      let productPreset: ProductPresetItem | null = null
      if (productName) {
        for (const items of Object.values(PRODUCT_PRESETS)) {
          const found = items.find((p) => p.name === productName)
          if (found) { productPreset = found; break }
        }
      }

      // 确定分类对应的品种 tab
      if (productName) {
        for (const [catKey, items] of Object.entries(PRODUCT_PRESETS)) {
          if (items.find((p) => p.name === productName)) {
            setPresetCategory(catKey)
            break
          }
        }
      }

      setStrategyMeta({ category: cat, productName: productName ?? "", yamlContract: rawSym })

      // 自动填入 YAML 合约到合约选择框
      if (rawSym) {
        setSelectedContracts([rawSym])
      }

      if (productPreset) {
        applyPreset(productPreset.params, productPreset.name)
      } else {
        const mKey = categoryToMarketKey(cat)
        const mPreset = MARKET_PRESETS[mKey] ?? MARKET_PRESETS.balanced
        applyPreset(mPreset.params, mKey)
      }
    } catch {
      // 静默失败，不影响主流程
    }
  }

  // ─── 策略审批：保存到生产文件夹 ────────────────────────────────────
  const handleApproveStrategy = async (strategyName: string) => {
    setIsApprovingStrategy(strategyName)
    setApproveMsg(null)
    try {
      const lastResult = strategyLastResult(strategyName)
      if (!lastResult || (lastResult.status !== 'completed' && lastResult.status !== 'done')) {
        setApproveMsg(`⚠️ 策略 ${strategyName} 尚无已完成的回测，无法保存到生产`)
        return
      }
      const yamlContent = await exportStrategyContent(strategyName)
      const meta = {
        resultId: lastResult.id,
        totalReturn: lastResult.totalReturn,
        sharpeRatio: lastResult.sharpeRatio,
      }
      const { date, path } = approveStrategyLocal(strategyName, yamlContent, meta)
      const updated = getApprovedStrategies()
      setApprovedStrategies(updated)
      setApproveMsg(`✓ 已保存到生产 (${date})，文件已下载 → 请放入：services/decision/approved_strategies/${date}/`)
      setImportSuccess([`✓ 策略 ${strategyName} 已审批保存 (${date})`])
    } catch (err) {
      setApproveMsg(`保存失败：${api.friendlyError(err)}`)
    } finally {
      setIsApprovingStrategy(null)
      setTimeout(() => setApproveMsg(null), 8000)
    }
  }

  const handleRevokeStrategy = (strategyName: string) => {
    revokeApprovedStrategy(strategyName)
    setApprovedStrategies(getApprovedStrategies())
    setApproveMsg(`已撤销：${strategyName} 已从审批列表移除`)
    setTimeout(() => setApproveMsg(null), 4000)
  }

  // ─── 回测完成后检查异常 ──────────────────────────────────────────
  const checkCompletedAnomalies = async () => {
    try {
      const latest = await api.getResults()
      const recent = Array.isArray(latest) ? latest.slice(0, 5) : []
      const anomalies: string[] = []
      for (const r of recent) {
        if (r.status === 'failed') {
          anomalies.push(`策略 ${r.strategy ?? r.name ?? r.id} 回测失败：${String(r.error_message ?? '未知错误').split('\n')[0]}`)
        } else if (r.status === 'completed' && (r.totalTrades === 0 || r.total_trades === 0)) {
          anomalies.push(`策略 ${r.strategy ?? r.name ?? r.id} 回测完成但零成交！请检查合约与策略信号配置`)
        }
      }
      if (anomalies.length > 0) {
        setAnomalyBanner(anomalies.join('\n'))
        setTimeout(() => setAnomalyBanner(null), 15000)
      }
    } catch (_) {}
  }

  const handleOpenYamlEditor = async (name: string) => {
    try {
      const content = await exportStrategyContent(name)
      setYamlContent(content)
      setYamlEditorStrategy(name)
      setYamlSaveMsg(null)
    } catch (err) {
      setApiError(api.friendlyError(err))
    }
  }

  const handleSaveYaml = async () => {
    if (!yamlEditorStrategy) return
    setIsSavingYaml(true)
    setYamlSaveMsg(null)
    try {
      await api.importStrategy(yamlEditorStrategy, yamlContent)
      setYamlSaveMsg("✓ 保存成功")
      setTimeout(() => loadAll(), 400)
    } catch (err) {
      setYamlSaveMsg(`保存失败: ${api.friendlyError(err)}`)
    } finally {
      setIsSavingYaml(false)
    }
  }

  const handleBatchDeleteStrategies = async () => {
    if (!confirm(`确定批量删除 ${selectedIds.size} 条策略？`)) return
    setIsLoading(true)
    try {
      const names = Array.from(selectedIds)
      await Promise.allSettled(names.map((n) => deleteStrategy(n)))
      setSelectedIds(new Set())
      setImportSuccess([`已批量删除 ${names.length} 条策略`])
      setTimeout(() => loadAll(), 400)
    } catch (err) {
      setApiError(api.friendlyError(err))
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    const label = mapStatus(status)
    switch (label) {
      case "运行中":
        return "bg-blue-500/20 text-blue-300"
      case "待测试":
        return "bg-neutral-600/20 text-neutral-300"
      case "已完成":
        return "bg-green-700/20 text-green-400"
      case "已归档":
        return "bg-neutral-700/20 text-neutral-500"
      case "错误":
        return "bg-red-700/20 text-red-400"
      default:
        return "bg-gray-600/20 text-gray-400"
    }
  }

  // 找出每个策略最新一次回测状态
  const strategyLastResult = (name: string) => {
    const matches = results.filter(
      (r) => r.strategy === name || r.payload?.strategy?.id === name || r.name === name
    )
    if (matches.length === 0) return null
    return matches.sort((a: any, b: any) => (b.submitted_at ?? 0) - (a.submitted_at ?? 0))[0]
  }

  const getStrategyDisplayStatus = (s: any) => {
    const lastResult = strategyLastResult(s.name)
    if (!lastResult) return s.status // 从未测试
    return lastResult.status
  }
  const rawParams = selectedStrategy?.params ?? selectedStrategy?.strategy?.params ?? null
  const editableEntries =
    rawParams && typeof rawParams === "object"
      ? Object.entries(rawParams).filter(
          ([, v]) => typeof v === "number" || (typeof v === "string" && !isNaN(Number(v))),
        )
      : []

  return (
    <div className="p-6 space-y-6">

      {/* ─── 异常横幅 ────────────────────────────────────── */}
      {anomalyBanner && (
        <div className="bg-red-900/30 border border-red-600/60 rounded-lg p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-semibold text-red-300 mb-1">⚠️ 回测异常提示 / Backtest Anomaly Detected</p>
            {anomalyBanner.split('\n').map((msg, i) => (
              <p key={i} className="text-xs text-red-400 mt-0.5">{msg}</p>
            ))}
          </div>
          <button onClick={() => setAnomalyBanner(null)} className="text-neutral-500 hover:text-neutral-300 text-xs">✕</button>
        </div>
      )}

      {/* ─── 审批结果提示 ─────────────────────────────────── */}
      {approveMsg && (
        <div className={`border rounded-lg p-3 text-sm ${approveMsg.startsWith('✓') ? 'bg-emerald-900/20 border-emerald-600/50 text-emerald-300' : 'bg-amber-900/20 border-amber-600/50 text-amber-300'}`}>
          {approveMsg}
        </div>
      )}

        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-wider">策略管理</h1>
            <p className="text-sm text-neutral-400">导入、编辑和管理交易策略</p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => fileInputRef.current?.click()}
              className="bg-orange-500 hover:bg-orange-600 text-white"
              disabled={isLoading}
            >
              <Upload className="w-4 h-4 mr-2" />单个导入
            </Button>
            <Button
              onClick={() => multipleFileInputRef.current?.click()}
              className="bg-orange-500 hover:bg-orange-600 text-white"
              disabled={isLoading}
            >
              <Upload className="w-4 h-4 mr-2" />批量导入
            </Button>
            {selectedIds.size > 0 && (
              <Button className="bg-red-700 hover:bg-red-800 text-white" disabled={isLoading} onClick={handleBatchDeleteStrategies}>
                <Trash2 className="w-4 h-4 mr-2" />批量删除 ({selectedIds.size})
              </Button>
            )}
            <input ref={fileInputRef} type="file" accept=".yaml,.yml" onChange={handleImportYAML} className="hidden" />
            <input
              ref={multipleFileInputRef}
              type="file"
              accept=".yaml,.yml"
              multiple
              onChange={(e) => handleBatchImport({ target: { files: e.target.files as FileList } })}
              className="hidden"
            />
          </div>
        </div>

      {apiError && <div className="text-sm text-red-400 bg-neutral-900 border border-red-800 p-3 rounded">API 错误: {apiError}</div>}

      {importSuccess.length > 0 && (
        <Card className="bg-green-900/20 border-green-600/50">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" />
              <div>{importSuccess.map((msg, i) => <p key={i} className="text-sm text-green-300">{msg}</p>)}</div>
            </div>
          </CardContent>
        </Card>
      )}

      {importErrors.length > 0 && (
        <Card className="bg-red-900/20 border-red-600/50">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <XCircle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
              <div>{importErrors.map((msg, i) => <p key={i} className="text-sm text-red-300">{msg}</p>)}</div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "策略总数", value: stats.total, icon: <FileText className="w-5 h-5 text-orange-400" />, color: "text-orange-400" },
          { label: "运行中", value: stats.running, icon: <Activity className="w-5 h-5 text-blue-400" />, color: "text-blue-400" },
          { label: "已完成", value: stats.completed, icon: <CheckCircle className="w-5 h-5 text-green-400" />, color: "text-green-400" },
          { label: "待测试", value: stats.pending, icon: <Clock className="w-5 h-5 text-neutral-400" />, color: "text-neutral-300" },
        ].map(({ label, value, icon, color }) => (
          <Card key={label} className="bg-neutral-900 border-neutral-700">
            <CardContent className="p-4 flex items-center gap-3">
              {icon}
              <div>
                <p className="text-xs text-neutral-400">{label}</p>
                <p className={`text-2xl font-bold ${color}`}>{isLoading ? "—" : value}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 回测参数调整面板 */}
      <div ref={runPanelRef}>
      <Card className={`border-2 ${showRunPanel ? "bg-neutral-900 border-orange-600/40" : "bg-neutral-900 border-neutral-700"}`}>
        <CardHeader className="cursor-pointer pb-3" onClick={() => setShowRunPanel(!showRunPanel)}>
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-orange-400 tracking-wider flex items-center gap-2">
              <Settings className="w-4 h-4" />
              回测参数调整
            </CardTitle>
            <span className="text-xs text-neutral-500">{showRunPanel ? "▲ 收起" : "▼ 展开"}</span>
          </div>
        </CardHeader>
        {showRunPanel && (
          <CardContent className="space-y-5">
            {/* 策略选择提示 */}
            <div className="bg-neutral-800 rounded p-3 flex items-center gap-3 flex-wrap">
              <span className="text-xs text-neutral-400">当前策略：</span>
              {selectedStrategyForRun ? (
                <span className="text-sm text-orange-400 font-mono">{selectedStrategyForRun}</span>
              ) : (
                <span className="text-xs text-neutral-600">请在下方策略列表中点击一行以选择</span>
              )}
              {strategyMeta && selectedStrategyForRun && (
                <div className="flex items-center gap-1.5 ml-1">
                  {strategyMeta.productName && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/15 text-blue-300 border border-blue-500/30">
                      📦 {strategyMeta.productName}
                    </span>
                  )}
                  {strategyMeta.category && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-purple-500/15 text-purple-300 border border-purple-500/30">
                      {strategyMeta.category.includes("reversal") || strategyMeta.category.includes("oscillat") ? "↔ 反转/震荡"
                        : strategyMeta.category.includes("trend") || strategyMeta.category.includes("momentum") ? "↗ 趋势"
                        : strategyMeta.category}
                    </span>
                  )}
                </div>
              )}
              {selectedStrategyForRun && (
                <button className="ml-auto text-xs text-neutral-500 hover:text-red-400" onClick={() => { setSelectedStrategyForRun(""); setStrategyMeta(null) }}>清除</button>
              )}
            </div>

            {/* 行情预设 + 品种预设 */}
            <div className="border border-neutral-700 rounded-lg p-4 bg-neutral-800/50 space-y-4">
              {/* 标题 */}
              <div className="flex items-center justify-between border-b border-neutral-700/60 pb-2">
                <span className="text-sm font-medium text-neutral-300">快速预设</span>
                {activePreset && (
                  <span className="text-xs text-orange-400 bg-orange-500/10 border border-orange-500/30 px-2 py-0.5 rounded">
                    已应用：{activePreset}
                  </span>
                )}
              </div>

              {/* 行情预设 */}
              <div>
                <p className="text-xs text-neutral-500 mb-2">行情类型</p>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(MARKET_PRESETS).map(([key, p]) => (
                    <button
                      key={key}
                      title={p.desc}
                      onClick={() => applyPreset(p.params, key)}
                      className={`text-sm px-4 py-1.5 rounded-md border transition-all ${p.color} ${
                        activePreset === key
                          ? "ring-2 ring-orange-400 bg-orange-500/10 shadow-[0_0_8px_rgba(251,146,60,0.3)]"
                          : "bg-neutral-800 hover:bg-neutral-700 hover:border-neutral-500"
                      }`}
                    >
                      <span className="font-medium">{p.label}</span>
                      <span className="ml-1.5 text-xs opacity-60">{p.desc}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* 品种预设 */}
              <div>
                <p className="text-xs text-neutral-500 mb-2">品种专属</p>
                {/* 分类 tabs */}
                <div className="flex flex-wrap gap-1.5 mb-3">
                  {Object.keys(PRODUCT_PRESETS).map((cat) => (
                    <button
                      key={cat}
                      onClick={() => setPresetCategory(cat)}
                      className={`text-xs px-3 py-1 rounded-md font-medium transition-colors ${
                        presetCategory === cat
                          ? "bg-orange-500/20 text-orange-300 border border-orange-500/50"
                          : "bg-neutral-800 text-neutral-500 hover:text-neutral-300 border border-neutral-700 hover:border-neutral-500"
                      }`}
                    >
                      {cat}
                    </button>
                  ))}
                </div>
                {/* 当前分类的品种 */}
                <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-7 gap-2">
                  {(PRODUCT_PRESETS[presetCategory] ?? []).map((p) => (
                    <button
                      key={p.name}
                      onClick={() => applyPreset(p.params, p.name)}
                      className={`text-xs px-2 py-2 rounded-md border text-center transition-all ${
                        activePreset === p.name
                          ? "border-orange-400 text-orange-300 bg-orange-500/10 ring-1 ring-orange-400/50"
                          : "border-neutral-700 text-neutral-400 hover:border-neutral-500 hover:text-neutral-200 hover:bg-neutral-700/50"
                      }`}
                    >
                      {p.name}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* ─── 并发控制 ─────────────────────────────────────── */}
            <div className="border border-neutral-700/50 rounded-lg p-3 bg-neutral-800/30 flex items-center gap-4 flex-wrap">
              <Zap className="w-4 h-4 text-yellow-400 flex-shrink-0" />
              <div>
                <span className="text-xs text-neutral-400">并发上限 / Batch Concurrency:</span>
                <span className="text-xs text-yellow-400 ml-1">后端队列容量 8 slots（BACKTEST_MAX_CONCURRENT）</span>
              </div>
              <div className="flex items-center gap-2 ml-auto">
                <label className="text-xs text-neutral-400">批量提交上限</label>
                <select
                  value={batchConcurrentLimit}
                  onChange={(e) => setBatchConcurrentLimit(Number(e.target.value))}
                  className="bg-neutral-800 border border-neutral-600 text-white text-xs rounded px-2 py-1"
                >
                  {[1,2,3,4,5,6,8,10,15,20].map(n => (
                    <option key={n} value={n}>{n} 个/批</option>
                  ))}
                </select>
              </div>
            </div>

            {/* ─── 策略专属参数（从 YAML 解析，动态渲染 + 双语注释）──── */}
            {selectedStrategyForRun && Object.keys(strategyYamlParams).length > 0 && (() => {
              const extraEntries = Object.entries(strategyYamlParams)
              if (extraEntries.length === 0) return null

              // 按 section 分组
              const klineEntries    = extraEntries.filter(([k]) => !RISK_GROUP_KEYS.has(k) && !CONTRACT_GROUP_KEYS.has(k) && !SIGNAL_GROUP_KEYS.has(k))
              const riskEntries     = extraEntries.filter(([k]) => RISK_GROUP_KEYS.has(k))
              const contractEntries = extraEntries.filter(([k]) => CONTRACT_GROUP_KEYS.has(k))
              const signalEntries   = extraEntries.filter(([k]) => SIGNAL_GROUP_KEYS.has(k))

              const renderParamGrid = (entries: typeof extraEntries, colorClass?: string) => (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                  {entries.map(([key, val]) => {
                    const label = PARAM_BILINGUAL[key as keyof typeof PARAM_BILINGUAL]
                    const isRisk = RISK_GROUP_KEYS.has(key)
                    const borderCls = isRisk ? 'border border-amber-700/40 rounded p-2 bg-amber-900/10' : ''
                    return (
                      <div key={key} className={borderCls}>
                        <label className="text-xs block mb-0.5">
                          {label ? (
                            <span className={isRisk ? 'text-amber-300' : (colorClass ?? 'text-neutral-400')}>
                              {label.zh} <span className="text-neutral-600 font-normal">/ {label.en}</span>
                              {label.unit && <span className="text-neutral-600"> ({label.unit})</span>}
                              {isRisk && <span className="text-amber-500 ml-1">🛡</span>}
                            </span>
                          ) : (
                            <span className="text-neutral-500 font-mono">{key}</span>
                          )}
                        </label>
                        <Input
                          type="text"
                          inputMode="decimal"
                          value={String(strategyYamlParams[key] ?? val)}
                          onChange={(e) => setStrategyYamlParams((prev) => ({ ...prev, [key]: e.target.value }))}
                          className={`text-xs ${isRisk ? 'bg-amber-900/20 border-amber-700 text-amber-200' : 'bg-neutral-800 border-neutral-600 text-white'}`}
                        />
                        {label && <p className="text-[10px] text-neutral-600 mt-0.5 leading-tight">{label.desc}</p>}
                      </div>
                    )
                  })}
                </div>
              )

              return (
                <div className="space-y-4">
                  <p className="text-xs text-neutral-500 border-b border-neutral-700 pb-1">
                    策略专属参数 / Strategy-Specific Parameters
                    <span className="ml-2 text-neutral-600">（手动修改后将覆盖 YAML 设置）</span>
                  </p>
                  {klineEntries.length > 0 && (
                    <div>
                      <p className="text-[11px] text-blue-400/80 mb-2 font-medium">📊 K线 / 时序参数</p>
                      {renderParamGrid(klineEntries, 'text-blue-300')}
                    </div>
                  )}
                  {signalEntries.length > 0 && (
                    <div>
                      <p className="text-[11px] text-purple-400/80 mb-2 font-medium">📡 信号参数</p>
                      {renderParamGrid(signalEntries, 'text-purple-300')}
                    </div>
                  )}
                  {riskEntries.length > 0 && (
                    <div>
                      <p className="text-[11px] text-amber-400/80 mb-2 font-medium">🛡 风控参数（严格按 YAML 执行，修改须谨慎）</p>
                      {renderParamGrid(riskEntries)}
                    </div>
                  )}
                  {contractEntries.length > 0 && (
                    <div>
                      <p className="text-[11px] text-cyan-400/80 mb-2 font-medium">📋 合约规格</p>
                      {renderParamGrid(contractEntries, 'text-cyan-300')}
                    </div>
                  )}
                </div>
              )
            })()}

            {/* ─── 合约选择（支持多选 + 自动补全 + 品种分组）──────────── */}
            <div>
              <p className="text-xs text-neutral-500 mb-3 border-b border-neutral-700 pb-1">合约选择（多选）</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-neutral-400 block mb-1">输入合约代码（自动补全）</label>
                  <div className="relative">
                    <Input
                      value={contractInput}
                      onChange={(e) => handleContractInputChange(e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter' && contractInput) addContract(contractInput) }}
                      placeholder="输入 p 自动提示 p2605…"
                      className="bg-neutral-800 border-neutral-600 text-white font-mono"
                    />
                    {contractSuggestions.length > 0 && (
                      <div className="absolute top-full left-0 right-0 bg-neutral-800 border border-neutral-600 rounded-b z-10 max-h-36 overflow-y-auto">
                        {contractSuggestions.map((c) => (
                          <div key={c} className="px-3 py-1.5 text-xs text-white cursor-pointer hover:bg-neutral-700 font-mono" onClick={() => addContract(c)}>{c}</div>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="mt-2">
                    <p className="text-xs text-neutral-500 mb-1">按品种批量添加：</p>
                    <div className="flex flex-wrap gap-1">
                      {Object.keys(PRODUCT_GROUPS).map((g) => (
                        <button key={g} onClick={() => addProductGroup(g)} className="text-xs px-2 py-0.5 bg-neutral-700 hover:bg-neutral-600 text-neutral-300 rounded">
                          {g}
                        </button>
                      ))}
                      {mainContracts.length > 0 && (
                        <button onClick={() => setSelectedContracts(mainContracts.slice(0, 20))} className="text-xs px-2 py-0.5 bg-neutral-700 hover:bg-neutral-600 text-neutral-300 rounded">
                          全部主力
                        </button>
                      )}
                    </div>
                  </div>
                </div>
                <div>
                  <label className="text-xs text-neutral-400 block mb-1">已选合约 ({selectedContracts.length})</label>
                  {selectedContracts.length === 0 ? (
                    <div className="text-xs bg-neutral-800 rounded p-3 border border-neutral-700">
                      {strategyMeta?.yamlContract ? (
                        <span className="text-blue-400/80">
                          📄 YAML 内置合约：<span className="font-mono text-blue-300">{strategyMeta.yamlContract}</span>
                          <span className="text-neutral-500 ml-1">（可在上方输入框覆盖）</span>
                        </span>
                      ) : (
                        <span className="text-neutral-600">留空则按策略 YAML 配置；添加合约后将覆盖策略合约设置</span>
                      )}
                    </div>
                  ) : (
                    <div className="flex flex-wrap gap-1 bg-neutral-800 rounded p-2 border border-neutral-700 min-h-[60px] max-h-28 overflow-y-auto">
                      {selectedContracts.map((c) => {
                        const isFromYaml = strategyMeta?.yamlContract === c
                        return (
                          <span key={c} className={`flex items-center gap-1 text-xs px-2 py-0.5 rounded font-mono ${isFromYaml ? "bg-blue-500/20 text-blue-300" : "bg-orange-500/20 text-orange-300"}`}>
                            {isFromYaml && <span className="text-blue-500/70 text-[10px]">YAML</span>}
                            {c}
                            <button onClick={() => removeContract(c)} className="text-neutral-500 hover:text-red-400 ml-0.5">×</button>
                          </span>
                        )
                      })}
                    </div>
                  )}
                  {selectedContracts.length > 0 && (
                    <button onClick={() => setSelectedContracts([])} className="text-xs text-neutral-500 hover:text-red-400 mt-1">清空</button>
                  )}
                </div>
              </div>
            </div>

            {/* 日期 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-neutral-400 block mb-1">回测开始日期</label>
                <Input type="date" value={backtestStart} onChange={(e) => setBacktestStart(e.target.value)}
                  className="bg-neutral-800 border-neutral-600 text-white" />
              </div>
              <div>
                <label className="text-xs text-neutral-400 block mb-1">回测结束日期</label>
                <Input type="date" value={backtestEnd} onChange={(e) => setBacktestEnd(e.target.value)}
                  className="bg-neutral-800 border-neutral-600 text-white" />
              </div>
            </div>

            {/* 操作按钮 */}
            <div className="flex gap-3 pt-1 flex-wrap">
              <Button onClick={() => handleSaveParamsAndRun()} className="bg-orange-500 hover:bg-orange-600 text-white flex-1 min-w-[160px]" disabled={isLoading || !selectedStrategyForRun}>
                <Play className="w-4 h-4 mr-2" />回测当前策略
              </Button>
              <Button onClick={handleBatchRunBacktest} className="bg-blue-600 hover:bg-blue-700 text-white flex-1 min-w-[160px]" disabled={isLoading || selectedIds.size === 0}>
                <Play className="w-4 h-4 mr-2" />批量回测已选 ({selectedIds.size})
              </Button>

            </div>
            {runParamMsg && (
              <p className={`text-xs ${runParamMsg?.startsWith("✓") ? "text-green-400" : "text-red-400"}`}>
                {runParamMsg}
              </p>
            )}
          </CardContent>
        )}
      </Card>
      </div>

      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">策略列表 ({filteredStrategies.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 mb-4">
            <div className="relative flex-1 max-w-xs">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400" />
              <Input
                placeholder="搜索策略名称..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 bg-neutral-800 border-neutral-600 text-white placeholder-neutral-400"
              />
            </div>
            <p className="text-xs text-neutral-500">更新于: {lastUpdate.toLocaleTimeString("zh-CN")}</p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-neutral-700">
                  <th className="py-3 px-4 w-10">
                    <input
                      type="checkbox"
                      className="accent-orange-500"
                      checked={filteredStrategies.length > 0 && selectedIds.size === filteredStrategies.length}
                      onChange={(e) => {
                        if (e.target.checked) setSelectedIds(new Set(filteredStrategies.map((s) => s.name)))
                        else setSelectedIds(new Set())
                      }}
                    />
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400 tracking-wider">文件名</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400 tracking-wider">状态</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400 tracking-wider">最新回测</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400 tracking-wider">最新收益</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400 tracking-wider">创建时间</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400 tracking-wider">大小 (KB)</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400 tracking-wider">操作</th>
                </tr>
              </thead>
              <tbody>
                {filteredStrategies.length > 0 ? (
                  filteredStrategies.map((s, i) => (
                    <tr
                      key={s.name ?? i}
                      className={`border-b border-neutral-800 hover:bg-neutral-800 cursor-pointer ${selectedIds.has(s.name) ? "bg-orange-900/20" : ""}`}
                      onClick={() => {
                        setSelectedStrategyForRun(s.name)
                        setEditedParams({})
                        setParamSaveMsg(null)
                        setShowRunPanel(true)
                        autoApplyPresetForStrategy(s.name)
                        setTimeout(() => runPanelRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 50)
                      }}
                    >
                      <td className="py-3 px-4 w-10" onClick={(e) => e.stopPropagation()}>
                        <input
                          type="checkbox"
                          className="accent-orange-500"
                          checked={selectedIds.has(s.name)}
                          onChange={(e) => {
                            const next = new Set(selectedIds)
                            if (e.target.checked) next.add(s.name)
                            else next.delete(s.name)
                            setSelectedIds(next)
                          }}
                        />
                      </td>
                      <td className="py-3 px-4 text-sm text-white font-mono">{s.name ?? "--"}</td>
                      <td className="py-3 px-4">
                        {(() => {
                          // 找到与该策略关联的 running 任务
                          const runningTask = results.find(
                            (r) =>
                              (r.status === "running" || r.status === "submitted" || r.status === "pending") &&
                              (r.strategy === s.name || r.payload?.strategy?.id === s.name || r.name === s.name)
                          )
                          const prog = runningTask ? progressMap[runningTask.id] : null
                          if (runningTask && prog != null) {
                            return (
                              <div className="min-w-[110px]">
                                <div className="flex items-center justify-between mb-1">
                                  <span className="text-xs text-orange-400 font-mono">{prog.progress}%</span>
                                  {prog.current_date && (
                                    <span className="text-xs text-neutral-500 ml-1">{prog.current_date}</span>
                                  )}
                                  <button
                                    disabled={cancellingId === runningTask.id}
                                    onClick={async () => {
                                      setCancellingId(runningTask.id)
                                      try { await api.cancelBacktest(runningTask.id) } catch {}
                                      setTimeout(() => { setCancellingId(null); loadAll() }, 800)
                                    }}
                                    className="text-xs text-red-400 hover:text-red-300 disabled:opacity-50 ml-2 flex items-center gap-0.5"
                                    title="终止回测"
                                  >
                                    ■ {cancellingId === runningTask.id ? "终止中…" : "终止"}
                                  </button>
                                </div>
                                <div className="h-1.5 w-full bg-neutral-700 rounded-full overflow-hidden">
                                  <div
                                    className="h-full bg-orange-500 rounded-full transition-all duration-500"
                                    style={{ width: `${prog.progress}%` }}
                                  />
                                </div>
                              </div>
                            )
                          }
                          const displayStatus = getStrategyDisplayStatus(s)
                          return (
                            <span className={`text-xs px-2 py-1 rounded tracking-wider ${getStatusColor(displayStatus)}`}>
                              {mapStatus(displayStatus)}
                            </span>
                          )
                        })()}
                      </td>
                      <td className="py-3 px-4 text-xs text-neutral-400">
                        {(() => {
                          const last = strategyLastResult(s.name)
                          if (!last) return <span className="text-neutral-600">—</span>
                          const d = last.submitted_at ? new Date(last.submitted_at * 1000) : null
                          return d ? d.toLocaleDateString("zh-CN") + " " + d.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" }) : "—"
                        })()}
                      </td>
                      <td className="py-3 px-4 text-xs font-mono">
                        {(() => {
                          const last = strategyLastResult(s.name)
                          if (!last) return <span className="text-neutral-600">—</span>
                          const ret = last.totalReturn ?? last.total_return
                          if (ret == null) return <span className="text-neutral-600">—</span>
                          const color = ret >= 0 ? "text-green-400" : "text-red-400"
                          return <span className={color}>{ret >= 0 ? "+" : ""}{typeof ret === "number" ? ret.toFixed(2) : ret}%</span>
                        })()}
                      </td>
                      <td className="py-3 px-4 text-sm text-neutral-300">{fmtDate(s.created_at)}</td>
                      <td className="py-3 px-4 text-sm text-neutral-300 font-mono">{s.size != null ? (s.size / 1024).toFixed(1) : "--"}</td>
                      <td className="py-3 px-4">
                        <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
                          <Button variant="ghost" size="icon" className="text-neutral-400 hover:text-purple-400 h-8 w-8" title="编辑 YAML" onClick={() => handleOpenYamlEditor(s.name)}>
                            <FileText className="w-4 h-4" />
                          </Button>
                          <Button variant="ghost" size="icon" className="text-neutral-400 hover:text-blue-400 h-8 w-8" title="用当前面板参数快速回测" onClick={(e) => { e.stopPropagation(); setSelectedStrategyForRun(s.name); autoApplyPresetForStrategy(s.name); handleSaveParamsAndRun(s.name) }}>
                            <Play className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-neutral-400 hover:text-green-400 h-8 w-8"
                            title="导出 YAML"
                            onClick={async () => {
                              try {
                                const content = await exportStrategyContent(s.name)
                                const blob = new Blob([content], { type: "text/yaml" })
                                const url = URL.createObjectURL(blob)
                                const a = document.createElement("a")
                                a.href = url
                                a.download = s.name
                                a.click()
                                URL.revokeObjectURL(url)
                              } catch (err) {
                                setApiError(api.friendlyError(err))
                              }
                            }}
                          >
                            <Download className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-neutral-400 hover:text-red-400 h-8 w-8"
                            title="删除策略"
                            onClick={async () => {
                              if (!confirm(`确定删除策略 ${s.name}？`)) return
                              try {
                                setIsLoading(true)
                                await deleteStrategy(s.name)
                                setImportSuccess([`已删除: ${s.name}`])
                                setTimeout(() => loadAll(), 400)
                              } catch (err) {
                                setApiError(api.friendlyError(err))
                              } finally {
                                setIsLoading(false)
                              }
                            }}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                          {/* 保存到生产：仅完成回测的策略可保存 */}
                          {(() => {
                            const lastResult = strategyLastResult(s.name)
                            const isCompleted = lastResult && (lastResult.status === 'completed' || lastResult.status === 'done')
                            const isApproved = approvedStrategies.some((a) => a.name === s.name)
                            return (
                              <Button
                                variant="ghost"
                                size="icon"
                                className={`h-8 w-8 ${isCompleted ? (isApproved ? 'text-emerald-400 hover:text-emerald-300' : 'text-neutral-400 hover:text-emerald-400') : 'text-neutral-700 cursor-not-allowed'}`}
                                title={isCompleted ? (isApproved ? '已保存到生产（可重复保存覆盖）' : '保存到生产文件夹（供决策端采集）') : '需先完成回测才能保存到生产'}
                                disabled={!isCompleted || isApprovingStrategy === s.name}
                                onClick={(e) => { e.stopPropagation(); setApproveConfirmTarget(s.name) }}
                              >
                                {isApproved ? <Shield className="w-4 h-4" /> : <Save className="w-4 h-4" />}
                              </Button>
                            )
                          })()}
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={8} className="py-8 px-4">
                      {isLoading ? (
                        <p className="text-center text-neutral-400">加载中...</p>
                      ) : (
                        <EmptyState
                          title="暂无策略"
                          description="暂无策略，请导入 YAML 策略文件"
                          icon="inbox"
                          actionLabel="导入策略"
                          onAction={() => fileInputRef.current?.click()}
                        />
                      )}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* ─── 已审批策略（保存到生产）清单 ──────────────────────── */}
      {approvedStrategies.length > 0 && (
        <Card className="bg-neutral-900 border-emerald-700/40">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-emerald-400 tracking-wider flex items-center gap-2">
              <Shield className="w-4 h-4" />
              已审批策略 / Approved for Production ({approvedStrategies.length})
              <span className="text-xs text-neutral-500 font-normal">— 等待决策端从指定路径采集</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
              {approvedStrategies.map((s) => {
                const isDelivered = !!(s as any).delivered
                return (
                  <div key={s.name} className={`flex items-center gap-2 rounded p-2 border ${isDelivered ? 'bg-emerald-950/30 border-emerald-700/60' : 'bg-neutral-800 border-emerald-900/40'}`}>
                    <Shield className={`w-3.5 h-3.5 flex-shrink-0 ${isDelivered ? 'text-emerald-300' : 'text-emerald-500'}`} />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-white font-mono truncate">{s.name}</p>
                      <p className="text-[10px] text-neutral-500">{s.date}</p>
                    </div>
                    {(s as any).totalReturn != null && (
                      <span className={`text-[10px] font-mono ${(s as any).totalReturn >= 0 ? 'text-red-400' : 'text-green-400'}`}>
                        {(s as any).totalReturn >= 0 ? '+' : ''}{Number((s as any).totalReturn).toFixed(1)}%
                      </span>
                    )}
                    {/* 已送达状态 */}
                    <button
                      className={`text-[10px] px-1.5 py-0.5 rounded border flex-shrink-0 transition-colors ${isDelivered ? 'text-emerald-300 border-emerald-700/60 bg-emerald-900/30 hover:bg-emerald-900/50' : 'text-neutral-500 border-neutral-600 bg-neutral-700/50 hover:text-emerald-400 hover:border-emerald-700'}`}
                      title={isDelivered ? '点击取消已送达标记' : '点击标记为已送达决策端'}
                      onClick={() => {
                        markStrategyDelivered(s.name, !isDelivered)
                        setApprovedStrategies(getApprovedStrategies())
                      }}
                    >
                      {isDelivered ? '✓已送达' : '待送达'}
                    </button>
                    <button
                      className="text-neutral-600 hover:text-red-400 transition-colors flex-shrink-0 ml-1"
                      title="撤销：从审批列表移除"
                      onClick={() => handleRevokeStrategy(s.name)}
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* ─── 保存到生产二次确认弹窗 ─────────────────────────────── */}
      {approveConfirmTarget && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-neutral-900 border border-red-600/60 rounded-xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-7 h-7 text-red-400 flex-shrink-0" />
              <div>
                <h3 className="text-base font-bold text-red-300">保存到生产 — 二次确认</h3>
                <p className="text-xs text-neutral-500 mt-0.5">此操作将策略标记为"已审批"并下载 YAML 文件</p>
              </div>
            </div>
            <div className="bg-neutral-800 rounded-lg p-3 border border-neutral-700">
              <p className="text-xs text-neutral-400 mb-1">即将保存的策略：</p>
              <p className="text-sm font-mono text-white font-semibold">{approveConfirmTarget}</p>
            </div>
            <div className="bg-amber-900/20 border border-amber-700/40 rounded-lg p-3">
              <p className="text-xs text-amber-300 leading-relaxed">
                ⚠️ 保存后该策略将出现在决策端采集路径中。<br />
                请确认回测表现符合上线标准，否则将影响实盘决策质量。
              </p>
            </div>
            <div className="flex gap-3 justify-end pt-1">
              <Button
                variant="outline"
                className="border-neutral-600 text-neutral-400 bg-transparent hover:bg-neutral-800"
                onClick={() => setApproveConfirmTarget(null)}
              >
                取消
              </Button>
              <Button
                className="bg-red-700 hover:bg-red-600 text-white font-semibold"
                disabled={isApprovingStrategy === approveConfirmTarget}
                onClick={() => {
                  const target = approveConfirmTarget
                  setApproveConfirmTarget(null)
                  handleApproveStrategy(target)
                }}
              >
                {isApprovingStrategy === approveConfirmTarget ? '保存中...' : '确认保存到生产'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* YAML 策略编辑器弹窗 */}
      {yamlEditorStrategy && (
        <div className="fixed inset-0 bg-black/75 flex items-center justify-center z-50 p-4" onClick={() => { setYamlEditorStrategy(null); setYamlSaveMsg(null) }}>
          <div className="bg-neutral-900 border border-purple-600/40 w-full max-w-4xl rounded-lg flex flex-col shadow-2xl" style={{ height: "82vh" }} onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between px-5 py-3 border-b border-neutral-700">
              <div>
                <p className="text-sm font-bold text-purple-300 font-mono">{yamlEditorStrategy}</p>
                <p className="text-xs text-neutral-500 mt-0.5">直接编辑策略 YAML 配置文件</p>
              </div>
              <div className="flex items-center gap-3">
                {yamlSaveMsg && (
                  <span className={`text-xs ${yamlSaveMsg.startsWith("✓") ? "text-green-400" : "text-red-400"}`}>{yamlSaveMsg}</span>
                )}
                <Button className="bg-purple-600 hover:bg-purple-700 text-white text-xs h-8 px-4" disabled={isSavingYaml} onClick={handleSaveYaml}>
                  {isSavingYaml ? "保存中..." : "保存修改"}
                </Button>
                <Button variant="outline" className="border-neutral-700 text-neutral-400 bg-transparent text-xs h-8 px-4" onClick={() => { setYamlEditorStrategy(null); setYamlSaveMsg(null) }}>
                  关闭
                </Button>
              </div>
            </div>
            <textarea
              value={yamlContent}
              onChange={(e) => setYamlContent(e.target.value)}
              className="flex-1 font-mono text-xs bg-neutral-950 text-green-300 p-5 resize-none focus:outline-none leading-relaxed"
              spellCheck={false}
              autoCorrect="off"
              autoCapitalize="off"
            />
            <div className="px-5 py-2 border-t border-neutral-800 flex items-center justify-between">
              <p className="text-xs text-neutral-600">Ctrl+S 不支持自动保存，请点击"保存修改"按钮</p>
              <p className="text-xs text-neutral-600">{yamlContent.split("\n").length} 行 · {yamlContent.length} 字符</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
