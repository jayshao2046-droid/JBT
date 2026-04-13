export type FieldLabel = {
  zh: string
  en?: string
  unit?: string
  desc?: string
}

export type ContractCategoryPreset = {
  key: string
  zh: string
  en: string
  codes: string[]
}

export const FALLBACK_CONTRACT_CATEGORIES: ContractCategoryPreset[] = [
  { key: "ferrous", zh: "黑色系", en: "Ferrous", codes: ["rb", "hc", "i", "j", "jm", "sf", "sm"] },
  { key: "non_ferrous", zh: "有色金属", en: "Non-Ferrous", codes: ["cu", "al", "zn", "pb", "ni", "sn", "ss", "ao", "bc"] },
  { key: "precious", zh: "贵金属", en: "Precious Metals", codes: ["au", "ag"] },
  { key: "energy", zh: "能源", en: "Energy", codes: ["sc", "lu", "fu", "bu", "nr"] },
  { key: "chemicals", zh: "化工", en: "Chemicals", codes: ["ru", "br", "l", "pp", "v", "eb", "eg", "pg", "ta", "ma", "fg", "sa", "ur", "sp"] },
  { key: "oils_meals", zh: "油脂油料", en: "Oils & Meals", codes: ["p", "y", "oi", "m", "rm", "a", "b"] },
  { key: "grains", zh: "谷物淀粉", en: "Grains & Starch", codes: ["c", "cs"] },
  { key: "softs", zh: "软商品", en: "Softs", codes: ["cf", "sr", "ap", "cj", "pk"] },
  { key: "livestock", zh: "畜禽", en: "Livestock", codes: ["jd", "lh"] },
  { key: "financials", zh: "金融期货", en: "Financial Futures", codes: ["if", "ih", "ic", "im", "ts", "tf", "t", "tl"] },
]

const BASE_LABELS: Record<string, FieldLabel> = {
  strategy_id: { zh: "策略标识", en: "Strategy ID", desc: "本次运行的策略标识 / Strategy id for this run" },
  name: { zh: "名称", en: "Name", desc: "配置项名称 / Item name" },
  description: { zh: "说明", en: "Description", desc: "配置项说明 / Item description" },
  version: { zh: "版本", en: "Version", desc: "策略版本 / Strategy version" },
  category: { zh: "分类", en: "Category", desc: "策略分类 / Strategy category" },
  template_id: { zh: "模板标识", en: "Template ID", desc: "正式策略模板标识 / Formal strategy template id" },
  start: { zh: "开始日期", en: "Start Date", desc: "回测起始日期 / Backtest start date" },
  end: { zh: "结束日期", en: "End Date", desc: "回测结束日期 / Backtest end date" },
  start_date: { zh: "开始日期", en: "Start Date", desc: "回测起始日期 / Backtest start date" },
  end_date: { zh: "结束日期", en: "End Date", desc: "回测结束日期 / Backtest end date" },
  symbol: { zh: "主合约", en: "Symbol", desc: "策略默认合约 / Default trading symbol" },
  symbols: { zh: "合约列表", en: "Symbols", desc: "策略默认合约集合 / Default symbol list" },
  contract: { zh: "合约", en: "Contract", desc: "本次回测使用的合约 / Contract used in this run" },
  timeframe: { zh: "时间周期", en: "Timeframe", desc: "策略使用的时间周期 / Strategy timeframe" },
  timeframe_minutes: { zh: "时间周期", en: "Timeframe", desc: "策略使用的时间周期 / Strategy timeframe" },
  initialcapital: { zh: "初始资金", en: "Initial Capital", unit: "元", desc: "回测初始资金 / Backtest starting capital" },
  initial_capital: { zh: "初始资金", en: "Initial Capital", unit: "元", desc: "回测初始资金 / Backtest starting capital" },
  initial_position: { zh: "初始仓位", en: "Initial Position", unit: "手", desc: "回测起始持仓 / Initial position size" },
  position_ratio: { zh: "仓位比例", en: "Position Ratio", unit: "小数", desc: "按小数表示的目标仓位比例（0.5 = 50%） / Target position ratio in decimal" },
  contract_size: { zh: "合约乘数", en: "Contract Size", desc: "每手合约乘数 / Contract multiplier" },
  contract_multiplier: { zh: "合约乘数", en: "Contract Multiplier", desc: "回测使用的合约乘数 / Contract multiplier" },
  price_tick: { zh: "最小跳动", en: "Price Tick", unit: "点", desc: "最小价格变动单位 / Minimum price tick" },
  pricetick: { zh: "最小跳动", en: "Price Tick", unit: "点", desc: "最小价格变动单位 / Minimum price tick" },
  commission: { zh: "手续费", en: "Commission", desc: "按策略 YAML 原值显示 / Display strategy raw commission value" },
  commission_rate: { zh: "手续费率", en: "Commission Rate", unit: "小数", desc: "按小数表示的手续费率 / Commission rate in decimal" },
  commission_per_contract: { zh: "每手手续费", en: "Commission Per Contract", unit: "元", desc: "每手交易手续费 / Commission per contract" },
  commission_per_lot_round_turn: { zh: "每手往返手续费", en: "Commission Per Lot", unit: "元", desc: "每手来回手续费 / Round-turn commission per lot" },
  slippage: { zh: "滑点", en: "Slippage", unit: "点", desc: "按策略 YAML 原值显示 / Display strategy raw slippage value" },
  slippage_per_unit: { zh: "每手滑点", en: "Slippage Per Unit", unit: "点", desc: "每手滑点成本 / Slippage per unit" },
  slippage_per_contract: { zh: "每手滑点", en: "Slippage Per Contract", unit: "点", desc: "每手交易滑点 / Slippage per contract" },
  formula: { zh: "公式", en: "Formula", desc: "因子或信号表达式 / Factor or signal formula" },
  type: { zh: "类型", en: "Type", desc: "参数或指标类型 / Type" },
  params: { zh: "参数", en: "Params", desc: "指标输入参数 / Indicator input parameters" },
  method: { zh: "方法", en: "Method", desc: "策略方法配置 / Method setting" },
  ratio: { zh: "比例", en: "Ratio", unit: "小数", desc: "按小数表示的比例 / Ratio in decimal" },
  threshold: { zh: "阈值", en: "Threshold", desc: "信号触发阈值 / Trigger threshold" },
  long_entry_threshold: { zh: "多头开仓阈值", en: "Long Entry Threshold", desc: "做多开仓阈值 / Long entry threshold" },
  long_exit_threshold: { zh: "多头平仓阈值", en: "Long Exit Threshold", desc: "做多平仓阈值 / Long exit threshold" },
  short_entry_threshold: { zh: "空头开仓阈值", en: "Short Entry Threshold", desc: "做空开仓阈值 / Short entry threshold" },
  short_exit_threshold: { zh: "空头平仓阈值", en: "Short Exit Threshold", desc: "做空平仓阈值 / Short exit threshold" },
  weight: { zh: "权重", en: "Weight", desc: "因子权重 / Factor weight" },
  long_condition: { zh: "做多条件", en: "Long Condition", desc: "多头信号触发条件 / Long signal condition" },
  short_condition: { zh: "做空条件", en: "Short Condition", desc: "空头信号触发条件 / Short signal condition" },
  factor_name: { zh: "因子名称", en: "Factor Name", desc: "因子标识 / Factor identifier" },
  adx_threshold: { zh: "ADX 阈值", en: "ADX Threshold", desc: "趋势强度阈值 / Trend strength threshold" },
  p2_health_threshold: { zh: "P2 健康阈值", en: "P2 Health Threshold", desc: "第二阶段健康度阈值 / Phase-2 health threshold" },
  p3_momentum_threshold: { zh: "P3 动量阈值", en: "P3 Momentum Threshold", desc: "第三阶段动量阈值 / Phase-3 momentum threshold" },
  volume_ratio_threshold: { zh: "量比阈值", en: "Volume Ratio Threshold", desc: "量比过滤阈值 / Volume ratio filter threshold" },
  cooldown_bars: { zh: "冷却 K 线数", en: "Cooldown Bars", unit: "根", desc: "信号冷却所需 K 线数量 / Cooldown bars" },
  lookback: { zh: "回看周期", en: "Lookback", unit: "根", desc: "回看历史 K 线数量 / Lookback bars" },
  window: { zh: "窗口大小", en: "Window", unit: "根", desc: "计算窗口大小 / Calculation window" },
  period: { zh: "计算周期", en: "Period", unit: "根", desc: "指标计算周期 / Indicator period" },
  timeperiod: { zh: "时间周期", en: "Time Period", unit: "根", desc: "指标时间周期 / Indicator time period" },
  fast: { zh: "快线周期", en: "Fast Period", unit: "根", desc: "快线参数 / Fast period" },
  slow: { zh: "慢线周期", en: "Slow Period", unit: "根", desc: "慢线参数 / Slow period" },
  signal: { zh: "信号周期", en: "Signal Period", unit: "根", desc: "信号线参数 / Signal period" },
  enabled: { zh: "启用", en: "Enabled", desc: "当前配置是否启用 / Whether current config is enabled" },
  stop_loss_atr: { zh: "止损 ATR 倍数", en: "Stop Loss ATR", desc: "基于 ATR 的止损倍数 / ATR-based stop loss multiple" },
  take_profit_atr: { zh: "止盈 ATR 倍数", en: "Take Profit ATR", desc: "基于 ATR 的止盈倍数 / ATR-based take profit multiple" },
  activate_at: { zh: "触发阈值", en: "Activate At", desc: "达到该阈值后启用移动止损 / Threshold that activates trailing stop" },
  distance: { zh: "跟踪距离", en: "Distance", desc: "移动止损跟随距离 / Trailing stop distance" },
  max_drawdown: { zh: "最大回撤", en: "Max Drawdown", unit: "小数", desc: "按策略原值显示（如 0.12 = 12%） / Display raw drawdown ratio" },
  max_drawdown_limit: { zh: "最大回撤限制", en: "Max Drawdown Limit", unit: "小数", desc: "按策略原值显示（如 0.03 = 3%） / Display raw max drawdown limit" },
  daily_loss_limit: { zh: "日亏限额", en: "Daily Loss Limit", desc: "具体单位由配置路径决定 / Unit depends on path" },
}

const FACTOR_NAME_LABELS: Record<string, { zh: string; en: string }> = {
  trend_direction: { zh: "趋势方向", en: "Trend Direction" },
  trend_strength: { zh: "趋势强度", en: "Trend Strength" },
  pullback_health: { zh: "回调健康度", en: "Pullback Health" },
  momentum: { zh: "动量", en: "Momentum" },
  volume_confirmation: { zh: "量能确认", en: "Volume Confirmation" },
  low_volatility: { zh: "低波动过滤", en: "Low Volatility" },
}

function getLeafKey(path: string): string {
  const normalized = path.replace(/\[(\d+)\]/g, ".$1")
  const segments = normalized.split(".").filter(Boolean)
  return (segments[segments.length - 1] ?? path).toLowerCase()
}

function toTitleCase(value: string): string {
  return value
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ")
}

export function formatTimeframeValue(rawValue: string | number | null | undefined): string {
  if (rawValue == null || rawValue === "") return "--"
  const value = String(rawValue).trim()
  const minuteMatch = value.match(/^(\d+)m$/i)
  if (minuteMatch) return `${minuteMatch[1]} 分钟 (${value})`
  const hourMatch = value.match(/^(\d+)h$/i)
  if (hourMatch) return `${hourMatch[1]} 小时 (${value})`
  if (/^\d+$/.test(value)) return `${value} 分钟`
  return value
}

export function humanizeDataSource(rawSource: string | null | undefined): string {
  if (!rawSource) return "--"
  if (rawSource === "service_local") return "服务本地数据"
  if (rawSource === "service_local_compatibility") return "兼容层本地数据"
  if (rawSource === "tqsdk_realtime_main_contracts") return "TqSdk 实时主力合约"
  if (rawSource === "tqsdk_realtime_quotes") return "TqSdk 实时行情"
  if (rawSource === "formal_backtest_engine") return "正式回测引擎"
  return rawSource
}

export function normalizeContractCategories(value: unknown): ContractCategoryPreset[] {
  if (!Array.isArray(value)) return FALLBACK_CONTRACT_CATEGORIES

  const normalized = value
    .map((item) => {
      if (!item || typeof item !== "object") return null
      const record = item as Record<string, unknown>
      const key = typeof record.key === "string" ? record.key : ""
      const zh = typeof record.zh === "string" ? record.zh : ""
      const en = typeof record.en === "string" ? record.en : ""
      const codes = Array.isArray(record.codes)
        ? record.codes.filter((code): code is string => typeof code === "string")
        : []
      if (!key || !zh || !en || codes.length === 0) return null
      return { key, zh, en, codes }
    })
    .filter((item): item is ContractCategoryPreset => item !== null)

  return normalized.length > 0 ? normalized : FALLBACK_CONTRACT_CATEGORIES
}

export function resolveFieldLabel(path: string, key?: string): FieldLabel {
  const normalizedPath = path.toLowerCase()
  const leafKey = (key ?? getLeafKey(path)).toLowerCase()

  if (normalizedPath.startsWith("factors[") && leafKey === "name") {
    return { zh: "因子名称", en: "Factor Name", desc: "因子名称 / Factor name" }
  }
  if (normalizedPath.startsWith("factors[") && leafKey === "description") {
    return { zh: "因子说明", en: "Factor Description", desc: "因子说明 / Factor description" }
  }
  if (normalizedPath.startsWith("factors[") && leafKey === "formula") {
    return { zh: "因子公式", en: "Factor Formula", desc: "因子计算表达式 / Factor formula" }
  }
  if (normalizedPath.startsWith("factors[") && leafKey === "type") {
    return { zh: "因子类型", en: "Factor Type", desc: "因子输出类型 / Factor output type" }
  }
  if (normalizedPath.startsWith("indicators[") && leafKey === "name") {
    return { zh: "指标名称", en: "Indicator Name", desc: "指标名称 / Indicator name" }
  }
  if (normalizedPath.startsWith("indicators[") && leafKey === "type") {
    return { zh: "指标类型", en: "Indicator Type", desc: "指标类型 / Indicator type" }
  }
  if (normalizedPath.startsWith("indicators[") && leafKey === "params") {
    return { zh: "指标参数", en: "Indicator Params", desc: "指标输入序列与周期 / Indicator inputs and periods" }
  }
  if (normalizedPath.startsWith("signal_rule.") && leafKey === "long_condition") {
    return { zh: "做多条件", en: "Long Condition", desc: "多头信号表达式 / Long signal expression" }
  }
  if (normalizedPath.startsWith("signal_rule.") && leafKey === "short_condition") {
    return { zh: "做空条件", en: "Short Condition", desc: "空头信号表达式 / Short signal expression" }
  }
  if (normalizedPath.startsWith("position_size.") && leafKey === "method") {
    return { zh: "仓位方法", en: "Position Method", desc: "仓位控制方法 / Position sizing method" }
  }
  if (normalizedPath.startsWith("position_size.") && leafKey === "ratio") {
    return { zh: "仓位比例", en: "Position Ratio", unit: "小数", desc: "按小数表示的仓位比例（0.6 = 60%） / Position ratio in decimal" }
  }
  if (normalizedPath.startsWith("risk_control.") && leafKey === "daily_loss_limit") {
    return { zh: "日亏限额", en: "Daily Loss Limit", unit: "小数", desc: "按策略原值显示（0.02 = 2%） / Display raw daily loss ratio" }
  }
  if (normalizedPath.startsWith("risk_control.") && leafKey === "max_drawdown") {
    return { zh: "最大回撤", en: "Max Drawdown", unit: "小数", desc: "按策略原值显示（0.12 = 12%） / Display raw max drawdown ratio" }
  }
  if (normalizedPath.startsWith("risk_control.") && leafKey === "stop_loss_atr") {
    return { zh: "止损 ATR 倍数", en: "Stop Loss ATR", desc: "按 ATR 倍数控制止损 / Stop loss multiple based on ATR" }
  }
  if (normalizedPath.startsWith("risk_control.") && leafKey === "take_profit_atr") {
    return { zh: "止盈 ATR 倍数", en: "Take Profit ATR", desc: "按 ATR 倍数控制止盈 / Take profit multiple based on ATR" }
  }
  if (normalizedPath.startsWith("risk_control.trailing_stop.") && leafKey === "activate_at") {
    return { zh: "移动止损触发", en: "Trailing Stop Trigger", desc: "达到该阈值后启用移动止损 / Trailing stop trigger" }
  }
  if (normalizedPath.startsWith("risk_control.trailing_stop.") && leafKey === "distance") {
    return { zh: "移动止损距离", en: "Trailing Stop Distance", desc: "移动止损跟踪距离 / Trailing stop distance" }
  }
  if (normalizedPath.startsWith("factor_weights.")) {
    const factorKey = leafKey
    const factorLabel = FACTOR_NAME_LABELS[factorKey]
    return {
      zh: factorLabel ? `${factorLabel.zh} 权重` : "因子权重",
      en: factorLabel ? `${factorLabel.en} Weight` : `Factor Weight: ${toTitleCase(factorKey)}`,
      desc: "因子权重配置 / Factor weight setting",
    }
  }

  const base = BASE_LABELS[leafKey]
  if (base) return base

  return {
    zh: "参数项",
    en: "Parameter",
    desc: `配置路径 / ${path}`,
  }
}