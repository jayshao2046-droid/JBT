"use client"

import { useEffect, useRef, useState } from "react"
import api, { deleteStrategy, exportStrategyContent, saveStrategyParams, approveStrategyLocal, getApprovedStrategies, isStrategyApproved, revokeApprovedStrategy, markStrategyDelivered } from "@/src/utils/api"
import { FALLBACK_CONTRACT_CATEGORIES, type ContractCategoryPreset, formatTimeframeValue, humanizeDataSource, normalizeContractCategories, resolveFieldLabel } from "@/src/utils/strategyPresentation"
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

type YamlScalarValue = string | number | boolean | Array<string | number | boolean>
type YamlFieldGroup = "basic" | "strategy" | "signal" | "risk"

type ParsedYamlField = {
  path: string
  key: string
  value: YamlScalarValue
  lineIndex: number
  indent: number
  group: YamlFieldGroup
  editable: boolean
  factorIndex?: number
  listSection?: string | null
  listCardKey?: string | null
}

type ParsedYamlDocument = {
  raw: string
  basic: {
    name: string
    description: string
    version: string
    category: string
    templateId: string
    timeframe: string
    symbols: string[]
    factorCount: number
    indicatorCount: number
    factorNames: string[]
    indicatorNames: string[]
  }
  fields: ParsedYamlField[]
  structuredParams: Record<string, unknown>
}

type StrategyListSection = {
  section: string
  cards: Record<number, ParsedYamlField[]>
}

type SystemRuntimeConfig = {
  commodityCode: string
  initialCapital: string
  positionFraction: string
  slippagePerUnit: string
  commissionPerLotRoundTurn: string
  dailyLossLimit: string
  maxDrawdown: string
  perSymbolFuseYuan: string
  stopLossAtrMultiplier: string
  takeProfitAtrMultiplier: string
  maxConsecutiveLosses: string
  forceCloseDay: string
  forceCloseNight: string
  noOvernight: boolean
}

type SystemRuntimePreset = {
  id: string
  name: string
  commodityCode: string
  config: SystemRuntimeConfig
  updatedAt: number
}

const BASIC_INFO_PATHS = {
  name: new Set(["name", "strategy.name"]),
  description: new Set(["description", "strategy.description"]),
  version: new Set(["version", "strategy.version"]),
  category: new Set(["category", "strategy.category", "strategy.group"]),
  templateId: new Set(["template_id", "strategy.template_id", "strategy.template"]),
  timeframe: new Set(["timeframe_minutes", "timeframe", "parameters.timeframe_minutes", "parameters.timeframe", "parameters.bar_interval"]),
  symbol: new Set(["symbol", "parameters.symbol", "strategy.symbol"]),
  symbols: new Set(["symbols", "parameters.symbols", "strategy.symbols"]),
}
const NON_EDITABLE_PATH_SUFFIXES = new Set(["name", "description", "version", "category", "template_id", "factor_name", "symbol", "symbols"])
const STRATEGY_LIST_SECTION_LABELS: Record<string, { zh: string; en: string }> = {
  factors: { zh: "因子参数", en: "Factor Params" },
  indicators: { zh: "指标参数", en: "Indicator Params" },
}
const RISK_GROUP_KEYS = new Set(["daily_loss_limit_yuan", "per_symbol_fuse_yuan", "max_drawdown_pct", "force_close_day", "force_close_night", "no_overnight", "slippage_points", "commission_rate", "per_trade_stop_loss_pct", "per_trade_take_profit_pct", "atr_period", "atr_filter_multiple", "atr_stop_loss_multiple", "atr_take_profit_multiple", "daily_loss_limit", "max_drawdown_limit", "slippage_per_contract", "commission_per_contract", "atr_multiplier_sl", "atr_multiplier_tp1", "atr_multiplier_tp2", "atr_volatility_threshold", "trailing_stop_trigger", "trailing_stop_distance"])
const SIGNAL_GROUP_KEYS = new Set(["long_threshold", "short_threshold", "ema_periods", "confirm_bars", "long_condition", "short_condition", "adx_threshold", "p2_health_threshold", "p3_momentum_threshold", "volume_ratio_threshold", "cooldown_bars"])
const STRATEGY_SPECIAL_PREFIXES = [
  "transaction_costs.",
  "parameters.transaction_costs.",
  "contract_specs.",
  "parameters.contract_specs.",
  "position_adjustment.",
  "parameters.position_adjustment.",
  "market_filter.",
  "parameters.market_filter.",
]
const SYSTEM_PRESET_STORAGE_KEY = "jbt_backtest_system_runtime_presets_v1"
const SYSTEM_RUNTIME_ROOT_PATHS = new Set(["position_fraction", "backtest_start_date", "backtest_end_date"])

function buildDefaultSystemConfig(commodityCode = ""): SystemRuntimeConfig {
  return {
    commodityCode,
    initialCapital: "500000",
    positionFraction: "0.08",
    slippagePerUnit: "1",
    commissionPerLotRoundTurn: "6",
    dailyLossLimit: "0.05",
    maxDrawdown: "0.15",
    perSymbolFuseYuan: "2000",
    stopLossAtrMultiplier: "1.5",
    takeProfitAtrMultiplier: "2.5",
    maxConsecutiveLosses: "5",
    forceCloseDay: "14:55",
    forceCloseNight: "22:55",
    noOvernight: true,
  }
}

function createSystemPresetId(): string {
  return `runtime_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

function readSystemRuntimePresets(): SystemRuntimePreset[] {
  if (typeof window === "undefined") return []
  try {
    const raw = window.localStorage.getItem(SYSTEM_PRESET_STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed.filter((item): item is SystemRuntimePreset => Boolean(item?.id && item?.name && item?.config))
  } catch {
    return []
  }
}

function writeSystemRuntimePresets(presets: SystemRuntimePreset[]) {
  if (typeof window === "undefined") return
  window.localStorage.setItem(SYSTEM_PRESET_STORAGE_KEY, JSON.stringify(presets))
}

function upsertTopLevelBlock(yaml: string, key: string, block: string): string {
  const lines = yaml.split("\n")
  const startIndex = lines.findIndex((line) => new RegExp(`^${key}:(?:\\s|$)`).test(line.trim()) && !line.startsWith(" "))

  if (startIndex === -1) {
    const next = [...lines]
    if (next.length > 0 && next[next.length - 1].trim() !== "") next.push("")
    next.push(...block.split("\n"))
    return next.join("\n")
  }

  let endIndex = startIndex + 1
  while (endIndex < lines.length) {
    const current = lines[endIndex]
    const trimmed = current.trim()
    if (trimmed && !trimmed.startsWith("#") && /^[A-Za-z_][A-Za-z0-9_]*\s*:/.test(current) && !current.startsWith(" ")) {
      break
    }
    endIndex += 1
  }

  const next = [...lines]
  next.splice(startIndex, endIndex - startIndex, ...block.split("\n"))
  return next.join("\n")
}

function removeTopLevelBlock(yaml: string, key: string): string {
  const lines = yaml.split("\n")
  const startIndex = lines.findIndex((line) => new RegExp(`^${key}:(?:\\s|$)`).test(line.trim()) && !line.startsWith(" "))
  if (startIndex === -1) return yaml

  let endIndex = startIndex + 1
  while (endIndex < lines.length) {
    const current = lines[endIndex]
    const trimmed = current.trim()
    if (trimmed && !trimmed.startsWith("#") && /^[A-Za-z_][A-Za-z0-9_]*\s*:/.test(current) && !current.startsWith(" ")) {
      break
    }
    endIndex += 1
  }

  const next = [...lines]
  next.splice(startIndex, endIndex - startIndex)
  while (next.length > 0 && next[next.length - 1] === "") next.pop()
  return next.join("\n")
}

function buildSystemRiskBlock(config: SystemRuntimeConfig): string {
  const lines = ["risk:"]

  if (config.dailyLossLimit.trim()) lines.push(`  daily_loss_limit: ${config.dailyLossLimit.trim()}`)
  if (config.maxDrawdown.trim()) lines.push(`  max_drawdown: ${config.maxDrawdown.trim()}`)
  if (config.perSymbolFuseYuan.trim()) lines.push(`  per_symbol_fuse_yuan: ${config.perSymbolFuseYuan.trim()}`)
  if (config.maxConsecutiveLosses.trim()) lines.push(`  max_consecutive_losses: ${config.maxConsecutiveLosses.trim()}`)
  if (config.forceCloseDay.trim()) lines.push(`  force_close_day: ${JSON.stringify(config.forceCloseDay.trim())}`)
  if (config.forceCloseNight.trim()) lines.push(`  force_close_night: ${JSON.stringify(config.forceCloseNight.trim())}`)
  lines.push(`  no_overnight: ${config.noOvernight ? "true" : "false"}`)
  lines.push("  stop_loss:")
  lines.push(`    atr_multiplier: ${config.stopLossAtrMultiplier.trim() || "1.5"}`)
  lines.push("    type: \"atr\"")
  lines.push("  take_profit:")
  lines.push(`    atr_multiplier: ${config.takeProfitAtrMultiplier.trim() || "2.5"}`)
  lines.push("    type: \"atr\"")

  return lines.join("\n")
}

function applySystemConfigToYaml(yaml: string, config: SystemRuntimeConfig): string {
  let next = yaml
  next = removeTopLevelBlock(next, "stop_loss")
  next = removeTopLevelBlock(next, "take_profit")
  next = upsertTopLevelBlock(next, "position_fraction", `position_fraction: ${config.positionFraction.trim() || "0.08"}`)
  next = upsertTopLevelBlock(
    next,
    "transaction_costs",
    [
      "transaction_costs:",
      `  slippage_per_unit: ${config.slippagePerUnit.trim() || "1"}`,
      `  commission_per_lot_round_turn: ${config.commissionPerLotRoundTurn.trim() || "6"}`,
    ].join("\n"),
  )
  next = upsertTopLevelBlock(next, "risk", buildSystemRiskBlock(config))
  return next
}

function stripYamlQuotes(rawValue: string): string {
  const trimmed = rawValue.trim()
  if ((trimmed.startsWith('"') && trimmed.endsWith('"')) || (trimmed.startsWith("'") && trimmed.endsWith("'"))) {
    return trimmed.slice(1, -1)
  }
  return trimmed
}

function parseYamlInlineArray(rawValue: string): Array<string | number | boolean> | null {
  const trimmed = rawValue.trim()
  if (!trimmed.startsWith("[") || !trimmed.endsWith("]")) return null

  const content = trimmed.slice(1, -1).trim()
  if (!content) return []

  return content
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
    .map((item) => {
      if (item === "true") return true
      if (item === "false") return false
      if (/^-?\d+(\.\d+)?$/.test(item)) return Number(item)
      return stripYamlQuotes(item)
    })
}

function parseYamlScalarValue(rawValue: string): YamlScalarValue | null {
  const trimmed = rawValue.trim()
  if (!trimmed || trimmed === "|" || trimmed === ">") return null
  if (trimmed === "true") return true
  if (trimmed === "false") return false
  if (/^-?\d+(\.\d+)?$/.test(trimmed)) return Number(trimmed)
  if (trimmed.startsWith("[")) return parseYamlInlineArray(trimmed)
  if (trimmed.startsWith("{")) return null
  return stripYamlQuotes(trimmed)
}

function parseYamlStringList(rawValue: string): string[] {
  const trimmed = rawValue.trim()
  if (!trimmed.startsWith("[") || !trimmed.endsWith("]")) return []
  return trimmed
    .slice(1, -1)
    .split(",")
    .map((item) => stripYamlQuotes(item))
    .filter(Boolean)
}

function tokenizeYamlPath(path: string): Array<string | number> {
  const tokens: Array<string | number> = []
  const matcher = path.matchAll(/([^[.\]]+)|\[(\d+)\]/g)
  for (const match of matcher) {
    if (match[1]) tokens.push(match[1])
    else if (match[2]) tokens.push(Number(match[2]))
  }
  return tokens
}

function normalizeYamlPath(path: string): string {
  return path.toLowerCase()
}

function matchesBasicInfoPath(path: string): boolean {
  const normalizedPath = normalizeYamlPath(path)
  return Object.values(BASIC_INFO_PATHS).some((paths) => paths.has(normalizedPath))
}

function appendUniqueSymbol(target: string[], rawSymbol: string) {
  const symbol = stripYamlQuotes(rawSymbol)
  if (symbol && !target.includes(symbol)) {
    target.push(symbol)
  }
}

function setNestedValue(target: Record<string, unknown>, path: string, value: unknown) {
  const tokens = tokenizeYamlPath(path)
  let cursor: any = target

  tokens.forEach((token, index) => {
    const nextToken = tokens[index + 1]
    const isLast = index === tokens.length - 1
    if (typeof token === "string") {
      if (isLast) {
        cursor[token] = value
        return
      }
      if (cursor[token] == null) cursor[token] = typeof nextToken === "number" ? [] : {}
      cursor = cursor[token]
      return
    }

    if (!Array.isArray(cursor)) return
    if (isLast) {
      cursor[token] = value
      return
    }
    if (cursor[token] == null) cursor[token] = typeof nextToken === "number" ? [] : {}
    cursor = cursor[token]
  })
}

function getYamlListMatches(path: string) {
  return Array.from(path.matchAll(/([A-Za-z_][A-Za-z0-9_]*)\[(\d+)\]/g))
}

function getYamlListSection(path: string): string | null {
  const matches = getYamlListMatches(path)
  const lastMatch = matches[matches.length - 1]
  return lastMatch?.[1] ?? null
}

function getYamlListIndex(path: string): number | undefined {
  const matches = getYamlListMatches(path)
  const lastMatch = matches[matches.length - 1]
  return lastMatch?.[2] != null ? Number(lastMatch[2]) : undefined
}

function getYamlListCardKey(path: string): string | null {
  const listSection = getYamlListSection(path)
  const listIndex = getYamlListIndex(path)
  if (!listSection || listIndex == null) return null
  return `${listSection}:${listIndex}`
}

function getYamlLeafKey(path: string): string {
  const tokens = tokenizeYamlPath(path)
  const lastToken = tokens[tokens.length - 1]
  return typeof lastToken === "string" ? lastToken : String(lastToken)
}

function resolveYamlListSectionTitle(section: string): { zh: string; en: string } {
  return STRATEGY_LIST_SECTION_LABELS[section] ?? { zh: section, en: section }
}

function resolveYamlFieldGroup(path: string, key: string): YamlFieldGroup {
  const normalizedPath = normalizeYamlPath(path)
  const normalizedKey = key.toLowerCase()

  if (normalizedPath.startsWith("risk.") || normalizedPath.startsWith("parameters.risk.") || RISK_GROUP_KEYS.has(normalizedKey)) return "risk"
  if (normalizedPath.startsWith("signal.") || normalizedPath.startsWith("parameters.signal.") || SIGNAL_GROUP_KEYS.has(normalizedKey)) return "signal"
  if (matchesBasicInfoPath(path)) return "basic"
  return "strategy"
}

function isEditableYamlField(path: string, key: string): boolean {
  if (path === "timeframe_minutes") return false
  return !NON_EDITABLE_PATH_SUFFIXES.has(key)
}

function applyBasicFieldValue(basic: ParsedYamlDocument["basic"], path: string, value: YamlScalarValue) {
  const normalizedPath = normalizeYamlPath(path)
  if (BASIC_INFO_PATHS.name.has(normalizedPath)) basic.name = String(value)
  if (BASIC_INFO_PATHS.description.has(normalizedPath)) basic.description = String(value)
  if (BASIC_INFO_PATHS.version.has(normalizedPath)) basic.version = String(value)
  if (BASIC_INFO_PATHS.category.has(normalizedPath)) basic.category = String(value)
  if (BASIC_INFO_PATHS.templateId.has(normalizedPath)) basic.templateId = String(value)
  if (BASIC_INFO_PATHS.timeframe.has(normalizedPath)) basic.timeframe = String(value)
}

function parseStrategyYamlDocument(yaml: string): ParsedYamlDocument {
  const lines = yaml.split("\n")
  const fields: ParsedYamlField[] = []
  const structuredParams: Record<string, unknown> = {}
  const contexts: Array<{ indent: number; path: string; kind: "container" | "list-item" }> = []
  const arrayIndexes: Record<string, number> = {}
  const symbols: string[] = []
  const listCards = new Map<string, { section: string; index: number; title?: string }>()
  const basic = {
    name: "",
    description: "",
    version: "",
    category: "",
    templateId: "",
    timeframe: "",
    symbols: [] as string[],
    factorCount: 0,
    indicatorCount: 0,
    factorNames: [] as string[],
    indicatorNames: [] as string[],
  }

  const pushScalarField = (path: string, key: string, rawValue: string, lineIndex: number, indent: number) => {
    const scalarValue = parseYamlScalarValue(rawValue)
    if (scalarValue == null) return

    applyBasicFieldValue(basic, path, scalarValue)

    const factorIndex = getYamlListIndex(path)
    const listSection = getYamlListSection(path)
    const listCardKey = getYamlListCardKey(path)
    if (listCardKey && listSection && factorIndex != null) {
      const current = listCards.get(listCardKey)
      const nextTitle = ["factor_name", "name", "alias"].includes(key) && String(scalarValue).trim()
        ? String(scalarValue).trim()
        : current?.title
      listCards.set(listCardKey, {
        section: listSection,
        index: factorIndex,
        title: nextTitle,
      })
    }

    const group = resolveYamlFieldGroup(path, key)
    if (group !== "basic") {
      setNestedValue(structuredParams, path, scalarValue)
    }
    fields.push({
      path,
      key,
      value: scalarValue,
      lineIndex,
      indent,
      group,
      editable: group !== "basic" && isEditableYamlField(path, key),
      factorIndex,
      listSection,
      listCardKey,
    })
  }

  lines.forEach((line, lineIndex) => {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith("#")) return

    const indent = line.match(/^\s*/)?.[0].length ?? 0
    const isListItem = trimmed.startsWith("- ")
    while (
      contexts.length
      && (
        indent < contexts[contexts.length - 1].indent
        || (!isListItem && indent <= contexts[contexts.length - 1].indent)
        || (isListItem && indent === contexts[contexts.length - 1].indent && contexts[contexts.length - 1].kind === "list-item")
      )
    ) {
      contexts.pop()
    }
    const parentPath = contexts[contexts.length - 1]?.path ?? ""

    if (isListItem) {
      if (!parentPath) return
      const itemRaw = trimmed.slice(2).trim()
      if (normalizeYamlPath(parentPath).endsWith("symbols")) {
        if (itemRaw) appendUniqueSymbol(symbols, itemRaw)
        return
      }

      const currentIndex = (arrayIndexes[parentPath] ?? -1) + 1
      arrayIndexes[parentPath] = currentIndex
      const itemPath = `${parentPath}[${currentIndex}]`
      const inlineMatch = itemRaw.match(/^([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.+)$/)
      contexts.push({ indent, path: itemPath, kind: "list-item" })
      if (inlineMatch) {
        pushScalarField(`${itemPath}.${inlineMatch[1]}`, inlineMatch[1], inlineMatch[2], lineIndex, indent)
      }
      return
    }

    const keyValueMatch = trimmed.match(/^([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.*)$/)
    if (!keyValueMatch) return

    const [, key, rawValue] = keyValueMatch
    const path = parentPath ? `${parentPath}.${key}` : key
    if (!rawValue) {
      contexts.push({ indent, path, kind: "container" })
      return
    }

    const normalizedPath = normalizeYamlPath(path)
    if (BASIC_INFO_PATHS.symbols.has(normalizedPath) || BASIC_INFO_PATHS.symbol.has(normalizedPath)) {
      const inlineSymbols = BASIC_INFO_PATHS.symbols.has(normalizedPath) ? parseYamlStringList(rawValue) : []
      if (inlineSymbols.length > 0) inlineSymbols.forEach((symbol) => appendUniqueSymbol(symbols, symbol))
      else appendUniqueSymbol(symbols, rawValue)
      return
    }

    pushScalarField(path, key, rawValue, lineIndex, indent)
  })

  const listCardEntries = Array.from(listCards.values()).sort((left, right) => {
    if (left.section !== right.section) return left.section.localeCompare(right.section)
    return left.index - right.index
  })
  const factorEntries = listCardEntries.filter((entry) => entry.section === "factors")
  const indicatorEntries = listCardEntries.filter((entry) => entry.section === "indicators")
  const buildEntryNames = (entries: typeof listCardEntries) => entries.map((entry) => {
    if (entry.title) return entry.title
    const label = resolveYamlListSectionTitle(entry.section)
    return `${label.en} ${entry.index + 1}`
  })

  basic.symbols = symbols
  basic.factorNames = buildEntryNames(factorEntries)
  basic.indicatorNames = buildEntryNames(indicatorEntries)
  basic.factorCount = factorEntries.length
  basic.indicatorCount = indicatorEntries.length

  return {
    raw: yaml,
    basic,
    fields,
    structuredParams,
  }
}

function coerceEditedYamlValue(rawValue: string, fallbackValue: YamlScalarValue): YamlScalarValue {
  const trimmed = rawValue.trim()
  if (Array.isArray(fallbackValue)) {
    const candidate = trimmed.startsWith("[") ? trimmed : `[${trimmed}]`
    const inlineArray = parseYamlInlineArray(candidate)
    if (inlineArray) return inlineArray
    if (trimmed === "") return fallbackValue
  }
  if (trimmed === "true") return true
  if (trimmed === "false") return false
  if (/^-?\d+(\.\d+)?$/.test(trimmed)) return Number(trimmed)
  if (trimmed === "") return fallbackValue
  return trimmed
}

function formatYamlInlineItem(value: string | number | boolean): string {
  if (typeof value === "string") {
    return /^[A-Za-z_][A-Za-z0-9_./-]*$/.test(value) ? value : JSON.stringify(value)
  }
  return String(value)
}

function formatYamlScalarValue(value: YamlScalarValue): string {
  if (Array.isArray(value)) return `[${value.map((item) => formatYamlInlineItem(item)).join(", ")}]`
  if (typeof value === "string") return JSON.stringify(value)
  return String(value)
}

function formatYamlEditableValue(value: YamlScalarValue): string {
  if (Array.isArray(value)) return `[${value.map((item) => formatYamlInlineItem(item)).join(", ")}]`
  return String(value)
}

function buildUpdatedStrategyYaml(document: ParsedYamlDocument, edits: Record<string, string>): string {
  const nextLines = document.raw.split("\n")
  document.fields.forEach((field) => {
    if (!field.editable || !(field.path in edits)) return
    const nextValue = coerceEditedYamlValue(edits[field.path], field.value)
    nextLines[field.lineIndex] = `${" ".repeat(field.indent)}${field.key}: ${formatYamlScalarValue(nextValue)}`
  })
  return nextLines.join("\n")
}

function buildStructuredRunParams(document: ParsedYamlDocument, edits: Record<string, string>): Record<string, unknown> {
  const params: Record<string, unknown> = {}
  document.fields.forEach((field) => {
    if (field.group === "basic") return
    const nextValue = field.editable && field.path in edits
      ? coerceEditedYamlValue(edits[field.path], field.value)
      : field.value
    setNestedValue(params, field.path, nextValue)
  })
  return params
}

function splitStrategyFields(fields: ParsedYamlField[]) {
  const strategyFields = fields.filter((field) => field.group === "strategy")
  const listSections = strategyFields.reduce<Record<string, StrategyListSection>>((accumulator, field) => {
    if (!field.listSection || field.factorIndex == null || !field.editable) return accumulator
    if (!accumulator[field.listSection]) {
      accumulator[field.listSection] = {
        section: field.listSection,
        cards: {},
      }
    }
    accumulator[field.listSection].cards[field.factorIndex] = [
      ...(accumulator[field.listSection].cards[field.factorIndex] ?? []),
      field,
    ]
    return accumulator
  }, {})

  return {
    root: strategyFields.filter((field) => !field.listSection && !STRATEGY_SPECIAL_PREFIXES.some((prefix) => field.path.startsWith(prefix))),
    transactionCosts: strategyFields.filter((field) => field.path.startsWith("transaction_costs.") || field.path.startsWith("parameters.transaction_costs.")),
    contractSpecs: strategyFields.filter((field) => field.path.startsWith("contract_specs.") || field.path.startsWith("parameters.contract_specs.")),
    positionAdjustment: strategyFields.filter((field) => field.path.startsWith("position_adjustment.") || field.path.startsWith("parameters.position_adjustment.")),
    marketFilter: strategyFields.filter((field) => field.path.startsWith("market_filter.") || field.path.startsWith("parameters.market_filter.")),
    lists: listSections,
  }
}

function buildYamlEditState(document: ParsedYamlDocument): Record<string, string> {
  return Object.fromEntries(
    document.fields
      .filter((field) => field.editable)
      .map((field) => [field.path, formatYamlEditableValue(field.value)]),
  )
}

function getContractVarietyCode(contract: string): string {
  const normalized = contract.includes(".") ? contract.split(".").pop() ?? contract : contract
  const match = normalized.match(/[A-Za-z]+/)
  return match ? match[0].toLowerCase() : normalized.toLowerCase()
}

function formatCompactCurrency(value: string | number | null | undefined): string {
  if (value == null || value === "") return "--"
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return String(value)
  if (Math.abs(numeric) >= 10000) {
    const wan = numeric / 10000
    return `${Number.isInteger(wan) ? wan.toFixed(0) : wan.toFixed(1)}万`
  }
  return numeric.toLocaleString("zh-CN")
}

function formatDecimalAsPercent(value: string | number | null | undefined, digits = 1): string {
  if (value == null || value === "") return "--"
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return String(value)
  const percent = numeric * 100
  return `${Number(percent.toFixed(digits))}%`
}

function formatPercentInput(value: string | number | null | undefined, digits = 2): string {
  if (value == null || value === "") return ""
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return String(value)
  return String(Number((numeric * 100).toFixed(digits)))
}

function parsePercentInput(value: string): string {
  const trimmed = value.trim().replace(/%/g, "")
  if (!trimmed) return ""
  const numeric = Number(trimmed)
  if (!Number.isFinite(numeric)) return value
  return String(numeric / 100)
}

function humanizeTemplateId(templateId: string): string {
  if (!templateId) return "--"
  if (templateId === "generic_formal_strategy_v1") return "通用正式策略"
  return templateId.replace(/_/g, " ")
}

function resolveMainContractsFromSymbols(symbols: string[], availableContracts: string[]): string[] {
  const resolved: string[] = []
  symbols.forEach((symbol) => {
    const normalizedSymbol = symbol.trim().toLowerCase()
    if (!normalizedSymbol) return
    const normalizedToken = normalizedSymbol.includes(".") ? normalizedSymbol.split(".").pop() ?? normalizedSymbol : normalizedSymbol
    const allowVarietyFallback = normalizedToken.endsWith("_main") || !/\d/.test(normalizedToken)

    const directMatch = availableContracts.find((contract) => {
      const lowerContract = contract.toLowerCase()
      return lowerContract === normalizedSymbol || lowerContract.endsWith(`.${normalizedSymbol}`)
    })
    const fallbackMatch = directMatch ?? (allowVarietyFallback
      ? availableContracts.find((contract) => getContractVarietyCode(contract) === getContractVarietyCode(symbol))
      : undefined)
    const nextSymbol = fallbackMatch ?? symbol.trim()

    if (!resolved.includes(nextSymbol)) {
      resolved.push(nextSymbol)
    }
  })
  return resolved
}

function getContractsByCategory(codes: readonly string[], availableContracts: string[]): string[] {
  return availableContracts.filter((contract) => codes.includes(getContractVarietyCode(contract)))
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

function fmtClock(date: Date): string {
  return date.toLocaleTimeString("zh-CN", { hour12: false })
}

export default function StrategyManagementPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedStrategy, setSelectedStrategy] = useState<any>(null)
  const [importErrors, setImportErrors] = useState<string[]>([])
  const [importSuccess, setImportSuccess] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [apiError, setApiError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState("--")
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
  const [contractCategoryPresets, setContractCategoryPresets] = useState<ContractCategoryPreset[]>(FALLBACK_CONTRACT_CATEGORIES)
  const [mainContractsNote, setMainContractsNote] = useState<string>("")
  const [selectedContract, setSelectedContract] = useState("")
  const [runParamMsg, setRunParamMsg] = useState<string | null>(null)
  const [selectedStrategyForRun, setSelectedStrategyForRun] = useState<string>("")
  const [cancellingId, setCancellingId] = useState<string | null>(null)
  const [progressMap, setProgressMap] = useState<Record<string, { progress: number; current_date: string | null }>>({})
  const [yamlEditorStrategy, setYamlEditorStrategy] = useState<string | null>(null)
  const [yamlContent, setYamlContent] = useState<string>("")
  const [yamlSaveMsg, setYamlSaveMsg] = useState<string | null>(null)
  const [isSavingYaml, setIsSavingYaml] = useState(false)
  const [selectedContracts, setSelectedContracts] = useState<string[]>([])
  const [contractInput, setContractInput] = useState("")
  const [contractSuggestions, setContractSuggestions] = useState<string[]>([])
  const [strategyYamlDocument, setStrategyYamlDocument] = useState<ParsedYamlDocument | null>(null)
  const [strategyYamlParams, setStrategyYamlParams] = useState<Record<string, string>>({})
  const [systemPresets, setSystemPresets] = useState<SystemRuntimePreset[]>([])
  const [selectedSystemPresetId, setSelectedSystemPresetId] = useState<string>("")
  const [systemPresetName, setSystemPresetName] = useState<string>("")
  const [systemPresetMsg, setSystemPresetMsg] = useState<string | null>(null)
  const [systemConfig, setSystemConfig] = useState<SystemRuntimeConfig>(buildDefaultSystemConfig())
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

  useEffect(() => {
    const presets = readSystemRuntimePresets()
    setSystemPresets(presets)
    if (presets.length > 0) {
      setSelectedSystemPresetId(presets[0].id)
      setSystemPresetName(presets[0].name)
      setSystemConfig({ ...presets[0].config })
    }
  }, [])

  const inferSystemConfigFromDocument = (document: ParsedYamlDocument | null, commodityCode: string): SystemRuntimeConfig => {
    const base = buildDefaultSystemConfig(commodityCode)
    if (!document) return base

    const readValue = (paths: string[]): YamlScalarValue | undefined => {
      const found = document.fields.find((field) => paths.includes(field.path))
      return found?.value
    }

    return {
      commodityCode: commodityCode || base.commodityCode,
      initialCapital: base.initialCapital,
      positionFraction: String(readValue(["position_fraction"]) ?? base.positionFraction),
      slippagePerUnit: String(readValue(["transaction_costs.slippage_per_unit"]) ?? base.slippagePerUnit),
      commissionPerLotRoundTurn: String(readValue(["transaction_costs.commission_per_lot_round_turn"]) ?? base.commissionPerLotRoundTurn),
      dailyLossLimit: String(readValue(["risk.daily_loss_limit", "risk.daily_loss_limit_yuan"]) ?? base.dailyLossLimit),
      maxDrawdown: String(readValue(["risk.max_drawdown", "risk.max_drawdown_pct"]) ?? base.maxDrawdown),
      perSymbolFuseYuan: String(readValue(["risk.per_symbol_fuse_yuan"]) ?? base.perSymbolFuseYuan),
      stopLossAtrMultiplier: String(readValue(["risk.stop_loss.atr_multiplier", "risk.stop_loss_atr_multiplier"]) ?? base.stopLossAtrMultiplier),
      takeProfitAtrMultiplier: String(readValue(["risk.take_profit.atr_multiplier", "risk.take_profit_atr_multiplier"]) ?? base.takeProfitAtrMultiplier),
      maxConsecutiveLosses: String(readValue(["risk.max_consecutive_losses"]) ?? base.maxConsecutiveLosses),
      forceCloseDay: String(readValue(["risk.force_close_day"]) ?? base.forceCloseDay),
      forceCloseNight: String(readValue(["risk.force_close_night"]) ?? base.forceCloseNight),
      noOvernight: Boolean(readValue(["risk.no_overnight"]) ?? base.noOvernight),
    }
  }

  const resolveSystemConfigForDocument = (document: ParsedYamlDocument, strategyName?: string): SystemRuntimeConfig => {
    const commodityCode = document.basic.symbols[0] ? getContractVarietyCode(document.basic.symbols[0]) : systemConfig.commodityCode
    if (strategyName && strategyName === selectedStrategyForRun) {
      return { ...systemConfig, commodityCode: systemConfig.commodityCode || commodityCode }
    }
    const matchedPreset = commodityCode ? systemPresets.find((preset) => preset.commodityCode === commodityCode) : undefined
    return matchedPreset ? { ...matchedPreset.config, commodityCode } : inferSystemConfigFromDocument(document, commodityCode)
  }

  const prepareStrategyYamlForAction = async (name: string) => {
    const loadedDocument = name === selectedStrategyForRun && strategyYamlDocument
      ? strategyYamlDocument
      : await loadStrategyYamlForStrategy(name, { resetContractSelection: true })

    if (!loadedDocument) {
      return null
    }

    const editState = name === selectedStrategyForRun && strategyYamlDocument
      ? strategyYamlParams
      : buildYamlEditState(loadedDocument)
    const effectiveSystemConfig = resolveSystemConfigForDocument(loadedDocument, name)
    const updatedYaml = buildUpdatedStrategyYaml(loadedDocument, editState)
    const runtimeYaml = applySystemConfigToYaml(updatedYaml, effectiveSystemConfig)
    const nextDocument = parseStrategyYamlDocument(runtimeYaml)
    const params = buildStructuredRunParams(nextDocument, editState)
    const symbolsToUse = resolveSymbolsForRun(nextDocument)

    return {
      editState,
      effectiveSystemConfig,
      loadedDocument,
      nextDocument,
      params,
      runtimeYaml,
      symbolsToUse,
    }
  }

  const buildRunPayloads = (
    strategyName: string,
    prepared: NonNullable<Awaited<ReturnType<typeof prepareStrategyYamlForAction>>>,
    imported: Record<string, any> | null | undefined,
  ) => {
    const basePayload: Record<string, any> = {
      strategy_id: strategyName,
      start: backtestStart,
      end: backtestEnd,
    }

    if (!Number.isNaN(Number(prepared.effectiveSystemConfig.initialCapital)) && Number(prepared.effectiveSystemConfig.initialCapital) > 0) {
      basePayload.initial_capital = Number(prepared.effectiveSystemConfig.initialCapital)
    }

    const slippage = Number(prepared.effectiveSystemConfig.slippagePerUnit)
    if (!Number.isNaN(slippage) && slippage >= 0) {
      basePayload.slippage_per_unit = slippage
    }
    const commission = Number(prepared.effectiveSystemConfig.commissionPerLotRoundTurn)
    if (!Number.isNaN(commission) && commission >= 0) {
      basePayload.commission_per_lot_round_turn = commission
    }

    if (!imported?.execution_profile?.formal_supported) {
      return [{
        ...basePayload,
        symbols: prepared.symbolsToUse,
        params: prepared.params,
      }]
    }

    const contractsToRun = (prepared.symbolsToUse?.length ? prepared.symbolsToUse : []).filter(Boolean)
    if (contractsToRun.length <= 1) {
      const contract = contractsToRun[0]
      return [{
        ...basePayload,
        symbols: contract ? [contract] : prepared.symbolsToUse,
        contract,
      }]
    }

    return contractsToRun.map((contract) => ({
      ...basePayload,
      symbols: [contract],
      contract,
    }))
  }

  const submitRunPayloads = async (payloads: Array<Record<string, any>>) => {
    const responses: Array<{ task_id?: string }> = []
    for (const payload of payloads) {
      const response = await api.runBacktest(payload)
      responses.push(response)
    }
    return responses
  }

  useEffect(() => {
    const symbol = strategyYamlDocument?.basic?.symbols?.[0]
    const commodityCode = symbol ? getContractVarietyCode(symbol) : ""
    if (!commodityCode) return

    const matchedPreset = systemPresets.find((preset) => preset.commodityCode === commodityCode)
    if (matchedPreset) {
      setSelectedSystemPresetId((prev) => (prev === matchedPreset.id ? prev : matchedPreset.id))
      setSystemPresetName(matchedPreset.name)
      setSystemConfig({ ...matchedPreset.config, commodityCode })
      return
    }

    setSelectedSystemPresetId("")
    setSystemPresetName(`${commodityCode.toUpperCase()} 预设`)
    setSystemConfig(inferSystemConfigFromDocument(strategyYamlDocument, commodityCode))
  }, [strategyYamlDocument, systemPresets])

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
        setContractCategoryPresets(normalizeContractCategories(contractsData.value?.categories))
        const source = contractsData.value?.source ? `来源: ${humanizeDataSource(contractsData.value.source)}` : ""
        const note = contractsData.value?.note ? String(contractsData.value.note) : ""
        setMainContractsNote([source, note].filter(Boolean).join(" | "))
      }
      const now = new Date()
      setLastUpdate(fmtClock(now))
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
      const slippage = Number(systemConfig.slippagePerUnit)
      const commission = Number(systemConfig.commissionPerLotRoundTurn)
      const runPayload: Record<string, any> = { strategy_id: strategyName, start: backtestStart, end: backtestEnd }
      if (!Number.isNaN(slippage) && slippage >= 0) runPayload.slippage_per_unit = slippage
      if (!Number.isNaN(commission) && commission >= 0) runPayload.commission_per_lot_round_turn = commission
      const resp = await api.runBacktest(runPayload)
      if (resp.status === 'failed' && resp.error_message) {
        setApiError(`回测失败 [${strategyName}]：${String(resp.error_message).split('\n')[0]}`)
      } else {
        setImportSuccess([`回测已提交: ${resp.task_id ?? "任务已提交"}`])
      }
      setTimeout(() => loadAll(), 800)
    } catch (err) {
      setApiError(api.friendlyError(err))
    } finally {
      setIsLoading(false)
    }
  }

  const handleSaveCurrentStrategy = async (strategyNameOverride?: string) => {
    const name = strategyNameOverride ?? selectedStrategyForRun
    if (!name) {
      setParamSaveMsg("请先在下方选择一个策略，再保存调整后的参数")
      return
    }

    setParamSaveMsg(null)
    setIsSavingParams(true)
    try {
      const prepared = await prepareStrategyYamlForAction(name)
      if (!prepared) {
        setParamSaveMsg(`保存失败：无法加载策略 ${name} 的 YAML，请刷新页面后重试`)
        return
      }

      await api.importStrategy(name, prepared.runtimeYaml)
      setSelectedStrategyForRun(name)
      setStrategyYamlDocument(prepared.nextDocument)
      setStrategyYamlParams(buildYamlEditState(prepared.nextDocument))
      setSystemConfig({ ...prepared.effectiveSystemConfig })
      setParamSaveMsg(`✓ 已保存策略：${name}，当前调整已覆盖后端策略 YAML`)
      setImportSuccess([`✓ 已保存策略：${name}`])
      setTimeout(() => loadAll(), 500)
    } catch (err) {
      const message = `保存失败：${api.friendlyError(err)}`
      setParamSaveMsg(message)
      setApiError(api.friendlyError(err))
    } finally {
      setIsSavingParams(false)
    }
  }

  const handleSaveParamsAndRun = async (strategyNameOverride?: string) => {
    const name = strategyNameOverride ?? selectedStrategyForRun
    if (!name) {
      setRunParamMsg("请先在下方选择一个策略（点击策略名）")
      return
    }
    setRunParamMsg(null)
    setIsLoading(true)
    try {
      const prepared = await prepareStrategyYamlForAction(name)
      if (!prepared) {
        setRunParamMsg(`提交失败：无法加载策略 ${name} 的 YAML，请刷新页面后重试`)
        return
      }

      if (!prepared.symbolsToUse || prepared.symbolsToUse.length === 0) {
        setRunParamMsg("⚠️ 未选择合约，且策略 YAML 中未找到 symbols，可能导致零成交")
      }

      const imported = await api.importStrategy(name, prepared.runtimeYaml)
      setSelectedStrategyForRun(name)
      setStrategyYamlDocument(prepared.nextDocument)
      setStrategyYamlParams(buildYamlEditState(prepared.nextDocument))
      setSystemConfig({ ...prepared.effectiveSystemConfig })

      const runPayloads = buildRunPayloads(name, prepared, imported)
      const responses = await submitRunPayloads(runPayloads)
      const failedResponses = responses.filter((r: any) => r.status === 'failed' && r.error_message)
      if (failedResponses.length > 0) {
        const errMsg = failedResponses.map((r: any) => String(r.error_message).split('\n')[0]).join('；')
        setRunParamMsg(`❌ 回测失败 [${name}]：${errMsg}`)
        setApiError(`回测失败 [${name}]：${errMsg}`)
      } else {
        const msg = responses.length > 1
          ? `✓ 已提交 ${responses.length} 个品种回测任务（策略：${name}）`
          : `✓ 已提交回测：${responses[0]?.task_id || "已提交"}（策略：${name}）`
        setRunParamMsg(msg)
        setImportSuccess([msg])
      }
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
    const batchFailures: string[] = []
    try {
      const names = Array.from(selectedIds)
      const limit = Math.max(1, Math.min(batchConcurrentLimit, names.length))
      let submitted = 0
      for (let i = 0; i < names.length; i += limit) {
        const chunk = names.slice(i, i + limit)
        await Promise.allSettled(chunk.map(async (stratName) => {
          try {
            const content = await exportStrategyContent(stratName)
            const document = parseStrategyYamlDocument(content)
            const params = buildStructuredRunParams(document, buildYamlEditState(document))
            const symbolsToUse = resolveSymbolsForRun(document, { preferOverride: false })
            const imported = await api.importStrategy(stratName, content)
            const effectiveSystemConfig = resolveSystemConfigForDocument(document, stratName)
            const prepared = {
              editState: buildYamlEditState(document),
              effectiveSystemConfig,
              loadedDocument: document,
              nextDocument: document,
              params,
              runtimeYaml: content,
              symbolsToUse,
            }
            const runPayloads = buildRunPayloads(stratName, prepared, imported)
            const responses = await submitRunPayloads(runPayloads)
            const failed = responses.filter((r: any) => r.status === 'failed' && r.error_message)
            if (failed.length > 0) {
              batchFailures.push(`${stratName}: ${String(failed[0].error_message).split('\n')[0]}`)
            }
          } catch (e) {
            batchFailures.push(`${stratName}: ${e instanceof Error ? e.message : String(e)}`)
            console.warn(`[batch] ${stratName} 提交失败:`, e)
          }
        }))
        submitted += chunk.length
        setRunParamMsg(`⏳ 已提交 ${submitted}/${names.length}（批次上限 ${limit}）`)
      }
      if (batchFailures.length > 0) {
        const failMsg = `❌ ${batchFailures.length}/${names.length} 个回测失败：\n${batchFailures.join('\n')}`
        setRunParamMsg(failMsg)
        setApiError(failMsg)
      } else {
        setRunParamMsg(`✓ 已批量提交 ${names.length} 个回测任务（并发上限 ${limit}）`)
      }
      setImportSuccess([`✓ 已批量提交 ${names.length} 个回测`])
      setTimeout(() => loadAll(), 800)
    } catch (err) {
      setRunParamMsg(`提交失败：${api.friendlyError(err)}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSystemPresetSelect = (presetId: string) => {
    setSelectedSystemPresetId(presetId)
    if (!presetId) {
      const commodityCode = systemConfig.commodityCode || (strategyYamlDocument?.basic?.symbols?.[0] ? getContractVarietyCode(strategyYamlDocument.basic.symbols[0]) : "")
      setSystemPresetName(commodityCode ? `${commodityCode.toUpperCase()} 预设` : "新预设")
      setSystemConfig(inferSystemConfigFromDocument(strategyYamlDocument, commodityCode))
      setSystemPresetMsg("ℹ 已切换为新的系统配置草稿，填写后保存即可加入下拉菜单")
      return
    }

    const preset = systemPresets.find((item) => item.id === presetId)
    if (!preset) return
    setSystemPresetName(preset.name)
    setSystemConfig({ ...preset.config })
    setSystemPresetMsg(`✓ 已载入商品预设：${preset.name}`)
  }

  const handleSaveSystemPreset = () => {
    const presetName = systemPresetName.trim()
    const commodityCode = systemConfig.commodityCode.trim().toLowerCase()
    if (!presetName) {
      setSystemPresetMsg("请先填写预设名称")
      return
    }
    if (!commodityCode) {
      setSystemPresetMsg("请先填写商品代码，例如 p / rb / i")
      return
    }

    const nextPreset: SystemRuntimePreset = {
      id: selectedSystemPresetId || createSystemPresetId(),
      name: presetName,
      commodityCode,
      config: { ...systemConfig, commodityCode },
      updatedAt: Date.now(),
    }

    const nextPresets = [
      nextPreset,
      ...systemPresets.filter((item) => item.id !== nextPreset.id),
    ].sort((left, right) => left.name.localeCompare(right.name, "zh-CN"))

    writeSystemRuntimePresets(nextPresets)
    setSystemPresets(nextPresets)
    setSelectedSystemPresetId(nextPreset.id)
    setSystemPresetName(nextPreset.name)
    setSystemConfig({ ...nextPreset.config })
    setSystemPresetMsg(`✓ 已保存商品预设：${nextPreset.name}`)
  }

  const handleDeleteSystemPreset = () => {
    if (!selectedSystemPresetId) return
    const current = systemPresets.find((item) => item.id === selectedSystemPresetId)
    const nextPresets = systemPresets.filter((item) => item.id !== selectedSystemPresetId)
    writeSystemRuntimePresets(nextPresets)
    setSystemPresets(nextPresets)
    setSelectedSystemPresetId("")
    const commodityCode = strategyYamlDocument?.basic?.symbols?.[0] ? getContractVarietyCode(strategyYamlDocument.basic.symbols[0]) : ""
    setSystemPresetName(commodityCode ? `${commodityCode.toUpperCase()} 预设` : "新预设")
    setSystemConfig(inferSystemConfigFromDocument(strategyYamlDocument, commodityCode))
    setSystemPresetMsg(current ? `已删除商品预设：${current.name}` : "已删除商品预设")
  }

  const updateSystemConfig = <K extends keyof SystemRuntimeConfig>(key: K, value: SystemRuntimeConfig[K]) => {
    setSystemConfig((prev) => ({ ...prev, [key]: value }))
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

  const addContractsByCategory = (codes: readonly string[]) => {
    const matchedContracts = getContractsByCategory(codes, mainContracts)
    if (matchedContracts.length === 0) return
    setSelectedContracts((prev) => Array.from(new Set([...prev, ...matchedContracts])))
  }

  const resolveSymbolsForRun = (document: ParsedYamlDocument | null, options?: { preferOverride?: boolean }) => {
    if (options?.preferOverride !== false) {
      if (selectedContracts.length > 0) return selectedContracts
      if (selectedContract) return [selectedContract]
    }

    if (!document?.basic.symbols?.length) return undefined
    const resolvedContracts = resolveMainContractsFromSymbols(document.basic.symbols, mainContracts)
    return resolvedContracts.length > 0 ? resolvedContracts : document.basic.symbols
  }

  const loadStrategyYamlForStrategy = async (stratName: string, options?: { resetContractSelection?: boolean }) => {
    try {
      const content = await exportStrategyContent(stratName)
      const document = parseStrategyYamlDocument(content)
      const autoContracts = resolveMainContractsFromSymbols(document.basic.symbols, mainContracts)
      setSelectedStrategyForRun(stratName)
      setStrategyYamlDocument(document)
      setStrategyYamlParams(buildYamlEditState(document))
      if (options?.resetContractSelection) {
        setSelectedContracts(autoContracts)
        setSelectedContract(autoContracts[0] ?? "")
      }
      return document
    } catch {
      setApiError("读取策略 YAML 失败，请检查策略内容或后端导出接口")
      return null
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
  const currentStrategyBasic = strategyYamlDocument?.basic ?? null
  const strategyFieldSections = strategyYamlDocument ? splitStrategyFields(strategyYamlDocument.fields) : null
  const signalFields = strategyYamlDocument?.fields.filter((field) => field.group === "signal" && field.editable) ?? []
  const riskFields = strategyYamlDocument?.fields.filter((field) => field.group === "risk" && field.editable) ?? []
  const displayStrategyRootFields = strategyFieldSections?.root.filter((field) => !SYSTEM_RUNTIME_ROOT_PATHS.has(field.path)) ?? []
  const displayRiskFields: ParsedYamlField[] = []
  const selectedPreset = systemPresets.find((preset) => preset.id === selectedSystemPresetId) ?? null
  const currentCommodityCode = systemConfig.commodityCode || (currentStrategyBasic?.symbols?.[0] ? getContractVarietyCode(currentStrategyBasic.symbols[0]) : "")
  const selectedStrategyActiveResults = selectedStrategyForRun
    ? results
        .filter((result) =>
          (result.status === "running" || result.status === "submitted" || result.status === "pending") &&
          (result.strategy === selectedStrategyForRun || result.payload?.strategy?.id === selectedStrategyForRun || result.name === selectedStrategyForRun),
        )
        .sort((left, right) => (right.submitted_at ?? 0) - (left.submitted_at ?? 0))
    : null
  const selectedTemplateLabel = humanizeTemplateId(currentStrategyBasic?.templateId ?? "")

  const resolveListCardDisplayTitle = (section: string, index: number, fields: ParsedYamlField[]) => {
    const structuredSection = (strategyYamlDocument?.structuredParams?.[section] as Array<Record<string, unknown>> | undefined)?.[index]
    if (structuredSection && typeof structuredSection === "object") {
      for (const key of ["factor_name", "name", "alias", "indicator_type"]) {
        const candidate = structuredSection[key]
        if (typeof candidate === "string" && candidate.trim()) return candidate.trim()
      }
    }
    const nameField = fields.find((field) => ["alias", "factor_name", "name"].includes(field.key))
    if (nameField) return String(strategyYamlParams[nameField.path] ?? nameField.value)
    const title = resolveYamlListSectionTitle(section)
    return `${title.en} ${index + 1}`
  }

  const renderYamlFieldGrid = (fields: ParsedYamlField[], tone: "neutral" | "signal" | "risk" = "neutral") => {
    if (fields.length === 0) return null
    const wrapperClass = tone === "risk"
      ? "border border-amber-700/30 bg-amber-900/10"
      : tone === "signal"
        ? "border border-purple-700/30 bg-purple-900/10"
        : "border border-neutral-700/60 bg-neutral-800/40"
    const labelClass = tone === "risk"
      ? "text-amber-300"
      : tone === "signal"
        ? "text-purple-300"
        : "text-neutral-300"
    const inputClass = tone === "risk"
      ? "bg-amber-950/20 border-amber-700/50 text-amber-100"
      : tone === "signal"
        ? "bg-purple-950/20 border-purple-700/50 text-purple-100"
        : "bg-neutral-900 border-neutral-600 text-white"

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
        {fields.map((field) => {
          const leafKey = getYamlLeafKey(field.path)
          const label = resolveFieldLabel(field.path, leafKey)
          return (
            <div key={`${field.path}:${field.lineIndex}`} className={`rounded-lg p-3 ${wrapperClass}`}>
              <label className={`text-xs block mb-1 ${labelClass}`}>
                {label.zh}
                {label.en && <span className="text-neutral-500 font-normal"> / {label.en}</span>}
                {label.unit && <span className="text-neutral-500"> ({label.unit})</span>}
              </label>
              <Input
                value={strategyYamlParams[field.path] ?? formatYamlEditableValue(field.value)}
                onChange={(event) => setStrategyYamlParams((prev) => ({ ...prev, [field.path]: event.target.value }))}
                className={inputClass}
              />
              <p className="text-[10px] text-neutral-500 mt-1 leading-relaxed">{label.desc}</p>
              <p className="text-[10px] text-neutral-600 mt-1 font-mono break-all">{field.path}</p>
            </div>
          )
        })}
      </div>
    )
  }

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
      <Card className="bg-neutral-900 border-2 border-orange-600/40">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-orange-400 tracking-wider flex items-center gap-2">
            <Settings className="w-4 h-4" />
            回测参数调整
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="border border-cyan-700/40 rounded-lg p-4 bg-cyan-950/10 space-y-4">
            <div className="flex items-center gap-2 text-cyan-300 text-sm font-medium tracking-wider">
              <Shield className="w-4 h-4" />
              系统级配置 / Commodity Runtime Presets
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="text-xs text-neutral-400 block mb-1">商品预设下拉菜单</label>
                <select
                  value={selectedSystemPresetId}
                  onChange={(event) => handleSystemPresetSelect(event.target.value)}
                  className="w-full bg-neutral-900 border border-neutral-600 text-white text-sm rounded px-3 py-2"
                >
                  <option value="">新建预设草稿</option>
                  {systemPresets.map((preset) => (
                    <option key={preset.id} value={preset.id}>
                      {preset.name} ({preset.commodityCode.toUpperCase()})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs text-neutral-400 block mb-1">预设名称</label>
                <Input
                  value={systemPresetName}
                  onChange={(event) => setSystemPresetName(event.target.value)}
                  placeholder="例如：棕榈油日内风控"
                  className="bg-neutral-900 border-neutral-600 text-white"
                />
              </div>
              <div>
                <label className="text-xs text-neutral-400 block mb-1">商品代码</label>
                <Input
                  value={systemConfig.commodityCode}
                  onChange={(event) => updateSystemConfig("commodityCode", event.target.value.toLowerCase())}
                  placeholder="例如：p / rb / i"
                  className="bg-neutral-900 border-neutral-600 text-white font-mono"
                />
              </div>
            </div>

            <div className="flex gap-2 flex-wrap">
              <Button onClick={() => handleSystemPresetSelect("")} className="bg-neutral-700 hover:bg-neutral-600 text-white">
                新建预设
              </Button>
              <Button onClick={handleSaveSystemPreset} className="bg-cyan-700 hover:bg-cyan-600 text-white">
                <Save className="w-4 h-4 mr-2" />保存当前预设
              </Button>
              <Button onClick={handleDeleteSystemPreset} className="bg-red-700 hover:bg-red-600 text-white" disabled={!selectedSystemPresetId}>
                删除当前预设
              </Button>
            </div>

            {systemPresetMsg && (
              <p className={`text-xs ${systemPresetMsg.startsWith("✓") ? "text-green-400" : systemPresetMsg.startsWith("ℹ") ? "text-blue-300" : "text-amber-300"}`}>
                {systemPresetMsg}
              </p>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
              <div className="rounded-lg p-3 border border-cyan-700/30 bg-neutral-900/70">
                <label className="text-xs text-cyan-300 block mb-1">本金 / Initial Capital</label>
                <Input value={systemConfig.initialCapital} onChange={(event) => updateSystemConfig("initialCapital", event.target.value)} className="bg-neutral-900 border-neutral-600 text-white" />
              </div>
              <div className="rounded-lg p-3 border border-cyan-700/30 bg-neutral-900/70">
                <label className="text-xs text-cyan-300 block mb-1">仓位 / Position Fraction</label>
                <Input value={formatPercentInput(systemConfig.positionFraction)} onChange={(event) => updateSystemConfig("positionFraction", parsePercentInput(event.target.value))} className="bg-neutral-900 border-neutral-600 text-white" />
                <p className="text-[10px] text-neutral-500 mt-1">按百分比输入，当前保存值 {formatDecimalAsPercent(systemConfig.positionFraction)}</p>
              </div>
              <div className="rounded-lg p-3 border border-cyan-700/30 bg-neutral-900/70">
                <label className="text-xs text-cyan-300 block mb-1">滑点 / Slippage</label>
                <Input value={systemConfig.slippagePerUnit} onChange={(event) => updateSystemConfig("slippagePerUnit", event.target.value)} className="bg-neutral-900 border-neutral-600 text-white" />
              </div>
              <div className="rounded-lg p-3 border border-cyan-700/30 bg-neutral-900/70">
                <label className="text-xs text-cyan-300 block mb-1">手续费 / Commission</label>
                <Input value={systemConfig.commissionPerLotRoundTurn} onChange={(event) => updateSystemConfig("commissionPerLotRoundTurn", event.target.value)} className="bg-neutral-900 border-neutral-600 text-white" />
              </div>
              <div className="rounded-lg p-3 border border-cyan-700/30 bg-neutral-900/70">
                <label className="text-xs text-cyan-300 block mb-1">日亏损限制</label>
                <Input value={formatPercentInput(systemConfig.dailyLossLimit)} onChange={(event) => updateSystemConfig("dailyLossLimit", parsePercentInput(event.target.value))} className="bg-neutral-900 border-neutral-600 text-white" />
                <p className="text-[10px] text-neutral-500 mt-1">按百分比输入，当前保存值 {formatDecimalAsPercent(systemConfig.dailyLossLimit)}</p>
              </div>
              <div className="rounded-lg p-3 border border-cyan-700/30 bg-neutral-900/70">
                <label className="text-xs text-cyan-300 block mb-1">最大回撤</label>
                <Input value={formatPercentInput(systemConfig.maxDrawdown)} onChange={(event) => updateSystemConfig("maxDrawdown", parsePercentInput(event.target.value))} className="bg-neutral-900 border-neutral-600 text-white" />
                <p className="text-[10px] text-neutral-500 mt-1">按百分比输入，当前保存值 {formatDecimalAsPercent(systemConfig.maxDrawdown)}</p>
              </div>
              <div className="rounded-lg p-3 border border-cyan-700/30 bg-neutral-900/70">
                <label className="text-xs text-cyan-300 block mb-1">单品种熔断</label>
                <Input value={systemConfig.perSymbolFuseYuan} onChange={(event) => updateSystemConfig("perSymbolFuseYuan", event.target.value)} className="bg-neutral-900 border-neutral-600 text-white" />
              </div>
              <div className="rounded-lg p-3 border border-cyan-700/30 bg-neutral-900/70">
                <label className="text-xs text-cyan-300 block mb-1">连续亏损上限</label>
                <Input value={systemConfig.maxConsecutiveLosses} onChange={(event) => updateSystemConfig("maxConsecutiveLosses", event.target.value)} className="bg-neutral-900 border-neutral-600 text-white" />
              </div>
              <div className="rounded-lg p-3 border border-cyan-700/30 bg-neutral-900/70">
                <label className="text-xs text-cyan-300 block mb-1">止损 ATR 倍数</label>
                <Input value={systemConfig.stopLossAtrMultiplier} onChange={(event) => updateSystemConfig("stopLossAtrMultiplier", event.target.value)} className="bg-neutral-900 border-neutral-600 text-white" />
              </div>
              <div className="rounded-lg p-3 border border-cyan-700/30 bg-neutral-900/70">
                <label className="text-xs text-cyan-300 block mb-1">止盈 ATR 倍数</label>
                <Input value={systemConfig.takeProfitAtrMultiplier} onChange={(event) => updateSystemConfig("takeProfitAtrMultiplier", event.target.value)} className="bg-neutral-900 border-neutral-600 text-white" />
              </div>
              <div className="rounded-lg p-3 border border-cyan-700/30 bg-neutral-900/70">
                <label className="text-xs text-cyan-300 block mb-1">日盘强平</label>
                <Input value={systemConfig.forceCloseDay} onChange={(event) => updateSystemConfig("forceCloseDay", event.target.value)} className="bg-neutral-900 border-neutral-600 text-white" />
              </div>
              <div className="rounded-lg p-3 border border-cyan-700/30 bg-neutral-900/70">
                <label className="text-xs text-cyan-300 block mb-1">夜盘强平</label>
                <Input value={systemConfig.forceCloseNight} onChange={(event) => updateSystemConfig("forceCloseNight", event.target.value)} className="bg-neutral-900 border-neutral-600 text-white" />
              </div>
            </div>

            <label className="flex items-center gap-2 text-sm text-neutral-300">
              <input
                type="checkbox"
                className="accent-cyan-500"
                checked={systemConfig.noOvernight}
                onChange={(event) => updateSystemConfig("noOvernight", event.target.checked)}
              />
              使用 no_overnight（禁止隔夜）
            </label>

            <p className="text-[11px] text-neutral-500 leading-relaxed">
              这里保存的是商品级系统参数预设。回测前系统会把这些配置统一覆盖到 position_fraction、transaction_costs 和 risk，策略下半区只保留 YAML 逻辑层参数。
            </p>
          </div>

          <div className="bg-neutral-800 rounded-lg p-4 space-y-3">
            <div className="flex items-start justify-between gap-3 flex-wrap">
              <div>
                <p className="text-xs text-neutral-400 mb-1">当前策略 / Current Strategy</p>
                {selectedStrategyForRun ? (
                  <>
                    <p className="text-lg text-orange-400 font-mono">{selectedStrategyForRun}</p>
                    {currentStrategyBasic?.description && (
                      <p className="text-xs text-neutral-500 mt-1 max-w-3xl leading-relaxed">{currentStrategyBasic.description}</p>
                    )}
                  </>
                ) : (
                  <p className="text-xs text-neutral-600">请在下方策略列表中点击一行以加载 YAML 真值参数</p>
                )}
              </div>
              {selectedStrategyForRun && (
                <button
                  className="text-xs text-neutral-500 hover:text-red-400"
                  onClick={() => {
                    setSelectedStrategyForRun("")
                    setStrategyYamlDocument(null)
                    setStrategyYamlParams({})
                    setSelectedContracts([])
                    setSelectedContract("")
                  }}
                >
                  清除
                </button>
              )}
            </div>
            {selectedStrategyForRun && currentStrategyBasic && (
              <div className="flex flex-wrap gap-2">
                {(selectedPreset?.name || systemPresetName) && <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">预设 {(selectedPreset?.name || systemPresetName)}</span>}
                {currentCommodityCode && <span className="text-xs px-2 py-0.5 rounded-full bg-neutral-700/50 text-neutral-200 border border-neutral-600">商品 {currentCommodityCode.toUpperCase()}</span>}
                {currentStrategyBasic.templateId && <span className="text-xs px-2 py-0.5 rounded-full bg-neutral-700/50 text-neutral-300 border border-neutral-600">模板 {selectedTemplateLabel}</span>}
                {currentStrategyBasic.timeframe && <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/15 text-blue-300 border border-blue-500/30">周期 {formatTimeframeValue(currentStrategyBasic.timeframe)}</span>}
                {systemConfig.initialCapital && <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">资金 {formatCompactCurrency(systemConfig.initialCapital)}</span>}
                {systemConfig.positionFraction && <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30">仓位 {formatDecimalAsPercent(systemConfig.positionFraction)}</span>}
                {(systemConfig.stopLossAtrMultiplier || systemConfig.takeProfitAtrMultiplier) && <span className="text-xs px-2 py-0.5 rounded-full bg-red-500/15 text-red-300 border border-red-500/30">止损/止盈 {systemConfig.stopLossAtrMultiplier || "--"} / {systemConfig.takeProfitAtrMultiplier || "--"} ATR</span>}
                <span className="text-xs px-2 py-0.5 rounded-full bg-orange-500/15 text-orange-300 border border-orange-500/30">因子 {currentStrategyBasic.factorCount} 个</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">指标 {currentStrategyBasic.indicatorCount} 个</span>
                {currentStrategyBasic.symbols.length > 0 && <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">YAML 合约 {currentStrategyBasic.symbols.join(", ")}</span>}
                {currentStrategyBasic.version && <span className="text-xs px-2 py-0.5 rounded-full bg-neutral-700/50 text-neutral-300 border border-neutral-600">版本 {currentStrategyBasic.version}</span>}
              </div>
            )}
          </div>

          {selectedStrategyForRun && currentStrategyBasic && (
            <>
              <div className="border border-neutral-700 rounded-lg p-4 bg-neutral-800/40 space-y-3">
                <p className="text-xs text-neutral-400 tracking-wider border-b border-neutral-700 pb-2">基本信息 / Basic Info</p>
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3 text-sm">
                  <div className="rounded-lg border border-neutral-700/60 bg-neutral-900/70 p-3">
                    <p className="text-xs text-neutral-500 mb-1">策略名称</p>
                    <p className="text-white font-mono break-all">{selectedStrategyForRun}</p>
                  </div>
                  <div className="rounded-lg border border-neutral-700/60 bg-neutral-900/70 p-3">
                    <p className="text-xs text-neutral-500 mb-1">当前预设</p>
                    <p className="text-white">{selectedPreset?.name || systemPresetName || "--"}</p>
                  </div>
                  <div className="rounded-lg border border-neutral-700/60 bg-neutral-900/70 p-3">
                    <p className="text-xs text-neutral-500 mb-1">YAML 合约</p>
                    <p className="text-white font-mono break-all">{currentStrategyBasic.symbols.length > 0 ? currentStrategyBasic.symbols.join(", ") : "--"}</p>
                  </div>
                  <div className="rounded-lg border border-neutral-700/60 bg-neutral-900/70 p-3">
                    <p className="text-xs text-neutral-500 mb-1">时间框架</p>
                    <p className="text-white">{formatTimeframeValue(currentStrategyBasic.timeframe)}</p>
                  </div>
                  <div className="rounded-lg border border-neutral-700/60 bg-neutral-900/70 p-3">
                    <p className="text-xs text-neutral-500 mb-1">执行模板</p>
                    <p className="text-white">{selectedTemplateLabel}</p>
                    {currentStrategyBasic.templateId && <p className="text-[10px] text-neutral-500 mt-1 font-mono break-all">{currentStrategyBasic.templateId}</p>}
                  </div>
                  <div className="rounded-lg border border-neutral-700/60 bg-neutral-900/70 p-3">
                    <p className="text-xs text-neutral-500 mb-1">版本</p>
                    <p className="text-white">{currentStrategyBasic.version || "--"}</p>
                  </div>
                  <div className="rounded-lg border border-neutral-700/60 bg-neutral-900/70 p-3">
                    <p className="text-xs text-neutral-500 mb-1">商品代码</p>
                    <p className="text-white font-mono">{currentCommodityCode ? currentCommodityCode.toUpperCase() : "--"}</p>
                  </div>
                  <div className="rounded-lg border border-neutral-700/60 bg-neutral-900/70 p-3 xl:col-span-2">
                    <p className="text-xs text-neutral-500 mb-1">结构概览</p>
                    <p className="text-white">因子 {currentStrategyBasic.factorCount} 个 / 指标 {currentStrategyBasic.indicatorCount} 个</p>
                    {currentStrategyBasic.factorNames.length > 0 && (
                      <p className="text-xs text-neutral-500 mt-1 leading-relaxed">因子: {currentStrategyBasic.factorNames.join(" / ")}</p>
                    )}
                    {currentStrategyBasic.indicatorNames.length > 0 && (
                      <p className="text-xs text-neutral-500 mt-1 leading-relaxed">指标: {currentStrategyBasic.indicatorNames.join(" / ")}</p>
                    )}
                  </div>
                  <div className="rounded-lg border border-neutral-700/60 bg-neutral-900/70 p-3 xl:col-span-2">
                    <p className="text-xs text-neutral-500 mb-1">运行预设摘要</p>
                    <p className="text-white">资金 {formatCompactCurrency(systemConfig.initialCapital)} / 仓位 {formatDecimalAsPercent(systemConfig.positionFraction)} / 滑点 {systemConfig.slippagePerUnit || "--"} / 手续费 {systemConfig.commissionPerLotRoundTurn || "--"}</p>
                    <p className="text-xs text-neutral-500 mt-1 leading-relaxed">风控：最大回撤 {formatDecimalAsPercent(systemConfig.maxDrawdown)} / 连亏上限 {systemConfig.maxConsecutiveLosses || "--"} / 止损 {systemConfig.stopLossAtrMultiplier || "--"} ATR / 止盈 {systemConfig.takeProfitAtrMultiplier || "--"} ATR</p>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div className="border border-neutral-700 rounded-lg p-4 bg-neutral-800/40 space-y-3">
                  <p className="text-xs text-neutral-400 tracking-wider border-b border-neutral-700 pb-2">策略参数 / Strategy Parameters</p>
                  {displayStrategyRootFields.length > 0 ? renderYamlFieldGrid(displayStrategyRootFields) : <p className="text-xs text-neutral-600">当前仅显示策略逻辑参数；系统级资金、成本、风控已上移到商品预设区</p>}
                  {strategyFieldSections?.contractSpecs.length ? (
                    <div className="space-y-2">
                      <p className="text-xs text-cyan-300">合约规格 / Contract Specs</p>
                      {renderYamlFieldGrid(strategyFieldSections.contractSpecs)}
                    </div>
                  ) : null}
                  {strategyFieldSections?.marketFilter.length ? (
                    <div className="space-y-2">
                      <p className="text-xs text-cyan-300">过滤条件 / Market Filter</p>
                      {renderYamlFieldGrid(strategyFieldSections.marketFilter)}
                    </div>
                  ) : null}
                  {Object.values(strategyFieldSections?.lists ?? {}).map((listSection) => {
                    const title = resolveYamlListSectionTitle(listSection.section)
                    const cards = Object.entries(listSection.cards)
                    if (cards.length === 0) return null

                    return (
                      <div key={listSection.section} className="space-y-3">
                        <p className="text-xs text-cyan-300">{title.zh} / {title.en}</p>
                        <div className="grid grid-cols-1 xl:grid-cols-2 gap-3 items-start">
                          {cards.map(([index, fields]) => {
                            const displayTitle = resolveListCardDisplayTitle(listSection.section, Number(index), fields)
                            return (
                              <div key={`${listSection.section}-${index}`} className="rounded-lg border border-neutral-700/60 bg-neutral-900/60 p-3 space-y-3 h-full">
                                <div>
                                  <p className="text-sm text-white font-medium">{displayTitle}</p>
                                  <p className="text-[11px] text-neutral-500">第 {Number(index) + 1} 组配置</p>
                                </div>
                                {renderYamlFieldGrid(fields)}
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )
                  })}
                </div>

                <div className="border border-neutral-700 rounded-lg p-4 bg-neutral-800/40 space-y-3">
                  <p className="text-xs text-neutral-400 tracking-wider border-b border-neutral-700 pb-2">信号参数 / Signal Parameters</p>
                  {signalFields.length > 0 ? renderYamlFieldGrid(signalFields, "signal") : <p className="text-xs text-neutral-600">当前 YAML 未定义 signal.* 可编辑参数</p>}
                </div>

              </div>
            </>
          )}

          <div className="border border-neutral-700 rounded-lg p-4 bg-neutral-800/40 space-y-3">
            <p className="text-xs text-neutral-400 tracking-wider border-b border-neutral-700 pb-2">合约选择 / Contract Selection</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-neutral-400 block mb-1">输入合约代码（自动补全）</label>
                <div className="relative">
                  <Input
                    value={contractInput}
                    onChange={(event) => handleContractInputChange(event.target.value)}
                    onKeyDown={(event) => { if (event.key === "Enter" && contractInput) addContract(contractInput) }}
                    placeholder="输入合约代码，例如 SHFE.rb2505"
                    className="bg-neutral-900 border-neutral-600 text-white font-mono"
                  />
                  {contractSuggestions.length > 0 && (
                    <div className="absolute top-full left-0 right-0 bg-neutral-900 border border-neutral-600 rounded-b z-10 max-h-36 overflow-y-auto">
                      {contractSuggestions.map((contract) => (
                        <div key={contract} className="px-3 py-1.5 text-xs text-white cursor-pointer hover:bg-neutral-800 font-mono" onClick={() => addContract(contract)}>{contract}</div>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex flex-wrap gap-2 mt-3">
                  {contractCategoryPresets.map((preset) => {
                    const matchedContracts = getContractsByCategory(preset.codes, mainContracts)
                    if (matchedContracts.length === 0) return null
                    return (
                      <button key={preset.key} onClick={() => addContractsByCategory(preset.codes)} className="text-xs px-2 py-1 bg-neutral-700 hover:bg-neutral-600 text-neutral-300 rounded">
                        添加 {preset.zh} / {preset.en} ({matchedContracts.length})
                      </button>
                    )
                  })}
                  {mainContracts.length > 0 && (
                    <button onClick={() => setSelectedContracts(mainContracts.slice(0, 20))} className="text-xs px-2 py-1 bg-neutral-700 hover:bg-neutral-600 text-neutral-300 rounded">
                      前 20 个主力合约
                    </button>
                  )}
                  {(selectedContracts.length > 1 || currentStrategyBasic?.symbols.length > 1) && (
                    <span className="text-[11px] px-2 py-1 rounded border border-emerald-500/20 bg-emerald-500/10 text-emerald-300">
                      多品种模式下会按当前合约列表逐个提交正式回测任务，确保每个品种都实际执行，不会只使用第一项。
                    </span>
                  )}
                  {currentStrategyBasic?.symbols.length ? (
                    <span className="text-[11px] px-2 py-1 rounded border border-blue-500/20 bg-blue-500/10 text-blue-300">
                      当前已自动载入 YAML 默认合约；如需恢复，点击右侧“清空覆盖，回退 YAML symbols”。
                    </span>
                  ) : null}
                  {mainContractsNote && <span className="text-[11px] text-neutral-500">{mainContractsNote}</span>}
                </div>
              </div>
              <div>
                <label className="text-xs text-neutral-400 block mb-1">当前运行合约</label>
                {selectedContracts.length === 0 ? (
                  <div className="text-xs bg-neutral-900 rounded p-3 border border-neutral-700 min-h-[72px]">
                    {currentStrategyBasic?.symbols.length ? (
                      <div className="space-y-2">
                        <p className="text-blue-300">默认使用 YAML symbols：</p>
                        <div className="flex flex-wrap gap-1">
                          {currentStrategyBasic.symbols.map((symbol) => (
                            <span key={symbol} className="px-2 py-0.5 rounded bg-blue-500/15 text-blue-300 border border-blue-500/30 font-mono">{symbol}</span>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <span className="text-neutral-600">当前策略 YAML 未定义 symbols，可在左侧输入框中手动添加覆盖</span>
                    )}
                  </div>
                ) : (
                  <div className="flex flex-wrap gap-1 bg-neutral-900 rounded p-2 border border-neutral-700 min-h-[72px]">
                    {selectedContracts.map((contract) => (
                      <span key={contract} className="flex items-center gap-1 text-xs px-2 py-0.5 rounded font-mono bg-orange-500/20 text-orange-300">
                        {contract}
                        <button onClick={() => removeContract(contract)} className="text-neutral-500 hover:text-red-400 ml-0.5">×</button>
                      </span>
                    ))}
                  </div>
                )}
                {selectedContracts.length > 0 && (
                  <button onClick={() => setSelectedContracts([])} className="text-xs text-neutral-500 hover:text-red-400 mt-2">清空覆盖，回退 YAML symbols</button>
                )}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-neutral-400 block mb-1">回测开始日期</label>
              <Input type="date" value={backtestStart} onChange={(event) => setBacktestStart(event.target.value)} className="bg-neutral-800 border-neutral-600 text-white" />
            </div>
            <div>
              <label className="text-xs text-neutral-400 block mb-1">回测结束日期</label>
              <Input type="date" value={backtestEnd} onChange={(event) => setBacktestEnd(event.target.value)} className="bg-neutral-800 border-neutral-600 text-white" />
            </div>
          </div>

          <div className="flex gap-3 pt-1 flex-wrap">
            <Button onClick={() => handleSaveCurrentStrategy()} className="bg-emerald-600 hover:bg-emerald-700 text-white flex-1 min-w-[160px]" disabled={isSavingParams || !selectedStrategyForRun}>
              <Save className="w-4 h-4 mr-2" />{isSavingParams ? "保存中..." : "保存当前策略"}
            </Button>
            <Button onClick={() => handleSaveParamsAndRun()} className="bg-orange-500 hover:bg-orange-600 text-white flex-1 min-w-[160px]" disabled={isLoading || !selectedStrategyForRun}>
              <Play className="w-4 h-4 mr-2" />回测当前策略
            </Button>
            <Button onClick={handleBatchRunBacktest} className="bg-blue-600 hover:bg-blue-700 text-white flex-1 min-w-[160px]" disabled={isLoading || selectedIds.size === 0}>
              <Play className="w-4 h-4 mr-2" />批量回测已选 ({selectedIds.size})
            </Button>
          </div>

          {!selectedStrategyForRun && (
            <p className="text-xs text-amber-300">
              单策略回测需要先点击下方策略列表中的整行或播放按钮；勾选框只用于批量回测。
            </p>
          )}

          {selectedStrategyActiveResults && selectedStrategyActiveResults.length > 0 && (
            <div className="border border-orange-500/30 rounded-lg p-4 bg-orange-500/5 space-y-3">
              <div>
                <p className="text-xs text-neutral-400">当前运行任务</p>
                <p className="text-sm text-orange-300 font-mono">{selectedStrategyForRun}</p>
                <p className="text-[11px] text-neutral-500 mt-1">当前共有 {selectedStrategyActiveResults.length} 个运行中的合约任务</p>
              </div>
              <div className="space-y-3">
                {selectedStrategyActiveResults.map((activeResult) => {
                  const progress = progressMap[activeResult.id] ?? { progress: 0, current_date: null }
                  const contractLabel = activeResult.contracts?.[0] ?? activeResult.payload?.contract ?? activeResult.payload?.symbols?.[0] ?? "--"
                  return (
                    <div key={activeResult.id} className="rounded-lg border border-orange-500/20 bg-neutral-900/50 p-3 space-y-2">
                      <div className="flex items-center justify-between gap-3 flex-wrap">
                        <div>
                          <p className="text-xs text-neutral-400">合约</p>
                          <p className="text-sm text-white font-mono">{contractLabel}</p>
                          <p className="text-[11px] text-neutral-500 mt-1">任务 ID: {activeResult.id}</p>
                        </div>
                        <Button
                          onClick={async () => {
                            setCancellingId(activeResult.id)
                            try {
                              await api.cancelBacktest(activeResult.id)
                              setRunParamMsg(`已发送终止指令：${contractLabel}`)
                            } catch (err) {
                              setRunParamMsg(`终止失败：${api.friendlyError(err)}`)
                            } finally {
                              setTimeout(() => {
                                setCancellingId(null)
                                loadAll()
                              }, 800)
                            }
                          }}
                          className="bg-red-700 hover:bg-red-600 text-white"
                          disabled={cancellingId === activeResult.id}
                        >
                          {cancellingId === activeResult.id ? "终止中..." : "终止当前回测"}
                        </Button>
                      </div>
                      <div>
                        <div className="flex items-center justify-between mb-1 text-xs">
                          <span className="text-orange-300 font-mono">进度 {progress.progress}%</span>
                          <span className="text-neutral-500">{progress.current_date ? `当前日期 ${progress.current_date}` : "等待后端返回进度"}</span>
                        </div>
                        <div className="h-2 w-full bg-neutral-700 rounded-full overflow-hidden">
                          <div className="h-full bg-orange-500 rounded-full transition-all duration-500" style={{ width: `${progress.progress}%` }} />
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

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
                onChange={(event) => setBatchConcurrentLimit(Number(event.target.value))}
                className="bg-neutral-800 border border-neutral-600 text-white text-xs rounded px-2 py-1"
              >
                {[1, 2, 3, 4, 5, 6, 8, 10, 15, 20].map((count) => (
                  <option key={count} value={count}>{count} 个/批</option>
                ))}
              </select>
            </div>
          </div>

          {paramSaveMsg && (
            <p className={`text-xs ${paramSaveMsg.startsWith("✓") ? "text-green-400" : "text-red-400"}`}>
              {paramSaveMsg}
            </p>
          )}

          {runParamMsg && (
            <p className={`text-xs ${runParamMsg.startsWith("✓") ? "text-green-400" : runParamMsg.startsWith("ℹ") ? "text-blue-300" : "text-red-400"}`}>
              {runParamMsg}
            </p>
          )}
        </CardContent>
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
            <p className="text-xs text-neutral-500">更新于: {lastUpdate}</p>
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
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400 tracking-wider">扫描</th>
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
                      className={`border-b border-neutral-800 hover:bg-neutral-800 cursor-pointer ${selectedIds.has(s.name) ? "bg-orange-900/20" : ""} ${selectedStrategyForRun === s.name ? "bg-blue-900/20" : ""}`}
                      onClick={async () => {
                        setEditedParams({})
                        setParamSaveMsg(null)
                        setSelectedStrategyForRun(s.name)
                        await loadStrategyYamlForStrategy(s.name, { resetContractSelection: true })
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
                          const scan = (s as any).scan_result || {}
                          const scanStatus: string = scan.scan_status || "unknown"
                          const missing: string[] = scan.missing_factors || []
                          const warnings: string[] = scan.warnings || []
                          const allIssues = [
                            ...(scan.formal_parser_error ? [`解析错误: ${scan.formal_parser_error}`] : []),
                            ...(missing.length > 0 ? [`未注册因子: ${missing.join(", ")}`] : []),
                            ...warnings,
                          ]
                          const tooltip = allIssues.length > 0 ? allIssues.join("\n") : "✓ 策略已通过扫描"
                          if (scanStatus === "ready") {
                            return <span title={tooltip} className="inline-flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 rounded bg-emerald-900/40 text-emerald-400 border border-emerald-700/40 cursor-help">✓ 就绪</span>
                          }
                          if (scanStatus === "warning") {
                            return <span title={tooltip} className="inline-flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 rounded bg-amber-900/40 text-amber-400 border border-amber-700/40 cursor-help">⚠ 警告</span>
                          }
                          if (scanStatus === "blocked") {
                            return <span title={tooltip} className="inline-flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 rounded bg-red-900/40 text-red-400 border border-red-700/40 cursor-help">✗ 阻塞</span>
                          }
                          return <span className="text-neutral-600 text-xs">—</span>
                        })()}
                      </td>
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
                          if (last.status === "running" || last.status === "submitted" || last.status === "pending") {
                            return <span className="text-orange-400">计算中…</span>
                          }
                          const ret = last.totalReturn ?? last.total_return
                          if (ret == null) return <span className="text-neutral-600">—</span>
                          const color = ret >= 0 ? "text-red-400" : "text-green-400"
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
                          <Button variant="ghost" size="icon" className="text-neutral-400 hover:text-blue-400 h-8 w-8" title="用当前策略 YAML 真值快速回测" onClick={async (e) => { e.stopPropagation(); await handleSaveParamsAndRun(s.name) }}>
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
